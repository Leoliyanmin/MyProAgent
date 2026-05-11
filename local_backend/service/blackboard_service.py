import json
import os
import time
import requests
import logging
from typing import Dict, Optional

from service.scraper.blackboard_scraper import BlackboardScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BB_SSO_URL = "https://bb.sustech.edu.cn/webapps/bb-sso-BBLEARN/index.jsp"

_SAVE_DIR = os.path.join(os.path.expanduser('~'), '.proagent', 'bind_data')
os.makedirs(_SAVE_DIR, exist_ok=True)


class BlackboardService:
    """Blackboard业务服务"""
    
    def __init__(self):
        self.blackboard_url = "https://bb.sustech.edu.cn"
        self._bound_users = {}
    
    def _create_session_with_cookies(self, cookies_dict: Dict) -> requests.Session:
        session = requests.Session()
        
        cookie_string = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
        
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://bb.sustech.edu.cn/",
            "Origin": "https://bb.sustech.edu.cn",
            "Cookie": cookie_string
        })
        
        session.timeout = 10
        
        return session
    
    def bind_with_cookie(self, user_id: str, cookies_str: str) -> Dict:
        try:
            logger.info(f"使用Cookie绑定: user_id={user_id}")
            
            try:
                cookies_dict = json.loads(cookies_str)
            except json.JSONDecodeError as e:
                logger.error(f"Cookie格式错误，不是有效的JSON: {str(e)}")
                return {'success': False, 'message': 'Cookie格式错误，不是有效的JSON'}
            
            logger.info(f"解析到的Cookie数量: {len(cookies_dict)} 个")
            logger.info(f"Cookie键: {list(cookies_dict.keys())}")
            
            required_cookies = ['JSESSIONID', 's_session_id']
            missing_required = [c for c in required_cookies if c not in cookies_dict]
            
            if missing_required:
                logger.error(f"Cookie中缺少必需的字段: {missing_required}")
                return {'success': False, 'message': f'Cookie中缺少必需的字段: {", ".join(missing_required)}'}
            
            session = self._create_session_with_cookies(cookies_dict)
            
            logger.info(f"成功设置 {len(cookies_dict)} 个Cookie到Session")
            logger.info(f"Cookie详情: {[(k, v[:20] + '...' if len(v) > 20 else v) for k, v in cookies_dict.items()]}")
            
            logger.info("验证Cookie有效性...")
            test_response = session.get(self.blackboard_url, allow_redirects=True)
            logger.info(f"验证响应状态码: {test_response.status_code}")
            logger.info(f"验证后URL: {test_response.url}")
            
            if 'cas.sustech.edu.cn' in test_response.url:
                logger.error("Cookie无效，被重定向到CAS登录页")
                return {'success': False, 'message': 'Cookie已失效，请重新登录Blackboard'}
            
            logger.info("爬取Blackboard课程数据...")
            scraper = BlackboardScraper(session=session)
            scrape_result = scraper.scrape_courses()
            
            if scrape_result['success']:
                courses_data = []
                for course in scrape_result['courses']:
                    course_data = {
                        'id': course.get('id', ''),
                        'name': course.get('name', ''),
                        'link': course.get('url', ''),
                        'assignments': [],
                        'announcements': [],
                        'course_materials': []
                    }
                    for assignment in course.get('upload_assignments', []):
                        course_data['assignments'].append({
                            'id': assignment.get('label', ''),
                            'name': assignment.get('label', ''),
                            'link': assignment.get('url', ''),
                            'due_date': assignment.get('due_date', ''),
                            'content': assignment.get('content_blocks', [])
                        })
                    for announcement in course.get('announcements', []):
                        course_data['announcements'].append({
                            'id': announcement.get('id', '') or announcement.get('label', ''),
                            'title': announcement.get('title', '') or announcement.get('label', ''),
                            'url': announcement.get('url', ''),
                            'date': announcement.get('posted_date', '') or announcement.get('posted_on', '') or announcement.get('date', ''),
                            'content': announcement.get('body_text', '') or announcement.get('content', '') or announcement.get('content_blocks', '')
                        })
                    for material in course.get('course_materials', []):
                        course_data['course_materials'].append({
                            'id': material.get('id', '') or material.get('label', ''),
                            'title': material.get('title', '') or material.get('label', ''),
                            'url': material.get('url', ''),
                            'date': material.get('date', ''),
                            'content': material.get('content', '') or material.get('content_blocks', '')
                        })
                    courses_data.append(course_data)
                
                json_path = os.path.join(_SAVE_DIR, f'{user_id}_blackboard_courses.json')
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'user_id': user_id,
                        'bind_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'courses': courses_data
                    }, f, ensure_ascii=False, indent=2)
                logger.info(f"Blackboard课程数据已保存到: {json_path}")
                
                course_names = [c.get('name', '') for c in courses_data]
                total_assignments = sum(len(c.get('assignments', [])) for c in courses_data)
                total_announcements = sum(len(c.get('announcements', [])) for c in courses_data)
                total_materials = sum(len(c.get('course_materials', [])) for c in courses_data)
                logger.info(f"爬取结果: 课程数={len(courses_data)}, 作业数={total_assignments}, 公告数={total_announcements}, 课程资料数={total_materials}, 课程名={course_names}")
            
            self._bound_users[user_id] = {
                'cookies': cookies_str,
                'bind_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'courses_count': len(scrape_result.get('courses', []))
            }
            
            return {
                'success': True,
                'message': f"Blackboard账号绑定成功，爬取到 {len(scrape_result.get('courses', []))} 门课程"
            }
            
        except Exception as e:
            logger.error(f"使用Cookie绑定失败: {str(e)}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return {'success': False, 'message': f'绑定失败: {str(e)}'}
    
    def sync_blackboard_data(self, user_id: str) -> Dict:
        try:
            logger.info(f"同步Blackboard数据: user_id={user_id}")
            
            if user_id not in self._bound_users:
                return {'success': False, 'message': '未绑定Blackboard账号，请先绑定'}
            
            cookies_str = self._bound_users[user_id].get('cookies', '')
            if not cookies_str:
                return {'success': False, 'message': '绑定信息中没有Cookie'}
            
            try:
                cookies_dict = json.loads(cookies_str)
            except json.JSONDecodeError:
                return {'success': False, 'message': 'Cookie格式错误'}
            
            session = self._create_session_with_cookies(cookies_dict)
            scraper = BlackboardScraper(session=session)
            scrape_result = scraper.scrape_courses()
            
            if scrape_result['success']:
                json_path = os.path.join(_SAVE_DIR, f'{user_id}_blackboard_sync.json')
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'user_id': user_id,
                        'sync_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'courses': scrape_result.get('courses', [])
                    }, f, ensure_ascii=False, indent=2)
                
                return {
                    'success': True,
                    'message': f"同步成功，共 {len(scrape_result.get('courses', []))} 门课程",
                    'data': scrape_result
                }
            else:
                return {'success': False, 'message': scrape_result.get('message', '爬取失败')}
        
        except Exception as e:
            logger.error(f"同步Blackboard数据失败: {str(e)}")
            return {'success': False, 'message': f'同步失败: {str(e)}'}
    
    def get_blackboard_status(self, user_id: str) -> Dict:
        try:
            if user_id in self._bound_users:
                bound_info = self._bound_users[user_id]
                return {
                    'success': True,
                    'is_bound': True,
                    'username': user_id.split('@')[0] if '@' in user_id else user_id,
                    'bind_time': bound_info.get('bind_time', ''),
                    'last_sync_time': ''
                }
            json_path = os.path.join(_SAVE_DIR, f'{user_id}_blackboard_courses.json')
            if os.path.exists(json_path):
                import json as _json
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = _json.load(f)
                return {
                    'success': True,
                    'is_bound': True,
                    'username': user_id.split('@')[0] if '@' in user_id else user_id,
                    'bind_time': data.get('bind_time', ''),
                    'last_sync_time': '',
                    'courses_count': len(data.get('courses', [])),
                }
            return {'success': True, 'is_bound': False, 'message': '未绑定Blackboard账号'}
        except Exception as e:
            logger.error(f"获取Blackboard状态失败: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def unbind_blackboard(self, user_id: str) -> Dict:
        try:
            if user_id in self._bound_users:
                del self._bound_users[user_id]
            json_path = os.path.join(_SAVE_DIR, f'{user_id}_blackboard_courses.json')
            if os.path.exists(json_path):
                os.remove(json_path)
                sync_path = os.path.join(_SAVE_DIR, f'{user_id}_blackboard_sync.json')
                if os.path.exists(sync_path):
                    os.remove(sync_path)
                logger.info(f"Blackboard解绑成功，已删除数据文件: user_id={user_id}")
                return {'success': True, 'message': 'Blackboard账号解绑成功'}
            if user_id not in self._bound_users:
                return {'success': False, 'message': '未绑定Blackboard账号'}
            logger.info(f"Blackboard解绑成功: user_id={user_id}")
            return {'success': True, 'message': 'Blackboard账号解绑成功'}
        except Exception as e:
            logger.error(f"解绑Blackboard失败: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def encrypt_cookie(self, cookies: Dict) -> str:
        return json.dumps(cookies)
    
    def decrypt_cookie(self, encrypted_cookie: str) -> Dict:
        try:
            return json.loads(encrypted_cookie)
        except json.JSONDecodeError:
            logger.error("Cookie解密失败")
            return {}
    
    def get_bb_assignments(self, user_id: str) -> Dict:
        """获取同步的作业列表（含 due_date）"""
        try:
            result = self.blackboard_handle.handle_get_assignments(user_id)
            return result
        except Exception as e:
            logger.error(f"获取作业失败: {str(e)}")
            return {'success': False, 'message': str(e)}

    def get_bb_announcements(self, user_id: str) -> Dict:
        """获取同步的公告列表"""
        try:
            result = self.blackboard_handle.handle_get_announcements(user_id)
            return result
        except Exception as e:
            logger.error(f"获取公告失败: {str(e)}")
            return {'success': False, 'message': str(e)}

    def get_bb_course_materials(self, user_id: str) -> Dict:
        """获取同步的课程资料列表"""
        try:
            result = self.blackboard_handle.handle_get_course_materials(user_id)
            return result
        except Exception as e:
            logger.error(f"获取课程资料失败: {str(e)}")
            return {'success': False, 'message': str(e)}
