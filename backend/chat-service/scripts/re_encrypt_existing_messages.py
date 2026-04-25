#!/usr/bin/env python3
"""
Script to re-encrypt existing unencrypted chat messages

This script will:
1. Find all messages with is_encrypted=false
2. Encrypt them using the current ENCRYPTION_KEY
3. Update is_encrypted=true

Usage:
    docker compose exec chat-service python3 scripts/re_encrypt_existing_messages.py

WARNING: This script modifies existing messages. Make sure you have a database backup!
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from app.db.models import ChatMessage
from app.utils.encryption import chat_encryption_service
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def re_encrypt_messages():
    """Re-encrypt all unencrypted messages"""
    
    # Check if encryption is enabled
    if not chat_encryption_service.is_encryption_enabled():
        logger.error("Encryption is not enabled! Set ENCRYPTION_KEY in .env file first.")
        sys.exit(1)
    
    # Create database session
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Find all unencrypted messages
            result = await session.execute(
                select(ChatMessage).where(ChatMessage.is_encrypted == False)
            )
            messages = result.scalars().all()
            
            total_count = len(messages)
            logger.info(f"Found {total_count} unencrypted messages to encrypt")
            
            if total_count == 0:
                logger.info("No unencrypted messages found. All messages are already encrypted.")
                return
            
            # Encrypt each message
            success_count = 0
            error_count = 0
            
            for message in messages:
                try:
                    # Skip if message is already encrypted (safety check)
                    if message.is_encrypted:
                        continue
                    
                    # Decrypt first (in case it's already encrypted but flag is wrong)
                    # Actually, if is_encrypted=false, it should be plain text
                    plain_text = message.message
                    
                    # Encrypt the message
                    encrypted_message = chat_encryption_service.encrypt_message(plain_text)
                    
                    # Update the message
                    await session.execute(
                        update(ChatMessage)
                        .where(ChatMessage.id == message.id)
                        .values(
                            message=encrypted_message,
                            is_encrypted=True
                        )
                    )
                    
                    success_count += 1
                    
                    if success_count % 100 == 0:
                        logger.info(f"Progress: {success_count}/{total_count} messages encrypted")
                        await session.commit()  # Commit in batches
                
                except Exception as e:
                    logger.error(f"Failed to encrypt message {message.id}: {e}")
                    error_count += 1
                    continue
            
            # Commit remaining changes
            await session.commit()
            
            logger.info("="*60)
            logger.info(f"Re-encryption complete!")
            logger.info(f"  Total messages: {total_count}")
            logger.info(f"  Successfully encrypted: {success_count}")
            logger.info(f"  Errors: {error_count}")
            logger.info("="*60)
            
    except Exception as e:
        logger.error(f"Error during re-encryption: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logger.info("Starting message re-encryption...")
    logger.info(f"Encryption enabled: {chat_encryption_service.is_encryption_enabled()}")
    asyncio.run(re_encrypt_messages())
