from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from layers.business.auth_service import AuthService

security = HTTPBearer()
auth_service = AuthService()


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = auth_service.decode_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    user_id = payload.get("user_id")
    
    if user_id is None:
        raise credentials_exception
    
    return user_id
