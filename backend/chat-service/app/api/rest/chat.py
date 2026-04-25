from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from app.db.session import get_db
from app.services.chat_service import ChatService
from app.db.models import SenderType
from app.schemas.chat import (
    StartChatRequest,
    StartChatResponse,
    ChatRoomListResponse,
    ChatRoomResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatMessageListResponse,
    CloseChatRequest,
    LastMessageResponse
)
from app.core.security import get_current_user_id, get_user_role, extract_token_from_header
from app.core.logging import logger

router = APIRouter(prefix="/chat", tags=["chat"])


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> tuple[str, str]:
    """
    Dependency to get current user ID and role from JWT token.
    """
    token = extract_token_from_header(authorization)
    user_id = await get_current_user_id(token)
    role = await get_user_role(token)
    return user_id, role


@router.post("/start", response_model=StartChatResponse, status_code=status.HTTP_201_CREATED)
async def start_chat(
    request: StartChatRequest,
    db: AsyncSession = Depends(get_db),
    user_info: tuple[str, str] = Depends(get_current_user)
):
    """
    Start a new chat room between doctor and patient.
    Only doctors can start chats.
    """
    user_id, role = user_info
    
    if role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can start chats"
        )
    
    try:
        doctor_id = UUID(user_id)
        patient_id = request.patient_id
        
        chat_service = ChatService(db)
        chat_room = await chat_service.start_chat(
            doctor_id=doctor_id,
            patient_id=patient_id,
            appointment_id=request.appointment_id
        )
        
        # Automatically mark existing messages as read when starting chat (default behavior)
        # This happens when a doctor opens an existing chat room
        try:
            await chat_service.mark_room_messages_as_read(
                room_id=chat_room.id,
                reader_id=doctor_id
            )
            logger.info(f"Automatically marked existing messages as read when starting chat {chat_room.id}")
        except Exception as e:
            # Don't fail the request if marking as read fails
            logger.warning(f"Failed to mark existing messages as read: {e}")
        
        return StartChatResponse(
            room_id=chat_room.id,
            doctor_id=chat_room.doctor_id,
            patient_id=chat_room.patient_id,
            appointment_id=chat_room.appointment_id,
            status=chat_room.status.value,
            created_at=chat_room.created_at
        )
    except Exception as e:
        logger.error(f"Error starting chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start chat"
        )


def _build_rooms_response(rooms_data: list[dict]) -> list[ChatRoomResponse]:
    """Helper to map enriched room dicts to ChatRoomResponse objects."""
    rooms: list[ChatRoomResponse] = []
    for room_data in rooms_data:
        # Build last_message response if exists
        last_message = None
        if room_data.get("last_message"):
            last_message = LastMessageResponse(**room_data["last_message"])
        
        room_response = ChatRoomResponse(
            id=UUID(room_data["id"]),
            doctor_id=UUID(room_data["doctor_id"]),
            patient_id=UUID(room_data["patient_id"]),
            appointment_id=UUID(room_data["appointment_id"]) if room_data.get("appointment_id") else None,
            status=room_data["status"],
            created_at=room_data["created_at"],
            updated_at=room_data["updated_at"],
            patient_name=room_data.get("patient_name"),
            patient_email=room_data.get("patient_email"),
            patient_image=room_data.get("patient_image"),
            doctor_name=room_data.get("doctor_name"),
            doctor_email=room_data.get("doctor_email"),
            doctor_image=room_data.get("doctor_image"),
            last_message=last_message,
            unread_count=room_data.get("unread_count", 0)
        )
        rooms.append(room_response)
    return rooms


@router.get("/rooms", response_model=ChatRoomListResponse)
async def get_chat_rooms(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user_info: tuple[str, str] = Depends(get_current_user)
):
    """
    Get all chat rooms for the current user (both active and closed).
    Includes patient/doctor info, last message, and unread count.
    """
    user_id, role = user_info
    
    try:
        chat_service = ChatService(db)
        rooms_data, total = await chat_service.get_user_chat_rooms_with_details(
            user_id=UUID(user_id),
            role=role,
            limit=min(limit, 100),
            offset=offset
        )
        
        rooms = _build_rooms_response(rooms_data)
        
        return ChatRoomListResponse(
            rooms=rooms,
            total=total
        )
    except Exception as e:
        logger.error(f"Error getting chat rooms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat rooms"
        )


