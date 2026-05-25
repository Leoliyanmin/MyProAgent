import json
import requests
import logging
from typing import Dict

from service.scraper.tis_scraper import TisScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TisService:
    def __init__(self):
        self.tis_url = "https://tis.sustech.edu.cn"
        self._bound_users = {}
    
    def get_tis_status(self, user_id: str) -> Dict:
        """获取TIS绑定状态"""
        try:
            from database.code.handle.database_tis_handle import TisHandle
            tis_handle = TisHandle()
            return tis_handle.handle_get_tis_status(user_id)
        except Exception as e:
            logger.error(f"获取TIS状态失败: {str(e)}")
            return {'success': False, 'is_bound': False, 'message': f'获取状态失败: {str(e)}'}
    
    def unbind_tis(self, user_id: str) -> Dict:
        """解绑TIS账号"""
        try:
            if user_id in self._bound_users:
                del self._bound_users[user_id]

            from database.code.handle.database_tis_handle import TisHandle
            from local_backend.database.code.command.database_command import list_events_by_user, delete_event

            tis_handle = TisHandle()
            tis_handle.handle_unbind_tis(user_id)
            old_events = list_events_by_user(user_id, event_type="course", event_source="tis")
            for ev in old_events:
                delete_event(ev["event_id"])

            logger.info(f"TIS解绑成功，已清理数据库: user_id={user_id}")
            return {'success': True, 'message': 'TIS账号解绑成功'}
        except Exception as e:
            logger.error(f"TIS解绑失败: {str(e)}")
            return {'success': False, 'message': f'解绑失败: {str(e)}'}
    
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
            
            logger.info("验证Cookie有效性...")
            try:
                scraper = TisScraper(session=session)
                user_info = scraper.get_user_info()
                
                # 支持两种响应结构
                student_info = None
                if user_info.get("xkxg_xs"):
                    student_info = user_info.get("xkxg_xs")
                elif user_info.get("yhdm") or user_info.get("xh"):
                    student_info = user_info
                
                if not student_info:
                    logger.error("Cookie无效，无法获取用户信息")
                    return {'success': False, 'message': 'Cookie已失效，请重新登录TIS'}
                
                student_id = (student_info.get('xh') or student_info.get('yhdm') or '')
                student_name = student_info.get('xm')
                
                logger.info(f"TIS绑定成功: user_id={user_id}, 学号={student_id}, 姓名={student_name}")
                
                try:
                    logger.info("开始爬取课程表...")
                    schedule_result = scraper.scrape_schedule()
                    if schedule_result.get('success'):
                        logger.info(f"课程表爬取成功，共 {schedule_result.get('total_courses', 0)} 门课程")

                        try:
                            from database.code.handle.database_tis_handle import TisHandle
                            tis_handle = TisHandle()
                            result = tis_handle.save_schedule_v2(user_id, schedule_result)
                            logger.info(f"TIS v2入库: {result}")
                            tis_handle.handle_bind_tis(user_id, student_id, cookies_str)
                            logger.info(f"TIS account记录已保存: user_id={user_id}, 学号={student_id}")
                        except Exception as e:
                            logger.error(f"TIS v2入库失败: {e}")
                    else:
                        logger.warning(f"课程表爬取失败: {schedule_result.get('message')}")
                except Exception as e:
                    logger.error(f"爬取课程表时发生错误: {str(e)}")
                    import traceback
                    logger.error(f"错误堆栈: {traceback.format_exc()}")
                
                # 保存绑定信息
                self._bound_users[user_id] = {
                    'cookies': cookies_str,
                    'user_info': {
                        'student_id': student_id,
                        'name': student_name,
                        'department': student_info.get('bmmc')
                    }
                }
                
                return {
                    'success': True, 
                    'message': 'TIS账号绑定成功'
                }
                
            except Exception as e:
                logger.error(f"TIS绑定失败: {str(e)}")
                return {'success': False, 'message': f'TIS绑定失败: {str(e)}'}
        
        except Exception as e:
            logger.error(f"绑定TIS时发生异常: {str(e)}")
            return {'success': False, 'message': f'绑定TIS时发生异常: {str(e)}'}
