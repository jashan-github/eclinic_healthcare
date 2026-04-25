"""
Agora Token Generation Service

All Agora RTC tokens are built with agora-token-builder (RtcTokenBuilder.buildTokenWithAccount).
No manual or custom token construction is used.

Reference: https://github.com/AgoraIO-Community/python-token-builder
"""

import base64
import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
from cryptography.fernet import Fernet
from app.core.logging import logger

from app.core.config import settings
from app.core.exceptions import ValidationException

# Default path for Agora token debug log (can override via AGORA_TOKEN_LOG_FILE env)
AGORA_TOKEN_LOG_FILE = os.getenv("AGORA_TOKEN_LOG_FILE", "logs/agora_tokens.log")

# Official Agora RTC token builder – required for token generation
from agora_token_builder import RtcTokenBuilder
from agora_token_builder.RtcTokenBuilder import Role_Publisher, Role_Subscriber


def _inspect_token(token: str) -> Dict[str, Any]:
    """
    Inspect Agora token: decode base64 and parse JSON if possible.
    Returns a dict with format info for logging (no full token logged).
    """
    out: Dict[str, Any] = {"raw_length": len(token), "is_base64": False, "decoded_json": None}
    if not token or not isinstance(token, str):
        return out
    try:
        raw = base64.b64decode(token, validate=True)
        out["encoding"] = "base64"
    except Exception:
        try:
            raw = base64.urlsafe_b64decode(token + "==")
            out["encoding"] = "base64url"
        except Exception as e:
            out["decode_error"] = str(e)
            return out
    out["is_base64"] = True
    out["decoded_bytes"] = len(raw)
    try:
        s = raw.decode("utf-8")
        obj = json.loads(s)
        out["decoded_json"] = True
        out["json_keys"] = list(obj.keys()) if isinstance(obj, dict) else type(obj).__name__
        if isinstance(obj, dict):
            out["structure"] = {k: type(v).__name__ for k, v in obj.items()}
        return out
    except (UnicodeDecodeError, json.JSONDecodeError):
        out["decoded_json"] = False
        out["decoded_preview"] = raw[:80].decode("utf-8", errors="replace") if len(raw) <= 200 else "(truncated)"
    return out


