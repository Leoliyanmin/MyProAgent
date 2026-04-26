import json
import requests
import logging
from typing import Dict, Optional

from service.scraper.blackboard_scraper import BlackboardScraper
from database.code.handle.database_blackboard_handle import BlackboardHandle

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BB_SSO_URL = "https://bb.sustech.edu.cn/webapps/bb-sso-BBLEARN/index.jsp"

class BlackboardService:
    """Blackboard业务服务"""
    
    def __init__(self):
        self.blackboard_url = "https://bb.sustech.edu.cn"
        self.blackboard_handle = BlackboardHandle()
    
    def _create_session_with_cookies(self, cookies_dict: Dict) -> requests.Session:
        """创建带有Cookie的Session
        
        使用直接在Header中设置Cookie的方式，避免CookieJar处理问题。
        
        Args:
            cookies_dict: Cookie字典
        
        Returns:
            配置好的Session对象
        """
        session = requests.Session()
        
        # 构建Cookie字符串
        cookie_string = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
        
        # 设置请求头，包括直接在Header中设置Cookie
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://bb.sustech.edu.cn/",
            "Origin": "https://bb.sustech.edu.cn",
            "Cookie": cookie_string  # 直接在Header中设置Cookie，避免CookieJar处理问题
        })
        
        session.timeout = 10
        
        return session
    
    def bind_with_cookie(self, user_id: str, cookies_str: str) -> Dict:
        """使用Cookie绑定Blackboard账号
        
        通过Tauri等方式获取Blackboard的Cookie后，传递给后端完成绑定。
        
        Args:
            user_id: 用户ID
            cookies_str: Blackboard的Cookie字符串（JSON格式）
        
        Returns:
            包含success和message的字典
        """
        try:
            logger.info(f"使用Cookie绑定: user_id={user_id}")
            
            # 解析Cookie字符串
            try:
                cookies_dict = json.loads(cookies_str)
            except json.JSONDecodeError as e:
                logger.error(f"Cookie格式错误，不是有效的JSON: {str(e)}")
                return {'success': False, 'message': 'Cookie格式错误，不是有效的JSON'}
            
            logger.info(f"解析到的Cookie数量: {len(cookies_dict)} 个")
            logger.info(f"Cookie键: {list(cookies_dict.keys())}")
            
            # 验证必需的Cookie（JSESSIONID和s_session_id都是必需的）
            required_cookies = ['JSESSIONID', 's_session_id']
            missing_required = [c for c in required_cookies if c not in cookies_dict]
            
            if missing_required:
                logger.error(f"Cookie中缺少必需的字段: {missing_required}")
                return {'success': False, 'message': f'Cookie中缺少必需的字段: {", ".join(missing_required)}'}
            
            # 可选Cookie列表
            optional_cookies = ['BBSESSION', 'COOKIE_CONSENT_ACCEPTED', '_ga', '_ga_0KD226TRZ5', 
                               'CdnSignedValidation', 'BbClientCalenderTimeZone', 
                               'BbClientDownloadExecuting', 'web_client_cache_guid']
            
            # 记录可选Cookie的缺失情况
            missing_optional = [c for c in optional_cookies if c not in cookies_dict]
            if missing_optional:
                logger.info(f"缺少可选Cookie: {missing_optional}")
            
            # 创建Session并设置Cookie（使用改进的方法）
            session = self._create_session_with_cookies(cookies_dict)
            
            logger.info(f"成功设置 {len(cookies_dict)} 个Cookie到Session")
            logger.info(f"Cookie详情: {[(k, v[:20] + '...' if len(v) > 20 else v) for k, v in cookies_dict.items()]}")
            
            # 验证Cookie有效性
            logger.info("验证Cookie有效性...")
            test_response = session.get(self.blackboard_url, allow_redirects=True)
            logger.info(f"验证响应状态码: {test_response.status_code}")
            logger.info(f"验证后URL: {test_response.url}")
            
            # 检查是否被重定向到CAS登录页
            if 'cas.sustech.edu.cn' in test_response.url:
                logger.error("Cookie无效，被重定向到CAS登录页")
                return {'success': False, 'message': 'Cookie已失效，请重新登录Blackboard'}
            
            # 爬取课程数据
            logger.info("爬取Blackboard课程数据...")
            scraper = BlackboardScraper(session=session)
            scrape_result = scraper.scrape_courses()
            
            # 同步数据到数据库
            if scrape_result['success']:
                courses_data = []
                for course in scrape_result['courses']:
                    course_data = {
                        'id': course.get('id', ''),
                        'name': course.get('name', ''),
                        'link': course.get('url', ''),
                        'assignments': []
                    }
                    for assignment in course.get('assignments', []):
                        course_data['assignments'].append({
                            'id': assignment.get('id', ''),
                            'name': assignment.get('title', ''),
                            'link': assignment.get('url', ''),
                            'due_date': assignment.get('due_date', ''),
                            'status': assignment.get('status', '未提交')
                        })
                    courses_data.append(course_data)
                
                sync_result = self.blackboard_handle.handle_full_sync(
                    user_id=user_id,
                    sync_data={'courses': courses_data}
                )
                
                total_announcements = sum(len(course.get('announcements', [])) for course in scrape_result.get('courses', []))
                total_course_materials = sum(len(course.get('course_materials', [])) for course in scrape_result.get('courses', []))
                total_upload_assignments = sum(len(course.get('upload_assignments', [])) for course in scrape_result.get('courses', []))
                course_names = [course.get('name', '') for course in scrape_result.get('courses', [])]
                
                logger.info(f"数据同步结果: 课程数={len(course_names)}, 公告数={total_announcements}, 课程资料数={total_course_materials}, 作业数={total_upload_assignments}, 课程名={course_names}")
            
            # 存储账号信息
            username = user_id.split('@')[0] if '@' in user_id else user_id
            encrypted_cookie = self.encrypt_cookie(cookies_dict)
            
            bind_result = self.blackboard_handle.handle_bind_blackboard(
                user_id=user_id,
                username=username,
                encrypted_cookie=encrypted_cookie
            )
            
            if bind_result['success']:
                logger.info("绑定成功")
                return {'success': True, 'message': 'Blackboard账号绑定成功'}
            else:
                return {'success': False, 'message': f"账号存储失败: {bind_result.get('message', '未知错误')}"}
            
        except Exception as e:
            logger.error(f"使用Cookie绑定失败: {str(e)}")
            return {'success': False, 'message': f'绑定失败: {str(e)}'}
    
    def sync_blackboard_data(self, user_id: str) -> Dict:
        """同步Blackboard数据"""
        try:
            logger.info(f"同步Blackboard数据: user_id={user_id}")
            
            # 获取存储的Cookie（从AccountOperations直接获取）
            account_info = self.blackboard_handle.account_ops.get_blackboard_account(user_id)
            if not account_info or not account_info.get('account_encrypted_cookie'):
                return {'success': False, 'message': '未找到绑定的Blackboard账号'}
            
            # 解密Cookie
            cookies_dict = self.decrypt_cookie(account_info['account_encrypted_cookie'])
            
            # 创建session并设置Cookie（使用改进的方法）
            session = self._create_session_with_cookies(cookies_dict)
            
            # 爬取课程数据
            scraper = BlackboardScraper(session=session)
            scrape_result = scraper.scrape_courses()
            
            if scrape_result['success']:
                courses_data = []
                for course in scrape_result['courses']:
                    course_data = {
                        'id': course.get('id', ''),
                        'name': course.get('name', ''),
                        'link': course.get('url', ''),
                        'assignments': []
                    }
                    for assignment in course.get('assignments', []):
                        course_data['assignments'].append({
                            'id': assignment.get('id', ''),
                            'name': assignment.get('title', ''),
                            'link': assignment.get('url', ''),
                            'due_date': assignment.get('due_date', ''),
                            'status': assignment.get('status', '未提交')
                        })
                    courses_data.append(course_data)
                
                sync_result = self.blackboard_handle.handle_full_sync(
                    user_id=user_id,
                    sync_data={'courses': courses_data}
                )
                
                return {'success': True, 'message': '同步成功', 'data': sync_result}
            else:
                return {'success': False, 'message': scrape_result.get('message', '爬取失败')}
        
        except Exception as e:
            logger.error(f"同步Blackboard数据失败: {str(e)}")
            return {'success': False, 'message': f'同步失败: {str(e)}'}
    
    def get_blackboard_status(self, user_id: str) -> Dict:
        """获取Blackboard绑定状态"""
        try:
            # 使用正确的方法名 handle_get_blackboard_status
            result = self.blackboard_handle.handle_get_blackboard_status(user_id)
            
            if result['success']:
                return {
                    'success': True,
                    'is_bound': result.get('is_bound', False),
                    'username': result.get('username', ''),
                    'bind_time': result.get('bind_time', ''),
                    'last_sync_time': result.get('last_sync_time', '')
                }
            else:
                return {'success': False, 'message': result.get('message', '获取状态失败')}
        
        except Exception as e:
            logger.error(f"获取Blackboard状态失败: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def unbind_blackboard(self, user_id: str) -> Dict:
        """解绑Blackboard账号"""
        try:
            result = self.blackboard_handle.handle_unbind_blackboard(user_id)
            return result
        except Exception as e:
            logger.error(f"解绑Blackboard失败: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def encrypt_cookie(self, cookies: Dict) -> str:
        """加密Cookie"""
        return json.dumps(cookies)
    
    def decrypt_cookie(self, encrypted_cookie: str) -> Dict:
        """解密Cookie"""
        try:
            return json.loads(encrypted_cookie)
        except json.JSONDecodeError:
            logger.error("Cookie解密失败")
            return {}
    
