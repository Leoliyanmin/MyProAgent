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
    
    def bind_with_cookie(self, user_id: str, cookies_str: str, ics_url: str | None = None) -> Dict:
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

            # Fetch ICS calendar feed for accurate due dates (one HTTP, all courses)
            ics_dates = {}
            if ics_url:
                try:
                    logger.info(f"获取 ICS 日历: {ics_url}")
                    ics_resp = session.get(ics_url, allow_redirects=True, timeout=30)
                    if ics_resp.status_code == 200 and 'BEGIN:VCALENDAR' in ics_resp.text:
                        import re
                        for block in ics_resp.text.split('BEGIN:VEVENT')[1:]:
                            m_dt = re.search(r'DTSTART(?:;TZID=[^:]+)?:(\d{8})T(\d{6})', block)
                            m_sum = re.search(r'SUMMARY:(.+)', block)
                            if m_dt and m_sum:
                                dt = f"{m_dt.group(1)[:4]}-{m_dt.group(1)[4:6]}-{m_dt.group(1)[6:8]} {m_dt.group(2)[:2]}:{m_dt.group(2)[2:4]}"
                                ics_dates[m_sum.group(1).strip().lower()] = dt
                        logger.info(f"ICS 解析到 {len(ics_dates)} 个截止日期")
                    else:
                        logger.warning(f"ICS 获取失败: HTTP {ics_resp.status_code}")
                except Exception as e:
                    logger.warning(f"ICS 获取异常: {e}")
            
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
                        label = assignment.get('label', '')
                        due = assignment.get('due_date', '')
                        if not due and ics_dates:
                            due = ics_dates.get(label.lower(), '')
                        course_data['assignments'].append({
                            'id': label,
                            'name': label,
                            'link': assignment.get('url', ''),
                            'due_date': due,
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

                try:
                    from database.code.handle.database_bb_v2_handle import BbV2Handle
                    bb_handle = BbV2Handle()
                    result = bb_handle.save_courses(user_id, courses_data)
                    logger.info(f"BB v2入库: {result}")
                except Exception as e:
                    logger.error(f"BB v2入库失败: {e}")
                
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
    
    def bind_with_ics(self, user_id: str, ics_url: str) -> Dict:
        """使用 BB 日历 ICS 链接直接绑定，无需 CAS 登录和 Cookie"""
        import re
        try:
            logger.info(f"使用 ICS 绑定 Blackboard: user_id={user_id}")
            resp = requests.get(ics_url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0"
            })
            if resp.status_code != 200 or 'BEGIN:VCALENDAR' not in resp.text:
                return {'success': False, 'message': f'ICS 获取失败: HTTP {resp.status_code}'}

            ics_events = []
            for block in resp.text.split('BEGIN:VEVENT')[1:]:
                m_dt = re.search(r'DTSTART(?:;TZID=[^:]+)?:(\d{8})T(\d{6})', block)
                m_sum = re.search(r'SUMMARY:(.+)', block)
                m_uid = re.search(r'UID:(.+)', block)
                if m_dt and m_sum:
                    due = f"{m_dt.group(1)[:4]}-{m_dt.group(1)[4:6]}-{m_dt.group(1)[6:8]} {m_dt.group(2)[:2]}:{m_dt.group(2)[2:4]}"
                    ics_events.append({
                        'label': m_sum.group(1).strip(),
                        'due_date': due,
                        'uid': m_uid.group(1).strip() if m_uid else '',
                    })
            if not ics_events:
                return {'success': False, 'message': 'ICS 中没有找到任何事件'}

            logger.info(f"ICS 解析到 {len(ics_events)} 个事件")

            courses_data = [{
                'id': 'ics',
                'name': 'Blackboard',
                'link': 'https://bb.sustech.edu.cn',
                'assignments': [{
                    'id': e['label'],
                    'name': e['label'],
                    'link': '',
                    'due_date': e['due_date'],
                    'content': [],
                } for e in ics_events],
                'announcements': [],
                'course_materials': [],
            }]

            json_path = os.path.join(_SAVE_DIR, f'{user_id}_blackboard_courses.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'user_id': user_id,
                    'bind_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'courses': courses_data,
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"Blackboard ICS 数据已保存: {json_path}")

            try:
                from database.code.handle.database_bb_v2_handle import BbV2Handle
                bb_handle = BbV2Handle()
                result = bb_handle.save_courses(user_id, courses_data)
                logger.info(f"BB v2入库: {result}")
            except Exception as e:
                logger.error(f"BB v2入库失败: {e}")

            return {
                'success': True,
                'message': f'Blackboard 绑定成功，{len(ics_events)} 个事件',
            }
        except Exception as e:
            logger.error(f"ICS 绑定失败: {e}")
            return {'success': False, 'message': f'绑定失败: {e}'}

    def get_bb_assignments(self, user_id: str) -> Dict:
        return {"success": True, "message": "use /api/v1/blackboard/assignments instead", "assignments": []}

    def get_bb_announcements(self, user_id: str) -> Dict:
        return {"success": True, "message": "use /api/v1/blackboard/status instead", "announcements": []}

    def get_bb_course_materials(self, user_id: str) -> Dict:
        return {"success": True, "message": "use /api/v1/blackboard/status instead", "course_materials": []}
