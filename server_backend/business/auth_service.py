from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from config import settings
from business.email_service import EmailService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self):
        self.email_service = EmailService()
    
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
        return "@" in email and "." in email.split("@")[-1]
    
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
        
        # 检查是否跳过验证码验证
        if not settings.SKIP_VERIFICATION:
            if not verification_code or len(verification_code.strip()) == 0:
                return {'valid': False, 'message': '验证码不能为空'}
        
        return {'valid': True, 'message': '注册数据验证通过'}
    
    def send_verification_code(self, email: str, purpose: str = "register") -> dict:
        return self.email_service.send_verification_code(email, purpose)
    
    def verify_registration_code(self, email: str, code: str) -> bool:
        return self.email_service.verify_code(email, code, "register")