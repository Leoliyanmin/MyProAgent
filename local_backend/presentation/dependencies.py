from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from business.auth_service import AuthService
from service.user_service import UserService

security = HTTPBearer()
auth_service = AuthService()
user_service = UserService()


def _extract_user_id_from_payload(payload: dict | None) -> str | None:
    if not payload:
        return None

    # Backward compatibility: some old tokens only carry `sub`.
    user_id = payload.get("user_id") or payload.get("sub")
    if user_id is None:
        return None
    return str(user_id)


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    payload = auth_service.decode_token(token)
    user_id = _extract_user_id_from_payload(payload)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


async def get_current_user_id_websocket(websocket: WebSocket) -> str | None:
    """从 WebSocket 连接中获取用户 ID"""
    # 从查询参数中获取 token
    token = websocket.query_params.get("token")
    if not token:
        # 尝试从子协议中获取
        protocols = websocket.headers.get("sec-websocket-protocol", "")
        if protocols:
            token = protocols.split(",")[-1].strip()

    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return None

    payload = auth_service.decode_token(token)
    user_id = _extract_user_id_from_payload(payload)
    if user_id is None:
        await websocket.close(code=4001, reason="Invalid token")
        return None

    return user_id
