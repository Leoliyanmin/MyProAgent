import logging
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        pass
        
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
            logger.error("SMTP认证失败，请检查SMTP配置和应用专用密码: %s", e)
            return {'success': False, 'message': 'SMTP认证失败，请检查邮箱配置'}
        except smtplib.SMTPException as e:
            logger.error("SMTP错误: %s", e)
            return {'success': False, 'message': '邮件服务错误，请稍后重试'}
        except Exception as e:
            logger.error("发送邮件时发生错误: %s", e)
            return {'success': False, 'message': '邮件发送失败，请稍后重试'}
    
    def send_verification_code(self, email: str, purpose: str = "register") -> dict:
        code = self.generate_verification_code()
        logger.info("验证码已生成 (邮箱: %s, 用途: %s)", email, purpose)

        email_result = self.send_verification_email(email, code, purpose)

        if not email_result['success']:
            return {
                'success': False,
                'message': email_result['message']
            }

        return {
            'success': True,
            'message': '验证码已发送，请查收邮件',
            'expires_in': settings.VERIFICATION_CODE_EXPIRE_MINUTES * 60
        }