def _log_token_to_file(channel_name: str, user_id: str, role: str, token: str, token_info: Dict[str, Any]) -> None:
    """Append token inspection and a redacted token line to the Agora token log file."""
    log_path = getattr(settings, "AGORA_TOKEN_LOG_FILE", AGORA_TOKEN_LOG_FILE)
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.isdir(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError:
            logger.warning("Could not create Agora token log dir %s", log_dir)
            return
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    redacted = f"{token[:20]}...{token[-10:]}" if len(token) > 35 else "(short)"
    line = (
        f"[{ts}] channel={channel_name} user_id={user_id} role={role} "
        f"token_len={len(token)} token_preview={redacted} inspect={json.dumps(token_info)}\n"
    )
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError as e:
        logger.warning("Could not write Agora token log to %s: %s", log_path, e)


class AgoraService:
    """
    Agora token and channel service.

    - Token generation: via agora-token-builder only (generate_token, generate_token_for_user).
    - Channel names: generate_secure_channel_name, generate_channel_name_from_participants.
    - Storage helpers: encrypt_token / decrypt_token for DB.
    """
    
    def __init__(self):
        """Initialize Agora service with credentials from config"""
        # Agora credentials (should be in environment variables)
        self.app_id = getattr(settings, 'AGORA_APP_ID', '')
        self.app_certificate = getattr(settings, 'AGORA_APP_CERTIFICATE', '')
        
        if not self.app_id or not self.app_certificate:
            logger.warning("Agora credentials not configured. Video calls will not work.")
        
        # Encryption key for storing tokens (use Fernet for symmetric encryption)
        encryption_key = settings.ENCRYPTION_KEY
        if encryption_key:
            try:
                self.cipher = Fernet(encryption_key.encode())
            except Exception as e:
                logger.error(f"Failed to initialize encryption: {e}")
                self.cipher = None
        else:
            logger.warning("ENCRYPTION_KEY not set. Tokens will be stored unencrypted.")
            self.cipher = None
    
    def generate_secure_channel_name(self, session_id: UUID) -> str:
        """
        Generate secure channel name from session_id
        
        CRITICAL: Channel name must NOT contain PHI (no user IDs, names, emails)
        Uses SHA-256 hash of session_id to ensure security and uniqueness
        
        Args:
            session_id: Video session UUID
            
        Returns:
            Secure channel name (hash-based)
        """
        # Create deterministic hash from session_id
        # This ensures:
        # 1. No PHI in channel name
        # 2. Uniqueness per session
        # 3. Deterministic (same session_id = same channel name)
        session_str = str(session_id)
        hash_obj = hashlib.sha256(session_str.encode())
        # Use first 31 chars to ensure total length is 64 bytes (32 app_id + 1 underscore + 31 hash = 64)
        # Agora channel name limit is 64 bytes
        channel_hash = hash_obj.hexdigest()[:31]
        
        # Prefix with app_id for multi-tenant support
        # Total length: 32 (app_id) + 1 (_) + 31 (hash) = 64 bytes (within Agora's limit)
        channel_name = f"{self.app_id}_{channel_hash}"
        
        logger.debug(f"Generated channel name for session {session_id}: {channel_name}")
        return channel_name
    
    def generate_channel_name_from_participants(
        self,
        doctor_name: str,
        patient_name: str,
        scheduled_start: Optional[datetime],
        session_id: UUID,
        max_bytes: int = 64,
    ) -> str:
        """
        Generate human-readable channel name: DoctorName_PatientName_YYYYMMDD_HHmm
        
        Uses doctor/patient names and appointment datetime. No app_id.
        Sanitized for Agora (alphanumeric + underscore). Truncated to max_bytes (default 64).
        Uniqueness ensured by appending short session_id suffix.
        """
        def _sanitize(s: str, max_len: int) -> str:
            if not s or not isinstance(s, str):
                return "Anonymous"
            # Replace spaces with underscore, keep alphanumeric and underscore only
            out = re.sub(r"[^a-zA-Z0-9_]", "", (s or "").replace(" ", "_"))
            return (out or "Anonymous")[:max_len]
        
        # Reserve: 2 underscores between parts, 13 for YYYYMMDD_HHmm, 1 + 7 for _xxxxxx suffix
        # So doctor + patient = 64 - 2 - 13 - 8 = 41 chars total, e.g. 20+1+20
        part_max = 20
        doctor_part = _sanitize(doctor_name, part_max)
        patient_part = _sanitize(patient_name, part_max)
        
        if scheduled_start:
            try:
                st = scheduled_start
                if hasattr(st, "strftime"):
                    dt_part = st.strftime("%Y%m%d_%H%M")
                else:
                    dt_part = "00000000_0000"
            except Exception:
                dt_part = "00000000_0000"
        else:
            dt_part = "00000000_0000"
        
        suffix = str(session_id).replace("-", "")[:6]
        channel_name = f"{doctor_part}_{patient_part}_{dt_part}_{suffix}"
        
        if len(channel_name.encode("utf-8")) > max_bytes:
            channel_name = channel_name.encode("utf-8")[:max_bytes].decode("utf-8", "ignore")
        
        logger.debug(f"Generated participant channel name: {channel_name}")
        return channel_name
    
    def generate_token(
        self,
        channel_name: str,
        user_id: str,
        role: str = "publisher",
        expire_timestamp: Optional[int] = None,
        privilege_expire_timestamp: Optional[int] = None,
    ) -> str:
        """
        Generate Agora RTC token via agora-token-builder (server-side only).

        Calls RtcTokenBuilder.buildTokenWithAccount(appId, appCertificate, channelName, account, role, privilegeExpiredTs).
        All tokens MUST be generated through this method; never build tokens manually.

        Args:
            channel_name: Agora channel name (must match the name used in client.join).
            user_id: User identifier as string (Agora userAccount; e.g. str(uuid)).
            role: "publisher" (can publish audio/video) or "subscriber" (audience only).
            expire_timestamp: Unix timestamp when token expires. Default: 60 minutes from now.
            privilege_expire_timestamp: Unix timestamp when privileges expire (privilegeExpiredTs).
                Default: same as expire_timestamp.

        Returns:
            Agora RTC token string from agora-token-builder.
        """
        if not self.app_id or not self.app_certificate:
            raise ValidationException(
                message="Agora credentials not configured",
                errors={"agora": ["Agora service is not properly configured"]},
            )

        now_ts = int(time.time())
        if expire_timestamp is None:
            expire_timestamp = now_ts + 3600
        if privilege_expire_timestamp is None:
            privilege_expire_timestamp = expire_timestamp

        role_int = Role_Publisher if (role or "").lower() == "publisher" else Role_Subscriber

        token = RtcTokenBuilder.buildTokenWithAccount(
            self.app_id,
            self.app_certificate,
            channel_name,
            str(user_id),
            role_int,
            privilege_expire_timestamp,
        )
        # Inspect token (base64 / JSON) and log to file
        role_str = "publisher" if role_int == Role_Publisher else "subscriber"
        token_info = _inspect_token(token)
        logger.debug("Generated Agora RTC token via agora-token-builder: %s", token_info)
        _log_token_to_file(channel_name, str(user_id), role_str, token, token_info)
        return token
    
    def encrypt_token(self, token: str) -> str:
        """
        Encrypt an Agora token (from generate_token / agora-token-builder) for DB storage.

        Uses Fernet symmetric encryption. The plain token is always produced by
        RtcTokenBuilder.buildTokenWithAccount via generate_token().

        Args:
            token: Plain Agora RTC token string returned by generate_token().

        Returns:
            Encrypted token string (base64), or the same string if ENCRYPTION_KEY is not set.
        """
        if not self.cipher:
            logger.warning("Encryption not available. Storing token unencrypted.")
            return token
        try:
            encrypted = self.cipher.encrypt(token.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt token: {e}")
            raise ValidationException(
                message="Failed to encrypt token",
                errors={"encryption": [str(e)]},
            )

    def decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt a stored Agora token back to the plain form used by the client.

        Inverse of encrypt_token(). The result is the same format as returned by
        generate_token() (agora-token-builder output).

        Args:
            encrypted_token: Value stored in DB (either encrypted or plain if encryption was off).

        Returns:
            Plain Agora RTC token string for client.join(appId, channelName, token, uid).
        """
        if not self.cipher:
            return encrypted_token
        try:
            decrypted = self.cipher.decrypt(encrypted_token.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt token: {e}")
            raise ValidationException(
                message="Failed to decrypt token",
                errors={"decryption": [str(e)]},
            )
    
    def generate_token_for_user(
        self,
        session_id: UUID,
        user_id: UUID,
        role: str = "publisher",
        expiry_minutes: int = 60,
        channel_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a full token package for one user using agora-token-builder.

        This is the main entry point for token generation. It:
        - Resolves channel_name (from argument or session_id),
        - Computes privilegeExpiredTs from expiry_minutes,
        - Calls generate_token() which uses RtcTokenBuilder.buildTokenWithAccount(),
        - Optionally encrypts the token for DB storage.

        Args:
            session_id: Video session UUID (used only if channel_name is None).
            user_id: User UUID; passed as string (Agora userAccount) to the builder.
            role: "publisher" or "subscriber".
            expiry_minutes: Token validity in minutes (15–60). Drives privilegeExpiredTs.
            channel_name: Agora channel name. If None, generated from session_id.

        Returns:
            Dict with:
            - channel_name: Channel name used in the token (and for client.join).
            - token: Encrypted token for DB (or plain if no ENCRYPTION_KEY).
            - token_plain: Plain token for the client.
            - expires_at: Expiration as datetime (UTC).
            - expire_timestamp: Expiration as Unix timestamp.
        """
        if expiry_minutes < 15 or expiry_minutes > 60:
            raise ValidationException(
                message="Token expiry must be between 15 and 60 minutes",
                errors={"expiry": [f"Invalid expiry: {expiry_minutes} minutes"]},
            )

        if not channel_name:
            channel_name = self.generate_secure_channel_name(session_id)

        from datetime import timezone

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
        expire_timestamp = int(expires_at.timestamp())

        token_plain = self.generate_token(
            channel_name=channel_name,
            user_id=str(user_id),
            role=role,
            expire_timestamp=expire_timestamp,
            privilege_expire_timestamp=expire_timestamp,
        )
        token_encrypted = self.encrypt_token(token_plain)

        return {
            "channel_name": channel_name,
            "token": token_encrypted,
            "token_plain": token_plain,
            "expires_at": expires_at,
            "expire_timestamp": expire_timestamp,
        }


# Singleton instance
agora_service = AgoraService()
