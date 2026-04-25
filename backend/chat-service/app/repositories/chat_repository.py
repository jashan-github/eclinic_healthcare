from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_, or_, text
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Tuple, Any
from uuid import UUID
from datetime import datetime
from app.db.models import ChatRoom, ChatMessage, ChatRoomStatus, SenderType, MessageType
from app.utils.encryption import chat_encryption_service
from app.core.config import settings


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_chat_room(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        appointment_id: Optional[UUID] = None
    ) -> ChatRoom:
        """
        Create a new chat room.
        
        Note: If a duplicate active room exists (due to race condition),
        this will raise an IntegrityError. The service layer should handle
        this by checking for existing rooms first.
        """
        chat_room = ChatRoom(
            doctor_id=doctor_id,
            patient_id=patient_id,
            appointment_id=appointment_id,
            status=ChatRoomStatus.ACTIVE
        )
        self.db.add(chat_room)
        try:
            await self.db.commit()
            await self.db.refresh(chat_room)
            return chat_room
        except IntegrityError as e:
            await self.db.rollback()
            # Unique constraint violation - get existing room
            existing_room = await self.get_active_chat_room(
                doctor_id=doctor_id,
                patient_id=patient_id,
                appointment_id=appointment_id
            )
            if existing_room:
                return existing_room
            raise
        except Exception as e:
            await self.db.rollback()
            raise
    
    async def get_chat_room_by_id(self, room_id: UUID) -> Optional[ChatRoom]:
        """Get chat room by ID."""
        result = await self.db.execute(
            select(ChatRoom).where(ChatRoom.id == room_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_chat_room(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        appointment_id: Optional[UUID] = None
    ) -> Optional[ChatRoom]:
        """
        Get active chat room between doctor and patient.
        
        Note: Returns the active room regardless of appointment_id to prevent duplicates.
        Only one active room should exist per doctor-patient pair.
        """
        # Check for any active room between doctor and patient (regardless of appointment_id)
        # This prevents duplicate rooms
        conditions = [
            ChatRoom.doctor_id == doctor_id,
            ChatRoom.patient_id == patient_id,
            ChatRoom.status == ChatRoomStatus.ACTIVE
        ]
        
        result = await self.db.execute(
            select(ChatRoom).where(and_(*conditions))
        )
        return result.scalar_one_or_none()
    
    async def get_user_chat_rooms(
        self,
        user_id: UUID,
        role: str,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[ChatRoom], int]:
        """Get chat rooms for a user (doctor or patient)."""
        if role == "doctor":
            condition = ChatRoom.doctor_id == user_id
        else:
            condition = ChatRoom.patient_id == user_id
        
        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(ChatRoom).where(condition)
        )
        total = count_result.scalar() or 0
        
        # Get rooms
        result = await self.db.execute(
            select(ChatRoom)
            .where(condition)
            .order_by(ChatRoom.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rooms = result.scalars().all()
        return list(rooms), total
    
    async def close_chat_room(self, room_id: UUID) -> bool:
        """Close a chat room."""
        result = await self.db.execute(
            update(ChatRoom)
            .where(ChatRoom.id == room_id)
            .values(status=ChatRoomStatus.CLOSED)
            .returning(ChatRoom)
        )
        await self.db.commit()
        return result.scalar_one_or_none() is not None
    
    async def create_message(
        self,
        chat_room_id: UUID,
        sender_id: UUID,
        sender_type: SenderType,
        message: str,
        message_type: MessageType = MessageType.TEXT,
        is_client_encrypted: bool = False
    ) -> ChatMessage:
        """
        Create a new chat message.
        
        If is_client_encrypted=True, the message is already encrypted by the client (E2E encryption)
        and will be stored as-is without additional server-side encryption.
        
        If is_client_encrypted=False, the message will be encrypted server-side (at-rest encryption).
        """
        from app.core.logging import logger
        
        if is_client_encrypted:
            # Message is already encrypted by client (E2E encryption)
            # Store as-is without additional encryption
            # Note: We can't decrypt it because we don't have the client's encryption key
            stored_message = message
            is_encrypted = True  # Mark as encrypted (by client)
            logger.info(f"Storing client-encrypted message (E2E) for room {chat_room_id}")
        else:
            # Encrypt message server-side (at-rest encryption)
            encrypted_message = chat_encryption_service.encrypt_message(message)
            is_encrypted = chat_encryption_service.is_encryption_enabled()
            stored_message = encrypted_message
        
        chat_message = ChatMessage(
            chat_room_id=chat_room_id,
            sender_id=sender_id,
            sender_type=sender_type,
            message_type=message_type,
            message=stored_message,
            is_encrypted=is_encrypted
        )
        self.db.add(chat_message)
        await self.db.commit()
        await self.db.refresh(chat_message)
        
        # Decrypt for return only if server-side encrypted
        # Client-encrypted messages cannot be decrypted by server
        if chat_message.is_encrypted and not is_client_encrypted:
            try:
                chat_message.message = chat_encryption_service.decrypt_message(
                    chat_message.message,
                    is_encrypted=chat_message.is_encrypted
                )
            except Exception as e:
                logger.error(f"Failed to decrypt message {chat_message.id} after creation: {e}")
        elif is_client_encrypted:
            # For client-encrypted messages, return as-is (server can't decrypt)
            # The client will decrypt it on their end
            pass
        
        return chat_message
    
    async def get_messages(
        self,
        chat_room_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[ChatMessage], int]:
        """
        Get messages for a chat room.
        Automatically decrypts encrypted messages before returning.
        """
        from app.core.logging import logger
        
        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(ChatMessage).where(
                ChatMessage.chat_room_id == chat_room_id
            )
        )
        total = count_result.scalar() or 0
        
        # Get messages
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_room_id == chat_room_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        messages = result.scalars().all()
        
        # Decrypt messages before returning
        for message in messages:
            if message.is_encrypted:
                try:
                    # Try to decrypt, but handle case where message might be plain text with wrong flag
                    message.message = chat_encryption_service.decrypt_message(
                        message.message,
                        is_encrypted=message.is_encrypted
                    )
                except Exception as e:
                    logger.warning(f"Failed to decrypt message {message.id}: {e}. Message might be plain text.")
                    # If decryption fails, check if it's actually plain text
                    # Don't show error to user - just return the message as-is
                    # The message might be plain text with incorrect is_encrypted flag
                    pass  # Keep original message (might be plain text)
            # Legacy unencrypted messages are returned as-is
        
        return list(messages), total
    
    async def mark_message_as_read(
        self,
        message_id: UUID,
        reader_id: UUID
    ) -> bool:
        """Mark a message as read."""
        result = await self.db.execute(
            update(ChatMessage)
            .where(
                and_(
                    ChatMessage.id == message_id,
                    ChatMessage.sender_id != reader_id  # Can't mark own messages as read
                )
            )
            .values(read_at=datetime.utcnow())
            .returning(ChatMessage)
        )
        await self.db.commit()
        return result.scalar_one_or_none() is not None
    
    async def mark_room_messages_as_read(
        self,
        room_id: UUID,
        reader_id: UUID
    ) -> int:
        """Mark all unread messages in a room as read."""
        result = await self.db.execute(
            update(ChatMessage)
            .where(
                and_(
                    ChatMessage.chat_room_id == room_id,
                    ChatMessage.sender_id != reader_id,
                    ChatMessage.read_at.is_(None)
                )
            )
            .values(read_at=datetime.utcnow())
            .returning(ChatMessage.id)
        )
        await self.db.commit()
        return len(result.scalars().all())
    
    async def mark_room_messages_as_unread(
        self,
        room_id: UUID,
        user_id: UUID
    ) -> int:
        """
        Mark all messages in a room as unread (reset read_at to NULL).
        Only messages that were read by this user will be reset.
        """
        result = await self.db.execute(
            update(ChatMessage)
            .where(
                and_(
                    ChatMessage.chat_room_id == room_id,
                    ChatMessage.sender_id != user_id,  # Can't reset read status of own messages
                    ChatMessage.read_at.isnot(None)  # Only reset messages that are currently read
                )
            )
            .values(read_at=None)
        )
        await self.db.commit()
        return result.rowcount
    
    async def verify_user_access(
        self,
        room_id: UUID,
        user_id: UUID,
        role: str
    ) -> bool:
        """Verify if user has access to the chat room."""
        room = await self.get_chat_room_by_id(room_id)
        if not room:
            return False
        
        if role == "doctor":
            return room.doctor_id == user_id
        else:
            return room.patient_id == user_id
    
    async def get_user_info(self, user_id: UUID) -> Optional[Dict[str, str]]:
        """Get user name, email, and avatar from users and user_profiles tables."""
        # Query to get user info with avatar (check both users.avatar and user_profiles.avatar)
        query = text("""
            SELECT 
                u.name, 
                u.email,
                COALESCE(up.avatar, u.avatar) as avatar
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE u.id = :user_id AND u.deleted_at IS NULL
        """)
        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()
        if row:
            avatar_path = row[2] if row[2] else None
            avatar_url = self._get_avatar_url(avatar_path) if avatar_path else None
            return {
                "name": row[0],
                "email": row[1],
                "avatar": avatar_url
            }
        return None
    
    def _get_avatar_url(self, avatar_path: str) -> Optional[str]:
        """Generate full URL for avatar image."""
        if not avatar_path:
            return None
        
        # Remove leading slash if present
        avatar_path = avatar_path.lstrip('/')
        
        # Construct full URL
        base_url = settings.BASE_URL.rstrip('/')
        return f"{base_url}/{avatar_path}"
    
    async def get_last_message(self, room_id: UUID) -> Optional[Dict[str, Any]]:
        """Get the last message for a chat room."""
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_room_id == room_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        message = result.scalar_one_or_none()
        if message:
            # Decrypt message if encrypted
            from app.core.logging import logger
            decrypted_message = message.message
            if message.is_encrypted:
                try:
                    decrypted_message = chat_encryption_service.decrypt_message(
                        message.message,
                        is_encrypted=message.is_encrypted
                    )
                except Exception as e:
                    logger.warning(f"Failed to decrypt last message {message.id}: {e}. Message might be plain text.")
                    # If decryption fails, return original message (might be plain text with wrong flag)
                    decrypted_message = message.message
            
            return {
                "id": str(message.id),
                "message": decrypted_message,
                "sender_id": str(message.sender_id),
                "sender_type": message.sender_type.value,
                "message_type": message.message_type.value,
                "created_at": message.created_at
            }
        return None
    
    async def get_unread_count(self, room_id: UUID, user_id: UUID) -> int:
        """Get count of unread messages for a user in a room."""
        result = await self.db.execute(
            select(func.count()).select_from(ChatMessage).where(
                and_(
                    ChatMessage.chat_room_id == room_id,
                    ChatMessage.sender_id != user_id,
                    ChatMessage.read_at.is_(None)
                )
            )
        )
        return result.scalar() or 0
    
    async def get_user_chat_rooms_with_details(
        self,
        user_id: UUID,
        role: str,
        limit: int = 50,
        offset: int = 0,
        status: Optional[ChatRoomStatus] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get chat rooms for a user with patient/doctor info, last message, and unread count.
        
        Returns a list of dictionaries with room data including:
        - Room information
        - Patient/Doctor name and email (opposite party)
        - Last message
        - Unread message count
        """
        if role == "doctor":
            base_condition = ChatRoom.doctor_id == user_id
            other_party_field = ChatRoom.patient_id
        else:
            base_condition = ChatRoom.patient_id == user_id
            other_party_field = ChatRoom.doctor_id

        # Optional status filter (active / closed)
        if status is not None:
            condition = and_(base_condition, ChatRoom.status == status)
        else:
            condition = base_condition
        
        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(ChatRoom).where(condition)
        )
        total = count_result.scalar() or 0
        
        # Get rooms
        result = await self.db.execute(
            select(ChatRoom)
            .where(condition)
            .order_by(ChatRoom.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rooms = result.scalars().all()
        
        # Enrich each room with patient/doctor info, last message, and unread count
        enriched_rooms = []
        for room in rooms:
            # Get other party info (patient for doctor, doctor for patient)
            other_party_id = room.patient_id if role == "doctor" else room.doctor_id
            other_party_info = await self.get_user_info(other_party_id)
            
            # Get last message
            last_message = await self.get_last_message(room.id)
            
            # Get unread count
            unread_count = await self.get_unread_count(room.id, user_id)
            
            enriched_room = {
                "id": str(room.id),
                "doctor_id": str(room.doctor_id),
                "patient_id": str(room.patient_id),
                "appointment_id": str(room.appointment_id) if room.appointment_id else None,
                "status": room.status.value,
                "created_at": room.created_at,
                "updated_at": room.updated_at,
                "patient_name": other_party_info["name"] if other_party_info and role == "doctor" else None,
                "patient_email": other_party_info["email"] if other_party_info and role == "doctor" else None,
                "patient_image": other_party_info.get("avatar") if other_party_info and role == "doctor" else None,
                "doctor_name": other_party_info["name"] if other_party_info and role == "patient" else None,
                "doctor_email": other_party_info["email"] if other_party_info and role == "patient" else None,
                "doctor_image": other_party_info.get("avatar") if other_party_info and role == "patient" else None,
                "last_message": last_message,
                "unread_count": unread_count
            }
            enriched_rooms.append(enriched_room)
        
        return enriched_rooms, total