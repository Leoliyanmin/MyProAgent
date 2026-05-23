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


def get_current_user_id_with_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> tuple[str, str]:
    """Get current user ID and raw JWT token.

    Like get_current_user_id but also returns the raw token string for
    downstream services that need to make authenticated API calls on
    behalf of the user (e.g. email tools calling local backend API).
    """
    if settings.TEST_MODE:
        if credentials is not None:
            token = credentials.credentials
            payload = auth_service.decode_token(token)
            user_id = _extract_user_id_from_payload(payload)
            if user_id is not None:
                return user_id, token
        return "test_user", ""
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
    return user_id, token


async def get_current_user_id_websocket(websocket: WebSocket) -> tuple[str, str] | tuple[None, None]:
    """Extract (user_id, token) from WebSocket connection query params or headers."""
    token = websocket.query_params.get("token")
    if not token:
        protocols = websocket.headers.get("sec-websocket-protocol", "")
        if protocols:
            token = protocols.split(",")[-1].strip()

    if not token:
        return None, None

    payload = auth_service.decode_token(token)
    user_id = _extract_user_id_from_payload(payload)
    if user_id is None:
        return None, None

    return user_id, token
