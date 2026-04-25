from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.db.models import ChatRoomStatus, SenderType, MessageType
import enum


class StartChatRequest(BaseModel):
    patient_id: UUID
    appointment_id: Optional[UUID] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "123e4567-e89b-12d3-a456-426614174000",
                "appointment_id": "123e4567-e89b-12d3-a456-426614174001"
            }
        }


class StartChatResponse(BaseModel):
    room_id: UUID
    doctor_id: UUID
    patient_id: UUID
    appointment_id: Optional[UUID]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class LastMessageResponse(BaseModel):
    """Last message in a chat room."""
    id: UUID
    message: str
    sender_id: UUID
    sender_type: str
    message_type: str
    created_at: datetime


class ChatRoomResponse(BaseModel):
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    appointment_id: Optional[UUID]
    status: str
    created_at: datetime
    updated_at: datetime
    patient_name: Optional[str] = None
    patient_email: Optional[str] = None
    patient_image: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_email: Optional[str] = None
    doctor_image: Optional[str] = None
    last_message: Optional[LastMessageResponse] = None
    unread_count: int = 0
    
    class Config:
        from_attributes = True


class ChatRoomListResponse(BaseModel):
    rooms: List[ChatRoomResponse]
    total: int


class ChatMessageCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=10240)
    message_type: MessageType = MessageType.TEXT
    is_client_encrypted: bool = Field(default=False, description="Whether the message is already encrypted by the client (for E2E encryption)")
    
    @validator("message")
    def validate_message_size(cls, v):
        if len(v.encode("utf-8")) > 10240:
            raise ValueError("Message too large (max 10KB)")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hello, how can I help you today?",
                "message_type": "text",
                "is_client_encrypted": False
            }
        }


class ChatMessageResponse(BaseModel):
    id: UUID
    chat_room_id: UUID
    sender_id: UUID
    sender_type: str
    message_type: str
    message: str
    read_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatMessageListResponse(BaseModel):
    messages: List[ChatMessageResponse]
    total: int
    room_id: UUID


class CloseChatRequest(BaseModel):
    room_id: UUID
    
    class Config:
        json_schema_extra = {
            "example": {
                "room_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class WSMessageType(str, enum.Enum):
    MESSAGE = "message"
    TYPING = "typing"
    READ_RECEIPT = "read_receipt"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


class WSMessage(BaseModel):
    type: WSMessageType
    room_id: UUID
    sender_id: UUID
    sender_type: SenderType
    message_type: MessageType = MessageType.TEXT
    message: Optional[str] = None
    message_id: Optional[UUID] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "message",
                "room_id": "123e4567-e89b-12d3-a456-426614174000",
                "sender_id": "123e4567-e89b-12d3-a456-426614174001",
                "sender_type": "doctor",
                "message_type": "text",
                "message": "Hello!",
                "timestamp": "2025-01-01T12:00:00Z"
            }
        }


class WSTypingIndicator(BaseModel):
    type: WSMessageType = WSMessageType.TYPING
    room_id: UUID
    sender_id: UUID
    sender_type: SenderType
    is_typing: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSReadReceipt(BaseModel):
    type: WSMessageType = WSMessageType.READ_RECEIPT
    room_id: UUID
    message_id: UUID
    read_by: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