@router.get("/rooms/active", response_model=ChatRoomListResponse)
async def get_active_chat_rooms(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user_info: tuple[str, str] = Depends(get_current_user)
):
    """
    Get only active chat rooms for the current user.
    """
    user_id, role = user_info
    
    try:
        chat_service = ChatService(db)
        rooms_data, total = await chat_service.get_user_chat_rooms_with_details(
            user_id=UUID(user_id),
            role=role,
            limit=min(limit, 100),
            offset=offset,
            status="active"
        )
        
        rooms = _build_rooms_response(rooms_data)
        
        return ChatRoomListResponse(
            rooms=rooms,
            total=total
        )
    except Exception as e:
        logger.error(f"Error getting active chat rooms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active chat rooms"
        )


@router.get("/rooms/closed", response_model=ChatRoomListResponse)
async def get_closed_chat_rooms(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user_info: tuple[str, str] = Depends(get_current_user)
):
    """
    Get only closed chat rooms for the current user.
    """
    user_id, role = user_info
    
    try:
        chat_service = ChatService(db)
        rooms_data, total = await chat_service.get_user_chat_rooms_with_details(
            user_id=UUID(user_id),
            role=role,
            limit=min(limit, 100),
            offset=offset,
            status="closed"
        )
        
        rooms = _build_rooms_response(rooms_data)
        
        return ChatRoomListResponse(
            rooms=rooms,
            total=total
        )
    except Exception as e:
        logger.error(f"Error getting closed chat rooms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get closed chat rooms"
        )


@router.get("/{room_id}/messages", response_model=ChatMessageListResponse)
async def get_chat_messages(
    room_id: UUID,
    limit: int = 100,
    offset: int = 0,
    mark_as_read: bool = True,  # Automatically mark messages as read when fetching
    db: AsyncSession = Depends(get_db),
    user_info: tuple[str, str] = Depends(get_current_user)
):
    """
    Get messages for a specific chat room.
    Verifies user has access to the room.
    
    By default, messages are automatically marked as read when fetched.
    Set mark_as_read=false to prevent automatic marking.
    """
    user_id, role = user_info
    
    try:
        chat_service = ChatService(db)
        
        # Verify access
        has_access = await chat_service.verify_user_access(
            room_id=room_id,
            user_id=UUID(user_id),
            role=role
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat room"
            )
        
        messages, total = await chat_service.get_chat_messages(
            room_id=room_id,
            limit=min(limit, 200),
            offset=offset
        )
        
        # Automatically mark messages as read when fetching (default behavior)
        if mark_as_read:
            try:
                await chat_service.mark_room_messages_as_read(
                    room_id=room_id,
                    reader_id=UUID(user_id)
                )
                logger.info(f"Automatically marked messages as read for user {user_id} in room {room_id}")
            except Exception as e:
                # Don't fail the request if marking as read fails
                logger.warning(f"Failed to mark messages as read: {e}")
        
        return ChatMessageListResponse(
            messages=[
                ChatMessageResponse(
                    id=msg.id,
                    chat_room_id=msg.chat_room_id,
                    sender_id=msg.sender_id,
                    sender_type=msg.sender_type.value,
                    message_type=msg.message_type.value,
                    message=msg.message,
                    read_at=msg.read_at,
                    created_at=msg.created_at
                )
                for msg in messages
            ],
            total=total,
            room_id=room_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages"
        )


@router.post("/{room_id}/mark-unread", status_code=status.HTTP_200_OK)
async def mark_room_messages_as_unread(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_info: tuple[str, str] = Depends(get_current_user)
):
    """
    Mark all messages in a room as unread (reset read count).
    This will reset the read_at timestamp to NULL for all messages in the room
    that were previously read by the current user.
    """
    user_id, role = user_info
    
    try:
        chat_service = ChatService(db)
        
        # Verify access
        has_access = await chat_service.verify_user_access(
            room_id=room_id,
            user_id=UUID(user_id),
            role=role
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat room"
            )
        
        count = await chat_service.mark_room_messages_as_unread(
            room_id=room_id,
            user_id=UUID(user_id)
        )
        
        return {
            "success": True,
            "message": f"Marked {count} message(s) as unread",
            "count": count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking messages as unread: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark messages as unread"
        )


@router.post("/{room_id}/close", status_code=status.HTTP_204_NO_CONTENT)
async def close_chat_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_info: tuple[str, str] = Depends(get_current_user)
):
    """
    Close a chat room.
    Only doctors can close chat rooms.
    """
    user_id, role = user_info
    
    if role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can close chat rooms"
        )
    
    try:
        chat_service = ChatService(db)
        
        # Verify access
        has_access = await chat_service.verify_user_access(
            room_id=room_id,
            user_id=UUID(user_id),
            role=role
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat room"
            )
        
        success = await chat_service.close_chat_room(room_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat room not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing chat room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close chat room"
        )
