from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from datetime import datetime
import json
import asyncio
from app.services.chat_service import ChatService
from app.services.redis_service import redis_service
from app.db.models import SenderType, MessageType
from app.schemas.chat import (
    ChatMessageCreate,
    WSMessage,
    WSMessageType,
    WSTypingIndicator,
    WSReadReceipt
)
from app.core.security import decode_jwt_token
from app.api.websocket.chat_manager import manager
from app.core.logging import logger
from app.db.session import AsyncSessionLocal

router = APIRouter()


async def verify_websocket_token(token: str) -> tuple[str, str]:
    """
    Verify JWT token and return user_id and role.
    Compatible with fastapi-backend token structure (uses "user_id" field).
    """
    try:
        payload = await decode_jwt_token(token)
        # fastapi-backend uses "user_id" field, but also check "sub" for compatibility
        user_id = payload.get("user_id") or payload.get("sub")
        role = payload.get("role", "patient")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id"
            )
        
        return user_id, role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )


@router.websocket("/ws/chat/{room_id}")
async def websocket_chat(
    websocket: WebSocket,
    room_id: UUID,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time chat.
    
    Requires:
    - JWT token as query parameter
    - Valid room_id
    - User must have access to the room
    
    Message format:
    {
        "type": "message" | "typing" | "read_receipt" | "ping",
        "message": "text content",
        "message_type": "text" | "image" | "file"
    }
    """
    logger.info(f"WebSocket connection attempt: room_id={room_id}, token_length={len(token)}")
    user_id_str = None
    role = None
    async_db = None
    
    try:
        # Verify JWT token BEFORE accepting connection
        try:
            user_id_str, role = await verify_websocket_token(token)
        except HTTPException as e:
            logger.error(f"WebSocket token verification failed: {e.detail}")
            # Accept connection first, then close with error
            await websocket.accept()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
            return
        except Exception as e:
            logger.error(f"WebSocket token verification error: {e}", exc_info=True)
            # Accept connection first, then close with error
            await websocket.accept()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token verification failed")
            return
        
        user_id = UUID(user_id_str)
        
        # Create database session for this connection
        async_db = AsyncSessionLocal()
        chat_service = ChatService(async_db)
        
        # Verify user has access to room
        has_access = await chat_service.verify_user_access(
            room_id=room_id,
            user_id=user_id,
            role=role
        )
        
        if not has_access:
            # Accept connection first, then close with error
            await websocket.accept()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Access denied to this chat room")
            logger.warning(f"Access denied: User {user_id} to room {room_id}")
            if async_db:
                await async_db.close()
            return
        
        # Determine sender type
        sender_type = SenderType.DOCTOR if role == "doctor" else SenderType.PATIENT
        
        # Connect WebSocket
        await manager.connect(websocket, room_id, user_id)
        
        # Subscribe to Redis for this room
        async def redis_message_handler(message_data: dict):
            """Handle messages received from Redis."""
            try:
                # Don't echo back to sender
                if message_data.get("sender_id") == str(user_id):
                    return
                
                await manager.broadcast_to_room(room_id, message_data, exclude_websocket=websocket)
            except Exception as e:
                logger.error(f"Error in Redis message handler: {e}")
        
        # Start Redis subscription in background
        redis_task = asyncio.create_task(
            redis_service.subscribe_to_room(room_id, redis_message_handler)
        )
        
        try:
            # Send welcome message
            await manager.send_personal_message(
                {
                    "type": "connected",
                    "room_id": str(room_id),
                    "message": "Connected to chat room"
                },
                websocket
            )
            
            # Main message loop
            while True:
                try:
                    # Receive message from client
                    data = await websocket.receive_json()
                    message_type = data.get("type", "message")
                    
                    if message_type == "ping":
                        # Respond to ping
                        await manager.send_personal_message(
                            {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                            websocket
                        )
                        continue
                    
                    elif message_type == "typing":
                        # Handle typing indicator
                        typing_data = {
                            "type": "typing",
                            "room_id": str(room_id),
                            "sender_id": str(user_id),
                            "sender_type": sender_type.value,
                            "is_typing": data.get("is_typing", True),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                        # Broadcast to room (excluding sender)
                        await manager.broadcast_to_room(room_id, typing_data, exclude_websocket=websocket)
                        
                        # Publish to Redis for other instances
                        await redis_service.publish_message(room_id, typing_data)
                        continue
                    
                    elif message_type == "read_receipt":
                        # Handle read receipt
                        message_id = data.get("message_id")
                        if message_id:
                            # Mark as read in database
                            await chat_service.mark_message_as_read(UUID(message_id), user_id)
                            
                            receipt_data = {
                                "type": "read_receipt",
                                "room_id": str(room_id),
                                "message_id": message_id,
                                "read_by": str(user_id),
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            
                            # Broadcast to room
                            await manager.broadcast_to_room(room_id, receipt_data, exclude_websocket=websocket)
                            await redis_service.publish_message(room_id, receipt_data)
                        continue
                    
                    elif message_type == "message":
                        # Handle chat message
                        message_text = data.get("message", "").strip()
                        if not message_text:
                            await manager.send_personal_message(
                                {"type": "error", "message": "Message cannot be empty"},
                                websocket
                            )
                            continue
                        
                        # Validate message size
                        message_bytes = len(message_text.encode("utf-8"))
                        if message_bytes > 10240:
                            await manager.send_personal_message(
                                {"type": "error", "message": "Message too large (max 10KB)"},
                                websocket
                            )
                            continue
                        
                        # Create message in database
                        # Check if message is already encrypted by client (E2E)
                        is_client_encrypted = data.get("is_client_encrypted", False)
                        message_create = ChatMessageCreate(
                            message=message_text,
                            message_type=MessageType(data.get("message_type", "text")),
                            is_client_encrypted=is_client_encrypted
                        )
                        
                        chat_message = await chat_service.send_message(
                            room_id=room_id,
                            sender_id=user_id,
                            sender_type=sender_type,
                            message_data=message_create
                        )
                        
                        # Prepare message for broadcast
                        ws_message = {
                            "type": "message",
                            "room_id": str(room_id),
                            "sender_id": str(user_id),
                            "sender_type": sender_type.value,
                            "message_type": chat_message.message_type.value,
                            "message": chat_message.message,
                            "message_id": str(chat_message.id),
                            "timestamp": chat_message.created_at.isoformat()
                        }
                        
                        # Broadcast to room (excluding sender)
                        await manager.broadcast_to_room(room_id, ws_message, exclude_websocket=websocket)
                        
                        # Publish to Redis for other instances
                        await redis_service.publish_message(room_id, ws_message)
                        
                        # Confirm to sender
                        await manager.send_personal_message(
                            {
                                "type": "message_sent",
                                "message_id": str(chat_message.id),
                                "timestamp": chat_message.created_at.isoformat()
                            },
                            websocket
                        )
                    
                    else:
                        await manager.send_personal_message(
                            {"type": "error", "message": f"Unknown message type: {message_type}"},
                            websocket
                        )
                
                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    await manager.send_personal_message(
                        {"type": "error", "message": "Invalid JSON format"},
                        websocket
                    )
                    continue
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")
                    await manager.send_personal_message(
                        {"type": "error", "message": "Internal server error"},
                        websocket
                    )
                    continue
        
        finally:
            # Cleanup
            redis_task.cancel()
            try:
                await redis_task
            except asyncio.CancelledError:
                pass
            
            if async_db:
                await async_db.close()
            manager.disconnect(websocket)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for room {room_id}")
        if async_db:
            await async_db.close()
        manager.disconnect(websocket)
    except HTTPException as e:
        # HTTPException from token verification - already closed connection
        logger.warning(f"WebSocket HTTPException: {e.detail}")
        if async_db:
            await async_db.close()
        try:
            manager.disconnect(websocket)
        except:
            pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        if async_db:
            await async_db.close()
        try:
            manager.disconnect(websocket)
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except:
            pass
