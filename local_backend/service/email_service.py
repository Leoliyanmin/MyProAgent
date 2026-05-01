import json
import logging
import traceback
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

            return {
                'success': True,
                'message': f'邮件爬取完成，共 {scrape_result.get("total", 0)} 封邮件，本次获取 {len(scrape_result.get("messages", []))} 封',
                'data': {
                    'total': scrape_result.get('total', 0),
                    'synced': len(scrape_result.get('messages', [])),
                },
            }

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
