from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from passlib.context import CryptContext
import jwt
from . import config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')

def generate_jwt(data: dict, expires_delta: timedelta | None = None):
    """生成JWT令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    print(config.SECRETE_KEY)
    encoded_jwt = jwt.encode(to_encode, str(config.SECRETE_KEY), config.JWT_ENCODE_ALGORITHM)
    return encoded_jwt

def generate_access_jwt(sid: str, expires_delta: timedelta | None = None):
    """
    :param sid: 学号
    :param expires_delta: token 有效期
    :return: JWT 字符串
    """
    return generate_jwt(data={"sub": sid}, expires_delta=expires_delta)

def extract_payloads(token: str):
    payload = jwt.decode(token, str(config.SECRETE_KEY), algorithms=[config.JWT_ENCODE_ALGORITHM])
    return payload

def extract_sid(token: str) -> str | None:
    """
    Extract sid from a JWT.
    :param token: JWT.
    :return: username: extracted username.
    """
    try:
        payload = extract_payloads(token)
    except InvalidTokenError:
        return None
    return payload.get("sub")