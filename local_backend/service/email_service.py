import json
import logging
import smtplib
import traceback
from email.message import EmailMessage
from typing import Dict, Optional

from service.scraper.mail_scraper import MailScraper, write_mail_result
from database.code.handle.database_email_handle import EmailHandle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.email_handle = EmailHandle()

    def get_email_status(self, user_id: str) -> Dict:
        try:
            result = self.email_handle.handle_get_email_status(user_id)
            if result['success']:
                return {
                    'success': True,
                    'is_bound': result.get('is_bound', False),
                    'email_address': result.get('email_address', ''),
                    'bind_time': result.get('bind_time', ''),
                    'last_sync_time': result.get('last_sync_time', ''),
                }
            else:
                return {'success': False, 'message': result.get('message', '获取状态失败')}
        except Exception as e:
            logger.error(f"获取邮箱状态失败: {str(e)}")
            return {'success': False, 'message': f'获取状态失败: {str(e)}'}

    def bind_with_app_password(self, user_id: str, email_address: str, app_password: str) -> Dict:
        try:
            logger.info(f"绑定邮箱: user_id={user_id}, email={email_address}")

            scraper = MailScraper(email_address, app_password)
            try:
                if not scraper.test_connection():
                    return {'success': False, 'message': 'IMAP连接测试返回失败，请检查后重试'}
            except ConnectionError as e:
                logger.error(f"IMAP连接测试失败: {e}")
                return {'success': False, 'message': str(e)}
            except Exception as e:
                logger.error(f"IMAP连接测试异常:\n{traceback.format_exc()}")
                return {'success': False, 'message': f'IMAP连接测试失败: {str(e)}'}

            encrypted_password = self._encrypt_app_password(app_password)

            account = self.email_handle.account_ops.get_email_account(user_id)
            if account:
                self.email_handle.handle_unbind_email(user_id)

            bind_result = self.email_handle.handle_bind_email(
                user_id=user_id,
                email_address=email_address,
                encrypted_app_password=encrypted_password,
            )

            if bind_result['success']:
                logger.info(f"邮箱绑定成功: user_id={user_id}, email={email_address}")
                return {'success': True, 'message': '邮箱账号绑定成功', 'email_address': email_address}
            else:
                return bind_result

        except Exception as e:
            logger.error(f"绑定邮箱失败: {str(e)}")
            return {'success': False, 'message': f'绑定邮箱失败: {str(e)}'}

    def sync_email_data(self, user_id: str, max_messages: int = 50) -> Dict:
        try:
            logger.info(f"同步邮件数据: user_id={user_id}")

            account_info = self.email_handle.account_ops.get_email_account(user_id)
            if not account_info:
                return {'success': False, 'message': '未绑定邮箱账号，请先绑定'}

            email_address = account_info['account_platform_username']
            encrypted_password = account_info.get('content', '')
            app_password = self._decrypt_app_password(encrypted_password)

            scraper = MailScraper(email_address, app_password)
            scrape_result = scraper.scrape_mail_detail(max_messages=max_messages)

            write_mail_result(scrape_result)

            sync_result = self.email_handle.handle_sync_messages(
                user_id=user_id,
                messages=scrape_result.get('messages', []),
            )

            if sync_result['success']:
                return {
                    'success': True,
                    'message': sync_result['message'],
                    'data': {
                        'total': scrape_result.get('total', 0),
                        'synced': len(scrape_result.get('messages', [])),
                    },
                }
            else:
                return sync_result

        except Exception as e:
            logger.error(f"同步邮件数据失败: {str(e)}")
            return {'success': False, 'message': f'同步邮件数据失败: {str(e)}'}

    def unbind_email(self, user_id: str) -> Dict:
        try:
            result = self.email_handle.handle_unbind_email(user_id)
            return result
        except Exception as e:
            logger.error(f"解绑邮箱失败: {str(e)}")
            return {'success': False, 'message': f'解绑失败: {str(e)}'}

    def _encrypt_app_password(self, app_password: str) -> str:
        return json.dumps({"password": app_password})

    def _decrypt_app_password(self, encrypted: str) -> str:
        try:
            data = json.loads(encrypted)
            return data.get('password', '')
        except (json.JSONDecodeError, TypeError):
            return encrypted

    def get_email_messages(self, user_id: str) -> Dict:
        try:
            result = self.email_handle.handle_get_messages(user_id)
            return result
        except Exception as e:
            logger.error(f"获取邮件列表失败: {str(e)}")
            return {'success': False, 'message': str(e)}

    def send_email(self, user_id: str, title: str, context: str, receiver: str) -> Dict:
        try:
            account_info = self.email_handle.account_ops.get_email_account(user_id)
            if not account_info:
                return {'success': False, 'message': '未绑定邮箱账号，请先绑定'}

            sender = account_info['account_platform_username']
            encrypted_password = account_info.get('content', '')
            app_password = self._decrypt_app_password(encrypted_password)

            msg = EmailMessage()
            msg['Subject'] = title
            msg['From'] = sender
            msg['To'] = receiver
            msg.set_content(context)

            with smtplib.SMTP_SSL('smtp.exmail.qq.com', 465) as server:
                server.login(sender, app_password)
                server.send_message(msg)

            logger.info(f"邮件发送成功: from={sender}, to={receiver}, subject={title}")
            return {'success': True, 'message': '邮件发送成功'}
        except smtplib.SMTPAuthenticationError:
            logger.error(f"SMTP认证失败: user_id={user_id}")
            return {'success': False, 'message': 'SMTP认证失败，请检查客户端专用密码'}
        except smtplib.SMTPRecipientsRefused:
            return {'success': False, 'message': '收件人地址被拒绝'}
        except Exception as e:
            logger.error(f"发送邮件失败: {str(e)}")
            return {'success': False, 'message': f'发送失败: {str(e)}'}
