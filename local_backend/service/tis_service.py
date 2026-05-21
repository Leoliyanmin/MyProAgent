import json
import os
import time
import requests
import logging
from typing import Dict

from service.scraper.tis_scraper import TisScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_SAVE_DIR = os.path.join(os.path.expanduser('~'), '.proagent', 'bind_data')
os.makedirs(_SAVE_DIR, exist_ok=True)


class TisService:
    def __init__(self):
        self.tis_url = "https://tis.sustech.edu.cn"
        self._bound_users = {}
    
    def get_tis_status(self, user_id: str) -> Dict:
        """获取TIS绑定状态"""
        try:
            if user_id in self._bound_users:
                bound_info = self._bound_users[user_id]
                return {
                    'success': True,
                    'is_bound': True,
                    'message': '已绑定TIS账号',
                    'user_info': bound_info.get('user_info', {})
                }
            json_path = os.path.join(_SAVE_DIR, f'{user_id}_tis_schedule.json')
            if os.path.exists(json_path):
                import json as _json
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = _json.load(f)
                return {
                    'success': True,
                    'is_bound': True,
                    'message': '已绑定TIS账号（历史数据）',
                    'user_info': {
                        'name': data.get('student_name', ''),
                        'student_id': data.get('student_id', ''),
                        'department': '',
                    }
                }
            return {
                'success': True,
                'is_bound': False,
                'message': '未绑定TIS账号'
            }
        except Exception as e:
            logger.error(f"获取TIS状态失败: {str(e)}")
            return {'success': False, 'message': f'获取状态失败: {str(e)}'}
    
    def unbind_tis(self, user_id: str) -> Dict:
        """解绑TIS账号"""
        try:
            if user_id in self._bound_users:
                del self._bound_users[user_id]
            json_path = os.path.join(_SAVE_DIR, f'{user_id}_tis_schedule.json')
            if os.path.exists(json_path):
                os.remove(json_path)
                logger.info(f"TIS解绑成功，已删除数据文件: user_id={user_id}")
                return {'success': True, 'message': 'TIS账号解绑成功'}
            if user_id not in self._bound_users:
                return {'success': False, 'message': '未绑定TIS账号'}
            logger.info(f"TIS解绑成功: user_id={user_id}")
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
                        
                        json_path = os.path.join(_SAVE_DIR, f'{user_id}_tis_schedule.json')
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump({
                                'user_id': user_id,
                                'bind_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'student_id': student_id,
                                'student_name': student_name,
                                'schedule': schedule_result.get('schedule', {}),
                                'term': schedule_result.get('term', ''),
                                'week': schedule_result.get('week', ''),
                                'total_courses': schedule_result.get('total_courses', 0)
                            }, f, ensure_ascii=False, indent=2)
                        logger.info(f"TIS课程数据已保存到: {json_path}")

                        try:
                            from database.code.handle.database_tis_handle import TisHandle
                            tis_handle = TisHandle()
                            result = tis_handle.save_schedule_v2(user_id, schedule_result)
                            logger.info(f"TIS v2入库: {result}")
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
