import json
import requests
import logging
from typing import Dict, Optional

from service.scraper.tis_scraper import TisScraper
from database.code.handle.database_tis_handle import TisHandle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TisService:
    def __init__(self):
        self.tis_url = "https://tis.sustech.edu.cn"
        self.tis_handle = TisHandle()

    def _create_session_with_cookies(self, cookies_dict: Dict) -> requests.Session:
        session = requests.Session()
        if cookies_dict.get('JSESSIONID'):
            session.cookies.set('JSESSIONID', cookies_dict['JSESSIONID'])
        if cookies_dict.get('route'):
            session.cookies.set('route', cookies_dict['route'])
        if cookies_dict.get('TGC'):
            session.cookies.set('TGC', cookies_dict['TGC'])
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://tis.sustech.edu.cn/",
            "Origin": "https://tis.sustech.edu.cn",
            "Content-Type": "application/json",
        })
        session.timeout = 10
        session.max_redirects = 10
        return session

    def get_tis_status(self, user_id: str) -> Dict:
        try:
            result = self.tis_handle.handle_get_tis_status(user_id)
            if result['success']:
                return {
                    'success': True,
                    'is_bound': result.get('is_bound', False),
                    'student_id': result.get('student_id', ''),
                    'bind_time': result.get('bind_time', ''),
                    'last_sync_time': result.get('last_sync_time', ''),
                }
            else:
                return {'success': False, 'message': result.get('message', '获取状态失败')}
        except Exception as e:
            logger.error(f"获取TIS状态失败: {str(e)}")
            return {'success': False, 'message': f'获取状态失败: {str(e)}'}

    def unbind_tis(self, user_id: str) -> Dict:
        try:
            result = self.tis_handle.handle_unbind_tis(user_id)
            return result
        except Exception as e:
            logger.error(f"TIS解绑失败: {str(e)}")
            return {'success': False, 'message': f'解绑失败: {str(e)}'}

    def bind_with_cookie(self, user_id: str, cookies_str: str) -> Dict:
        try:
            logger.info(f"使用Cookie绑定TIS: user_id={user_id}")

            try:
                cookies_dict = json.loads(cookies_str)
            except json.JSONDecodeError as e:
                logger.error(f"Cookie格式错误: {str(e)}")
                return {'success': False, 'message': 'Cookie格式错误，不是有效的JSON'}

            if not cookies_dict.get('JSESSIONID'):
                return {'success': False, 'message': '缺少必需的Cookie: JSESSIONID'}
            if not cookies_dict.get('TGC'):
                return {'success': False, 'message': '缺少必需的Cookie: TGC'}

            session = self._create_session_with_cookies(cookies_dict)

            scraper = TisScraper(session=session)
            user_info = scraper.get_user_info()

            student_info = None
            if user_info.get("xkxg_xs"):
                student_info = user_info.get("xkxg_xs")
            elif user_info.get("yhdm") or user_info.get("xh"):
                student_info = user_info

            if not student_info:
                logger.error("Cookie无效，无法获取用户信息")
                return {'success': False, 'message': 'Cookie已失效，请重新登录TIS'}

            student_id = student_info.get('xh') or student_info.get('yhdm')
            student_name = student_info.get('xm')

            logger.info(f"TIS绑定成功: user_id={user_id}, 学号={student_id}, 姓名={student_name}")

            try:
                logger.info("开始爬取课程表...")
                schedule_result = scraper.scrape_schedule()
                if schedule_result.get('success'):
                    logger.info(f"课程表爬取成功，共 {schedule_result.get('total_courses', 0)} 门课程")
                    from service.scraper.tis_scraper import OUTPUT_FILE
                    logger.info(f"tis_result.txt 已更新: {OUTPUT_FILE}")

                    sync_result = self.tis_handle.handle_sync_schedule(
                        user_id=user_id,
                        term=schedule_result.get('term', ''),
                        week=schedule_result.get('week', ''),
                        schedule_data=schedule_result.get('schedule', {}),
                    )
                    if sync_result['success']:
                        logger.info(f"课表数据已入库: {sync_result['message']}")
                    else:
                        logger.warning(f"课表入库失败: {sync_result.get('message')}")
                else:
                    logger.warning(f"课程表爬取失败: {schedule_result.get('message')}")
            except Exception as e:
                logger.error(f"爬取或入库课表时发生错误: {str(e)}")
                import traceback
                logger.error(f"错误堆栈: {traceback.format_exc()}")

            encrypted_cookie = self._encrypt_cookie(cookies_dict)
            bind_result = self.tis_handle.handle_bind_tis(
                user_id=user_id,
                student_id=student_id,
                encrypted_cookie=encrypted_cookie,
            )

            if bind_result['success']:
                return {'success': True, 'message': 'TIS账号绑定成功'}
            else:
                return bind_result

        except Exception as e:
            logger.error(f"绑定TIS时发生异常: {str(e)}")
            return {'success': False, 'message': f'绑定TIS时发生异常: {str(e)}'}

    def sync_tis_data(self, user_id: str, week_override: Optional[str] = None) -> Dict:
        try:
            logger.info(f"同步TIS数据: user_id={user_id}")

            account_info = self.tis_handle.account_ops.get_tis_account(user_id)
            if not account_info:
                return {'success': False, 'message': '未绑定TIS账号，请先绑定'}

            encrypted_cookie = account_info.get('content', '')
            cookies_dict = self._decrypt_cookie(encrypted_cookie)

            session = self._create_session_with_cookies(cookies_dict)
            scraper = TisScraper(session=session)
            schedule_result = scraper.scrape_schedule(week_override)

            if schedule_result['success']:
                course_count = schedule_result.get('total_courses', 0)
                week = schedule_result.get('week', '')
                term = schedule_result.get('term', '')
                schedule = schedule_result.get('schedule', {})

                sync_result = self.tis_handle.handle_sync_schedule(
                    user_id=user_id,
                    term=term,
                    week=week,
                    schedule_data=schedule,
                )

                logger.info(f"TIS数据同步成功: 用户={schedule_result.get('user')}, 学期={term}, 周次={week}, 课程数={course_count}")

                return {
                    'success': True,
                    'message': f'同步完成，第{week}周共 {course_count} 门课程',
                    'schedule': schedule,
                    'term': term,
                    'week': week,
                    'total_courses': course_count,
                    'sync_result': sync_result,
                }
            else:
                logger.error(f"TIS数据同步失败: {schedule_result.get('message')}")
                return {'success': False, 'message': schedule_result.get('message', '同步失败')}

        except Exception as e:
            logger.error(f"同步TIS数据失败: {str(e)}")
            return {'success': False, 'message': f'同步TIS数据失败: {str(e)}'}

    def _encrypt_cookie(self, cookies: Dict) -> str:
        return json.dumps(cookies)

    def _decrypt_cookie(self, encrypted_cookie: str) -> Dict:
        try:
            return json.loads(encrypted_cookie)
        except (json.JSONDecodeError, TypeError):
            return {}
