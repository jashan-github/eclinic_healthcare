from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.repositories.chat_repository import ChatRepository
from app.db.models import ChatRoom, ChatMessage, SenderType, MessageType, ChatRoomStatus
from app.schemas.chat import ChatMessageCreate
from app.core.logging import logger


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ChatRepository(db)
    
    async def start_chat(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        appointment_id: Optional[UUID] = None
    ) -> ChatRoom:
        """
        Start a new chat between doctor and patient.
        Returns existing active room if one exists, otherwise creates new.
        
        Prevents duplicate chat rooms between the same doctor and patient.
        """
        # Check for existing active room (regardless of appointment_id to prevent duplicates)
        existing_room = await self.repository.get_active_chat_room(
            doctor_id=doctor_id,
            patient_id=patient_id,
            appointment_id=appointment_id
        )
        
        if existing_room:
            logger.info(f"Returning existing chat room {existing_room.id} for doctor {doctor_id} and patient {patient_id}")
            return existing_room
        
        # Create new room
        try:
            chat_room = await self.repository.create_chat_room(
                doctor_id=doctor_id,
                patient_id=patient_id,
                appointment_id=appointment_id
            )
            logger.info(f"Created new chat room {chat_room.id} for doctor {doctor_id} and patient {patient_id}")
            return chat_room
        except IntegrityError as e:
            # Handle race condition: if room was created by another request, get existing one
            logger.warning(f"Duplicate chat room detected (unique constraint violation), fetching existing room: {e}")
            existing_room = await self.repository.get_active_chat_room(
                doctor_id=doctor_id,
                patient_id=patient_id,
                appointment_id=appointment_id
            )
            if existing_room:
                logger.info(f"Returning existing chat room {existing_room.id} after duplicate detection")
                return existing_room
            # If no existing room found, re-raise the error
            logger.error(f"IntegrityError but no existing room found for doctor {doctor_id} and patient {patient_id}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating chat room: {e}")
            raise
    
    async def get_user_chat_rooms(
        self,
        user_id: UUID,
        role: str,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[ChatRoom], int]:
        """Get all chat rooms for a user."""
        return await self.repository.get_user_chat_rooms(
            user_id=user_id,
            role=role,
            limit=limit,
            offset=offset
        )
    
    async def get_user_chat_rooms_with_details(
        self,
        user_id: UUID,
        role: str,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> tuple[List[dict], int]:
        """
        Get chat rooms for a user with patient/doctor info, last message, and unread count.
        
        If status is provided ('active' or 'closed'), only rooms with that status are returned.
        """
        status_enum = None
        if status:
            status_lower = status.lower()
            if status_lower == ChatRoomStatus.ACTIVE.value:
                status_enum = ChatRoomStatus.ACTIVE
            elif status_lower == ChatRoomStatus.CLOSED.value:
                status_enum = ChatRoomStatus.CLOSED
        return await self.repository.get_user_chat_rooms_with_details(
            user_id=user_id,
            role=role,
            limit=limit,
            offset=offset,
            status=status_enum
        )
    
    async def get_chat_messages(
        self,
        room_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[ChatMessage], int]:
        """Get messages for a chat room."""
        return await self.repository.get_messages(
            chat_room_id=room_id,
            limit=limit,
            offset=offset
        )
    
    async def send_message(
        self,
        room_id: UUID,
        sender_id: UUID,
        sender_type: SenderType,
        message_data: ChatMessageCreate
    ) -> ChatMessage:
        """
        Send a message in a chat room.
        Validates room access and creates message.
        
        Supports both:
        - Server-side encryption (is_client_encrypted=False): Message encrypted by server
        - Client-side encryption (is_client_encrypted=True): Message already encrypted by client (E2E)
        """
        # Verify room exists and is active
        room = await self.repository.get_chat_room_by_id(room_id)
        if not room:
            raise ValueError("Chat room not found")
        
        if room.status != ChatRoomStatus.ACTIVE:
            raise ValueError("Chat room is closed")
        
        # Create message (with client encryption flag)
        message = await self.repository.create_message(
            chat_room_id=room_id,
            sender_id=sender_id,
            sender_type=sender_type,
            message=message_data.message,
            message_type=message_data.message_type,
            is_client_encrypted=getattr(message_data, 'is_client_encrypted', False)
        )
        
        encryption_type = "client-encrypted (E2E)" if getattr(message_data, 'is_client_encrypted', False) else "server-encrypted"
        logger.info(f"Created {encryption_type} message {message.id} in room {room_id}")
        return message
    
    async def mark_message_as_read(
        self,
        message_id: UUID,
        reader_id: UUID
    ) -> bool:
        """Mark a specific message as read."""
        return await self.repository.mark_message_as_read(
            message_id=message_id,
            reader_id=reader_id
        )
    
    async def mark_room_messages_as_read(
        self,
        room_id: UUID,
        reader_id: UUID
    ) -> int:
        """Mark all messages in a room as read."""
        return await self.repository.mark_room_messages_as_read(
            room_id=room_id,
            reader_id=reader_id
        )
    
    async def mark_room_messages_as_unread(
        self,
        room_id: UUID,
        user_id: UUID
    ) -> int:
        """Mark all messages in a room as unread (reset read count)."""
        return await self.repository.mark_room_messages_as_unread(
            room_id=room_id,
            user_id=user_id
        )
    
    async def close_chat_room(self, room_id: UUID) -> bool:
        """Close a chat room."""
        return await self.repository.close_chat_room(room_id)
    
    async def verify_user_access(
        self,
        room_id: UUID,
        user_id: UUID,
        role: str
    ) -> bool:
        """Verify if user has access to the chat room."""
        return await self.repository.verify_user_access(
            room_id=room_id,
            user_id=user_id,
            role=role
        )
