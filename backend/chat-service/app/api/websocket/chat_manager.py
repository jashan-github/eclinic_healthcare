from typing import Dict, Set
from uuid import UUID
from fastapi import WebSocket, WebSocketDisconnect
from app.core.logging import logger
import json


class ConnectionManager:
    """Manages WebSocket connections for chat rooms."""
    
    def __init__(self):
        # Map room_id -> set of WebSocket connections
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
        # Map WebSocket -> (room_id, user_id)
        self.connection_info: Dict[WebSocket, tuple[UUID, UUID]] = {}
    
    async def connect(self, websocket: WebSocket, room_id: UUID, user_id: UUID):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        
        self.active_connections[room_id].add(websocket)
        self.connection_info[websocket] = (room_id, user_id)
        
        logger.info(f"User {user_id} connected to room {room_id}")
    
    def disconnect(self, websocket: WebSocket):
        """Unregister a WebSocket connection."""
        if websocket in self.connection_info:
            room_id, user_id = self.connection_info[websocket]
            
            if room_id in self.active_connections:
                self.active_connections[room_id].discard(websocket)
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]
            
            del self.connection_info[websocket]
            logger.info(f"User {user_id} disconnected from room {room_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast_to_room(self, room_id: UUID, message: dict, exclude_websocket: WebSocket = None):
        """Broadcast a message to all connections in a room."""
        if room_id not in self.active_connections:
            return
        
        disconnected = set()
        for websocket in self.active_connections[room_id]:
            if websocket == exclude_websocket:
                continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to room {room_id}: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            self.disconnect(ws)
    
    def get_room_connections_count(self, room_id: UUID) -> int:
        """Get number of active connections in a room."""
        return len(self.active_connections.get(room_id, set()))


# Global connection manager instance
manager = ConnectionManager()
