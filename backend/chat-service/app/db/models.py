from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import uuid
from app.db.session import Base
import enum


class ChatRoomStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class SenderType(str, enum.Enum):
    DOCTOR = "doctor"
    PATIENT = "patient"
    SYSTEM = "system"


class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"


class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    appointment_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    status = Column(SQLEnum(ChatRoomStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]), nullable=False, default=ChatRoomStatus.ACTIVE, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        {"comment": "Chat rooms between doctors and patients"}
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_room_id = Column(UUID(as_uuid=True), ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    sender_type = Column(SQLEnum(SenderType, native_enum=False, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    message_type = Column(SQLEnum(MessageType, native_enum=False, values_callable=lambda x: [e.value for e in x]), nullable=False, default=MessageType.TEXT)
    message = Column(Text, nullable=False, comment="Encrypted message content (Fernet encryption)")
    is_encrypted = Column(Boolean, nullable=False, default=True, comment="Flag indicating if message is encrypted")
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    __table_args__ = (
        {"comment": "Chat messages within chat rooms"}
    )
