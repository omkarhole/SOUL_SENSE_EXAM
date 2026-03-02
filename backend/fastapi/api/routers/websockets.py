from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
import logging

from ..config import get_settings_instance
from ..services.db_service import get_db
from ..models import User
from ..root_models import TokenRevocation
from ..services.websocket_manager import manager

router = APIRouter()
logger = logging.getLogger("websocket_router")
settings = get_settings_instance()

async def get_ws_user(
    websocket: WebSocket,
    token: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.jwt_algorithm])
        
        # Check if token is revoked
        rev_stmt = select(TokenRevocation).filter(TokenRevocation.token_str == token)
        rev_res = await db.execute(rev_stmt)
        if rev_res.scalar_one_or_none():
            logger.warning("Revoked token used for WS connection")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        username: str = payload.get("sub")
        if not username:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
    except JWTError:
        logger.warning("Invalid JWT used for WS connection")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    from ..services.cache_service import cache_service
    cache_key = f"user_rbac:{username}"
    user_data = await cache_service.get(cache_key)

    if user_data:
        class CachedUser:
            def __init__(self, **entries):
                self.__dict__.update(entries)
        user = CachedUser(**user_data)
    else:
        user_stmt = select(User).filter(User.username == username)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        
        if user:
            user_data = {
                "id": user.id,
                "username": user.username,
                "is_active": user.is_active,
                "is_deleted": user.is_deleted,
                "deleted_at": user.deleted_at.isoformat() if getattr(user, 'deleted_at', None) else None,
                "is_admin": getattr(user, 'is_admin', False)
            }
            await cache_service.set(cache_key, user_data, 3600)
    if user is None or getattr(user, 'is_deleted', False) or getattr(user, 'deleted_at', None) is not None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
        
    if not getattr(user, 'is_active', True):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
        
    return user

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user: User = Depends(get_ws_user)
):
    if not user:
        return # connection already closed in dependency
        
    await manager.connect(websocket, user.id)
    
    try:
        # Acknowledge connection
        await manager.send_personal_message(user.id, {"type": "connection_established", "message": f"Connected as {user.username}"})
        
        while True:
            try:
                data = await websocket.receive_json()
                action = data.get("action")
                payload = data.get("payload", {})

                # Example RBAC checks for specific actions
                if action == "admin_broadcast":
                    # Check if user is an admin
                    if not getattr(user, "is_admin", False):
                        await manager.send_personal_message(user.id, {
                            "type": "error",
                            "message": "Permission denied: Admin role required for 'admin_broadcast'"
                        })
                        continue

                    # Execute the restricted action
                    broadcast_msg = payload.get("message", "Empty broadcast")
                    await manager.broadcast({
                        "type": "admin_broadcast",
                        "message": broadcast_msg,
                        "from": user.username
                    })
                    
                else:
                    # Handle normal user actions
                    await manager.send_personal_message(user.id, {
                        "type": "ack",
                        "action": action,
                        "status": "received"
                    })
                    
            except ValueError:
                # Handle non-JSON messages
                data = await websocket.receive_text()
                await manager.send_personal_message(user.id, {
                    "type": "error",
                    "message": "Only JSON messages are supported"
                })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id)
        logger.info(f"User {user.username} (ID: {user.id}) disconnected from WS.")
        
@router.post("/broadcast", include_in_schema=False)
async def trigger_broadcast(message: dict):
    # This is a test endpoint to simulate a server broadcast
    # In reality, this would be protected by admin RBAC
    await manager.broadcast(message)
    return {"status": "broadcasted"}
