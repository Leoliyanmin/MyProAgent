from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from business.auth_service import AuthService
from service.user_service import UserService
from config import settings

security = HTTPBearer(auto_error=False)
auth_service = AuthService()
user_service = UserService()


def _extract_user_id_from_payload(payload: dict | None) -> str | None:
    if not payload:
        return None
    user_id = payload.get("user_id") or payload.get("sub")
    if user_id is None:
        return None
    return str(user_id)


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    if settings.TEST_MODE:
        if credentials is not None:
            payload = auth_service.decode_token(credentials.credentials)
            user_id = _extract_user_id_from_payload(payload)
            if user_id is not None:
                return user_id
        return "test_user"
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
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
    token = websocket.query_params.get("token")
    if not token:
        protocols = websocket.headers.get("sec-websocket-protocol", "")
        if protocols:
            token = protocols.split(",")[-1].strip()

    if not token:
        return None

    payload = auth_service.decode_token(token)
    user_id = _extract_user_id_from_payload(payload)
    if user_id is None:
        return None

    return user_id
