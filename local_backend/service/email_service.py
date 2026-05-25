import json
import logging
import smtplib
import traceback
import hashlib
import base64
import datetime
from email.message import EmailMessage
from typing import Dict, Optional

from cryptography.fernet import Fernet, InvalidToken

from service.scraper.mail_scraper import MailScraper, write_mail_result
from database.code.handle.database_email_v2_handle import EmailV2Handle
from local_backend.database.code.command.database_command import upsert_user
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.email_handle = EmailV2Handle()

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

            account = self.email_handle.account_ops.get(user_id)
            if account:
                self.email_handle.handle_unbind_email(user_id)

            upsert_user(
                user_id=user_id,
                username=user_id,
                user_email=user_id,
                user_is_active=1,
                user_created_at=datetime.datetime.utcnow().isoformat(),
                user_last_login=None,
                user_source_device_id=None,
            )

            bind_result = self.email_handle.handle_bind_email(
                user_id=user_id,
                email_address=email_address,
                encrypted_password=encrypted_password,
            )

            if bind_result['success']:
                logger.info(f"邮箱绑定成功: user_id={user_id}, email={email_address}")
                return {'success': True, 'message': '邮箱账号绑定成功', 'email_address': email_address}
            else:
                return bind_result

        except Exception as e:
            logger.error(f"绑定邮箱失败: {str(e)}")
            return {'success': False, 'message': f'绑定邮箱失败: {str(e)}'}

    def sync_email_data(self, user_id: str, max_messages: int = 50, incremental: bool = True) -> Dict:
        try:
            logger.info(f"同步邮件数据: user_id={user_id}")

            account_info = self.email_handle.account_ops.get(user_id)
            if not account_info:
                return {'success': False, 'message': '未绑定邮箱账号，请先绑定'}

            email_address = account_info['email_address']
            encrypted_password = account_info.get('encrypted_password', '')
            app_password = self._decrypt_app_password(encrypted_password)

            scraper = MailScraper(email_address, app_password)

            # Incremental sync: use SINCE date if last_sync_time exists
            if incremental:
                last_sync = account_info.get('last_sync_time', '')
                if last_sync:
                    try:
                        last_sync_dt = datetime.datetime.strptime(last_sync[:10], "%Y-%m-%d")
                        days_since = max(1, (datetime.datetime.now() - last_sync_dt).days + 1)
                        scrape_result = scraper.scrape_recent_mails(days=days_since)
                        logger.info(f"增量同步: last_sync={last_sync}, days_since={days_since}, fetched={scrape_result['returned']}")
                    except Exception:
                        scrape_result = scraper.scrape_mail_detail(max_messages=max_messages)
                else:
                    scrape_result = scraper.scrape_mail_detail(max_messages=max_messages)
            elif max_messages:
                scrape_result = scraper.scrape_mail_detail(max_messages=max_messages)
            else:
                scrape_result = scraper.scrape_recent_mails(days=1)

            write_mail_result(scrape_result)

            sync_result = self.email_handle.handle_sync_messages(
                user_id=user_id,
                messages=scrape_result.get('messages', []),
            )

            if sync_result['success']:
                db_total = sync_result.get('db_total', len(sync_result.get('messages', [])))
                return {
                    'success': True,
                    'message': sync_result['message'],
                    'data': {
                        'db_total': db_total,
                        'synced': len(scrape_result.get('messages', [])),
                        'new_count': sync_result.get('new_count', 0),
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

    def _get_fernet(self) -> Fernet:
        key = settings.ENCRYPTION_KEY.encode("utf-8")
        derived = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
        return Fernet(derived)

    def _encrypt_app_password(self, app_password: str) -> str:
        fernet = self._get_fernet()
        return fernet.encrypt(app_password.encode("utf-8")).decode("utf-8")

    def _decrypt_app_password(self, encrypted: str) -> str:
        # 兼容旧 JSON 格式 {"password": "..."}
        if encrypted.startswith('{'):
            try:
                data = json.loads(encrypted)
                return data.get('password', '')
            except (json.JSONDecodeError, TypeError):
                pass
        # Fernet 解密
        try:
            fernet = self._get_fernet()
            return fernet.decrypt(encrypted.encode("utf-8")).decode("utf-8")
        except (InvalidToken, Exception):
            return encrypted

    def get_email_messages(self, user_id: str) -> Dict:
        try:
            result = self.email_handle.handle_get_messages(user_id)
            if result.get('success') and result.get('messages'):
                result['messages'] = [
                    {
                        'id': msg.get('message_id', ''),
                        'title': msg.get('subject', ''),
                        'sender': msg.get('sender', ''),
                        'release_time': msg.get('received_at', ''),
                        'context': msg.get('body_text', ''),
                        'raw_html': msg.get('body_html', ''),
                    }
                    for msg in result['messages']
                ]
            return result
        except Exception as e:
            logger.error(f"获取邮件列表失败: {str(e)}")
            return {'success': False, 'message': str(e)}

    def send_email(self, user_id: str, title: str, context: str, receiver: str) -> Dict:
        try:
            account_info = self.email_handle.account_ops.get(user_id)
            if not account_info:
                return {'success': False, 'message': '未绑定邮箱账号，请先绑定'}

            sender = account_info['email_address']
            encrypted_password = account_info.get('encrypted_password', '')
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

    def star_email(self, user_id: str, email_id: int, reason: str | None = None) -> Dict:
        return self.email_handle.handle_star_email(user_id, email_id, reason)

    def unstar_email(self, user_id: str, email_id: int) -> Dict:
        return self.email_handle.handle_unstar_email(user_id, email_id)

    def is_email_starred(self, user_id: str, email_id: int) -> Dict:
        try:
            from local_backend.database.code.operations.database_email_v2_operations import StarredEmailV2Operations
            star_ops = StarredEmailV2Operations()
            result = star_ops.is_starred(user_id, email_id)
            return {'success': True, 'is_starred': result}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def get_starred_emails(self, user_id: str) -> Dict:
        try:
            result = self.email_handle.handle_get_starred_emails(user_id)
            if not result.get('success'):
                return result
            starred = result.get('starred', [])
            msgs_result = self.email_handle.handle_get_messages(user_id)
            msg_map = {}
            if msgs_result.get('success'):
                for m in msgs_result.get('messages', []):
                    msg_map[m.get('message_id')] = m
            enriched = []
            for s in starred:
                msg = msg_map.get(s.get('email_id'))
                if msg:
                    enriched.append({
                        'id': msg.get('message_id'),
                        'title': msg.get('subject', ''),
                        'sender': msg.get('sender', ''),
                        'release_time': msg.get('received_at', ''),
                        'context': msg.get('body_text', ''),
                        'raw_html': msg.get('body_html', ''),
                        'star_reason': s.get('reason', ''),
                        'star_source': s.get('source', 'manual'),
                        'starred_at': s.get('starred_at', ''),
                    })
            return {'success': True, 'messages': enriched}
        except Exception as e:
            logger.error(f"获取星标邮件失败: {str(e)}")
            return {'success': False, 'message': str(e)}

    def delete_email_message(self, user_id: str, message_id: int) -> Dict:
        result = self.email_handle.handle_delete_message(user_id, message_id)
        if result.get('success'):
            from local_backend.database.code.command.database_command import delete_starred_emails_by_email_id
            try:
                delete_starred_emails_by_email_id(message_id)
            except:
                pass
        return result

    def get_trash_messages(self, user_id: str) -> Dict:
        try:
            result = self.email_handle.handle_get_trash(user_id)
            if result.get('success') and result.get('messages'):
                result['messages'] = [
                    {
                        'id': msg.get('message_id', ''),
                        'title': msg.get('subject', ''),
                        'sender': msg.get('sender', ''),
                        'release_time': msg.get('received_at', ''),
                        'context': msg.get('body_text', ''),
                        'raw_html': msg.get('body_html', ''),
                    }
                    for msg in result['messages']
                ]
            return result
        except Exception as e:
            logger.error(f"获取回收站失败: {str(e)}")
            return {'success': False, 'message': str(e)}

    def restore_email_message(self, user_id: str, message_id: int) -> Dict:
        return self.email_handle.handle_restore_message(user_id, message_id)

    def permanent_delete_email(self, user_id: str, message_id: int) -> Dict:
        result = self.email_handle.handle_permanent_delete(user_id, message_id)
        if result.get('success'):
            from local_backend.database.code.command.database_command import delete_starred_emails_by_email_id
            try:
                delete_starred_emails_by_email_id(message_id)
            except:
                pass
        return result

    def empty_trash(self, user_id: str) -> Dict:
        return self.email_handle.handle_empty_trash(user_id)
