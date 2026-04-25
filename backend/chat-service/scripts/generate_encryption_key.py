#!/usr/bin/env python3
"""
Generate a Fernet encryption key for chat message encryption

Usage:
    python scripts/generate_encryption_key.py

Output:
    A base64-encoded encryption key that can be used in ENCRYPTION_KEY environment variable
"""
from cryptography.fernet import Fernet

if __name__ == "__main__":
    key = Fernet.generate_key()
    print("\n" + "="*60)
    print("Chat Service Encryption Key Generator")
    print("="*60)
    print(f"\nGenerated Encryption Key:")
    print(f"ENCRYPTION_KEY={key.decode()}")
    print("\n" + "="*60)
    print("\nAdd this to your .env file:")
    print(f"ENCRYPTION_KEY={key.decode()}")
    print("\n" + "="*60)
    print("\n⚠️  IMPORTANT:")
    print("  - Store this key securely")
    print("  - Never commit this key to version control")
    print("  - Use different keys for different environments")
    print("  - Keep a backup of this key (you'll need it to decrypt existing messages)")
    print("="*60 + "\n")
