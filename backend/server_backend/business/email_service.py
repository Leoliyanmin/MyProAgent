import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from config import settings


class EmailService:
    def __init__(self):
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
            msg['Subject'] = f"ProAgent Verification Code"

            if purpose == "register":
                body = f"""Welcome to ProAgent!

Your verification code is: {code}

This code will expire in {settings.VERIFICATION_CODE_EXPIRE_MINUTES} minutes.

If you didn't request this, please ignore this email.

---
ProAgent Team"""
            elif purpose == "reset_password":
                body = f"""Password Reset Request

Your password reset code is: {code}

This code will expire in {settings.VERIFICATION_CODE_EXPIRE_MINUTES} minutes.

If you didn't request this, please ignore this email.

---
ProAgent Team"""
            else:
                body = f"Your verification code is: {code}"

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # Try STARTTLS first (port 587)
            try:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                    server.set_debuglevel(1)  # Enable debug output
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
                print(f"Email sent successfully via STARTTLS to {email}")
                return {'success': True, 'message': '邮件发送成功'}
            except Exception as starttls_error:
                print(f"STARTTLS failed: {starttls_error}, trying SSL...")
                # Fallback to SSL (port 465)
                with smtplib.SMTP_SSL(settings.SMTP_HOST, 465, timeout=30) as server:
                    server.set_debuglevel(1)
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
                print(f"Email sent successfully via SSL to {email}")
                return {'success': True, 'message': '邮件发送成功'}

        except smtplib.SMTPAuthenticationError as e:
            print(f"SMTP认证失败: {e}")
            print("请检查SMTP配置：")
            print("1. 确保使用的是 Gmail 应用专用密码（App Password），不是普通密码")
            print("2. 访问 https://myaccount.google.com/apppasswords 生成")
            return {'success': False, 'message': f'SMTP认证失败: {str(e)}。请确保使用 Gmail 应用专用密码。'}
        except smtplib.SMTPException as e:
            print(f"SMTP错误: {e}")
            return {'success': False, 'message': f'SMTP错误: {str(e)}'}
        except Exception as e:
            print(f"发送邮件时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'发送邮件时发生错误: {str(e)}'}
    
    def send_verification_code(self, email: str, purpose: str = "register") -> dict:
        if getattr(settings, 'SKIP_RATE_LIMIT', False):
            print("跳过频率限制模式：直接允许请求")
        
        code = self.generate_verification_code()
        print(f"生成的验证码: {code} (邮箱: {email}, 用途: {purpose})")
        
        email_result = self.send_verification_email(email, code, purpose)
        
        if not email_result['success']:
            if self.test_mode:
                print("测试模式：即使邮件发送失败，也继续")
            else:
                return {
                    'success': False,
                    'message': f'发送验证码失败: {email_result["message"]}'
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