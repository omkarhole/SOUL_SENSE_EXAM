import json
import asyncio
import logging
from typing import Dict, List
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from ..models import User
from ..config import get_settings_instance

logger = logging.getLogger("websocket_manager")
settings = get_settings_instance()

class ConnectionManager:
    def __init__(self):
        # Maps user_id to a list of active WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.redis_client = None
        self.pubsub = None
        self.channel_name = "soulsense_ws_events"
        self._listener_task = None
        self._is_connected = False

    async def connect_redis(self):
        if not self._is_connected:
            try:
                self.redis_client = redis.from_url(
                    settings.redis_url, 
                    encoding="utf-8", 
                    decode_responses=True
                )
                self.pubsub = self.redis_client.pubsub()
                await self.pubsub.subscribe(self.channel_name)
                self._listener_task = asyncio.create_task(self._listen())
                self._is_connected = True
                logger.info(f"[OK] WebSocketManager subscribed to Redis channel: {self.channel_name}")
                print(f"[OK] WebSocketManager subscribed to Redis channel: {self.channel_name}")
            except Exception as e:
                logger.error(f"[WARNING] Failed to connect WebSocketManager to Redis: {e}. Falling back to local broadcasting.")
                print(f"[WARNING] Failed to connect WebSocketManager to Redis: {e}. Falling back to local broadcasting.")

    async def _listen(self):
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    user_id = data.get("user_id")
                    payload = data.get("payload")
                    
                    if user_id:
                        # Direct message to specific local user connections
                        await self._send_to_local_user(user_id, payload)
                    else:
                        # Broadcast message to all local user connections
                        await self._broadcast_local(payload)
        except asyncio.CancelledError:
            logger.info("Redis listener task cancelled")
        except Exception as e:
            logger.error(f"Redis listener error: {e}")

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        # Verify redis connection on first connect
        if not self._is_connected:
            await self.connect_redis()

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def _send_to_local_user(self, user_id: int, payload: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(payload)
                except Exception as e:
                    logger.error(f"Error sending to local user {user_id}: {e}")

    async def _broadcast_local(self, payload: dict):
        for user_connections in self.active_connections.values():
            for connection in user_connections:
                try:
                    await connection.send_json(payload)
                except Exception as e:
                    pass

    async def send_personal_message(self, user_id: int, message: dict):
        """Sends message via Redis to reach user on any node"""
        if not self.redis_client or not self._is_connected:
            # Fallback for local-only functionality
            await self._send_to_local_user(user_id, message)
            return
            
        payload = {
            "user_id": user_id,
            "payload": message
        }
        try:
            await self.redis_client.publish(self.channel_name, json.dumps(payload))
        except Exception as e:
            logger.error(f"Failed to publish personal message to Redis: {e}")
            await self._send_to_local_user(user_id, message)

    async def broadcast(self, message: dict):
        """Broadcasts message via Redis to all nodes"""
        if not self.redis_client or not self._is_connected:
            await self._broadcast_local(message)
            return

        payload = {
            "user_id": None,
            "payload": message
        }
        try:
            await self.redis_client.publish(self.channel_name, json.dumps(payload))
        except Exception as e:
            logger.error(f"Failed to publish broadcast message to Redis: {e}")
            await self._broadcast_local(message)
            
    async def shutdown(self):
        try:
            if self._listener_task:
                self._listener_task.cancel()
            if self.pubsub:
                try:
                    await self.pubsub.unsubscribe(self.channel_name)
                    await self.pubsub.close()
                except Exception:
                    pass
            if self.redis_client:
                try:
                    await self.redis_client.close()
                except Exception:
                    pass
            self._is_connected = False
        except Exception:
            pass

manager = ConnectionManager()
