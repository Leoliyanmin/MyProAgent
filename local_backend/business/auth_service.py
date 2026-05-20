from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from config import settings
import httpx

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


class AuthService:
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None

    def validate_email(self, email: str) -> bool:
        return email.endswith("@mail.sustech.edu.cn")

    def validate_password(self, password: str) -> dict:
        if len(password) < 8:
            return {'valid': False, 'message': '密码长度至少为8位'}

        if not any(char.isupper() for char in password):
            return {'valid': False, 'message': '密码必须包含至少一个大写字母'}

        if not any(char.islower() for char in password):
            return {'valid': False, 'message': '密码必须包含至少一个小写字母'}

        if not any(char.isdigit() for char in password):
            return {'valid': False, 'message': '密码必须包含至少一个数字'}

        return {'valid': True, 'message': '密码格式正确'}

    def validate_registration_data(self, email: str, password: str, confirm_password: str, verification_code: str) -> dict:
        email_validation = self.validate_email(email)
        if not email_validation:
            return {'valid': False, 'message': '邮箱格式不正确，必须使用@mail.sustech.edu.cn域名'}

        password_validation = self.validate_password(password)
        if not password_validation['valid']:
            return password_validation

        if password != confirm_password:
            return {'valid': False, 'message': '两次输入的密码不一致'}

        if not settings.SKIP_VERIFICATION:
            if not verification_code or len(verification_code.strip()) == 0:
                return {'valid': False, 'message': '验证码不能为空'}

        return {'valid': True, 'message': '注册数据验证通过'}

    async def send_verification_code(self, email: str, purpose: str = "register") -> dict:
        if settings.TEST_MODE or settings.SKIP_VERIFICATION:
            return {
                'success': True,
                'message': 'TEST MODE: 验证码已发送（任意验证码均可使用）',
                'test_code': '123456',
                'expires_in': 300,
                'retry_after': 60
            }
        try:
            url = f"{settings.SERVER_BACKEND_URL}/auth/verification/send"
            data = {
                "email": email,
                "purpose": purpose
            }
            client = await _get_client()
            response = await client.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                return {
                    'success': False,
                    'message': f'发送验证码失败，服务器返回: {response.status_code}'
                }
        except Exception as e:
            print(f"Error sending verification code: {e}")
            return {
                'success': False,
                'message': '发送验证码失败，请稍后重试'
            }

    def verify_registration_code(self, email: str, code: str) -> bool:
        return True