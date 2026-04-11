import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
from database.redis_connection import get_redis


class EmailService:
    def __init__(self):
        self.redis = get_redis()
        self.test_mode = getattr(settings, 'TEST_MODE', False)
        
    def generate_verification_code(self, length: int = None) -> str:
        if length is None:
            length = settings.VERIFICATION_CODE_LENGTH
        return ''.join(random.choices(string.digits, k=length))
    
    def send_verification_email(self, email: str, code: str, purpose: str = "register") -> dict:
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg['To'] = email
            msg['Subject'] = f"验证码 - {purpose.upper()}"
            
            if purpose == "register":
                body = f"""
                您的验证码是: {code}
                
                该验证码将在 {settings.VERIFICATION_CODE_EXPIRE_MINUTES} 分钟后过期。
                
                如果这不是您的操作，请忽略此邮件。
                """
            elif purpose == "reset_password":
                body = f"""
                您的密码重置验证码是: {code}
                
                该验证码将在 {settings.VERIFICATION_CODE_EXPIRE_MINUTES} 分钟后过期。
                
                如果这不是您的操作，请忽略此邮件。
                """
            else:
                body = f"您的验证码是: {code}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            return {'success': True, 'message': '邮件发送成功'}
        except smtplib.SMTPAuthenticationError as e:
            print(f"SMTP认证失败: {e}")
            print("请检查SMTP配置，确保使用正确的应用专用密码")
            return {'success': False, 'message': f'SMTP认证失败: {str(e)}'}
        except smtplib.SMTPException as e:
            print(f"SMTP错误: {e}")
            return {'success': False, 'message': f'SMTP错误: {str(e)}'}
        except Exception as e:
            print(f"发送邮件时发生错误: {e}")
            return {'success': False, 'message': f'发送邮件时发生错误: {str(e)}'}
    
    def store_verification_code(self, email: str, code: str, purpose: str = "register") -> bool:
        try:
            key = f"verification_code:{purpose}:{email}"
            expire_seconds = settings.VERIFICATION_CODE_EXPIRE_MINUTES * 60
            self.redis.setex(key, expire_seconds, code)
            print(f"验证码已存储到Redis: {code} (有效期: {expire_seconds}秒)")
            return True
        except Exception as e:
            print(f"存储验证码时发生错误: {e}")
            return False
    
    def verify_code(self, email: str, code: str, purpose: str = "register") -> bool:
        try:
            key = f"verification_code:{purpose}:{email}"
            stored_code = self.redis.get(key)
            
            if not stored_code:
                print(f"验证码不存在或已过期: {email}")
                return False
            
            stored_code_str = stored_code.decode() if isinstance(stored_code, bytes) else stored_code
            
            if stored_code_str == code:
                self.redis.delete(key)
                print(f"验证码验证成功: {email}")
                return True
            
            print(f"验证码不匹配: 期望 {stored_code_str}, 实际 {code}")
            return False
        except Exception as e:
            print(f"验证验证码时发生错误: {e}")
            return False
    
    def check_rate_limit(self, email: str, purpose: str = "register") -> tuple[bool, int]:
        # 检查是否跳过频率限制
        if getattr(settings, 'SKIP_RATE_LIMIT', False):
            print("跳过频率限制模式：直接允许请求")
            return True, 0
        
        try:
            key = f"rate_limit:{purpose}:{email}"
            current_count = self.redis.get(key)
            
            if current_count is None:
                expire_seconds = settings.RATE_LIMIT_WINDOW_MINUTES * 60
                self.redis.setex(key, expire_seconds, 1)
                return True, 1
            
            count = int(current_count)
            if count >= settings.RATE_LIMIT_MAX_REQUESTS:
                ttl = self.redis.ttl(key)
                return False, ttl
            
            self.redis.incr(key)
            return True, count + 1
        except Exception as e:
            print(f"检查频率限制时发生错误: {e}")
            return True, 0
    
    def send_verification_code(self, email: str, purpose: str = "register") -> dict:
        is_allowed, remaining = self.check_rate_limit(email, purpose)
        
        if not is_allowed:
            minutes_left = remaining // 60
            return {
                'success': False,
                'message': f'请求过于频繁，请 {minutes_left} 分钟后再试',
                'retry_after': remaining
            }
        
        code = self.generate_verification_code()
        print(f"生成的验证码: {code} (邮箱: {email}, 用途: {purpose})")
        
        email_result = self.send_verification_email(email, code, purpose)
        
        if not email_result['success']:
            if self.test_mode:
                print("测试模式：即使邮件发送失败，也继续存储验证码")
            else:
                return {
                    'success': False,
                    'message': f'发送验证码失败: {email_result["message"]}'
                }
        
        if not self.store_verification_code(email, code, purpose):
            return {
                'success': False,
                'message': '存储验证码失败，请稍后重试'
            }
        
        message = '验证码已发送，请查收邮件'
        if not email_result['success']:
            message = f'验证码已生成 (邮件发送失败: {email_result["message"]})，测试验证码: {code}'
        
        result = {
            'success': True,
            'message': message,
            'expires_in': settings.VERIFICATION_CODE_EXPIRE_MINUTES * 60
        }
        
        if self.test_mode:
            result['test_code'] = code
            print(f"测试模式：返回测试验证码: {code}")
        
        return result