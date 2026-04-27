import json
import requests
import logging
from typing import Dict, Optional

from service.scraper.tis_scraper import TisScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TisService:
    """TIS教务系统业务服务"""
    
    def __init__(self):
        self.tis_url = "https://tis.sustech.edu.cn"
        # 临时存储绑定状态（实际应用中应使用数据库）
        self._bound_users = {}  # user_id -> {'cookies': ..., 'user_info': ...}
    
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
            else:
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
                logger.info(f"TIS解绑成功: user_id={user_id}")
                return {'success': True, 'message': 'TIS账号解绑成功'}
            else:
                return {'success': False, 'message': '未绑定TIS账号'}
        except Exception as e:
            logger.error(f"TIS解绑失败: {str(e)}")
            return {'success': False, 'message': f'解绑失败: {str(e)}'}
    
    def _create_session_with_cookies(self, cookies_dict: Dict) -> requests.Session:
        """创建带有Cookie的Session
        
        使用session.cookies.set设置Cookie，确保正确处理跨域Cookie。
        
        Args:
            cookies_dict: Cookie字典（使用JSESSIONID、route和TGC）
        
        Returns:
            配置好的Session对象
        """
        session = requests.Session()
        
        # 设置Cookie：JSESSIONID、route 和 TGC
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
        """使用Cookie绑定TIS账号
        
        通过Tauri等方式获取TIS的Cookie后，传递给后端完成绑定。
        
        Args:
            user_id: 用户ID
            cookies_str: TIS的Cookie字符串（JSON格式）
        
        Returns:
            包含success和message的字典
        """
        try:
            logger.info(f"使用Cookie绑定TIS: user_id={user_id}")
            
            try:
                cookies_dict = json.loads(cookies_str)
            except json.JSONDecodeError as e:
                logger.error(f"Cookie格式错误，不是有效的JSON: {str(e)}")
                return {'success': False, 'message': 'Cookie格式错误，不是有效的JSON'}
            
            logger.info(f"解析到的Cookie数量: {len(cookies_dict)} 个")
            logger.info(f"Cookie键: {list(cookies_dict.keys())}")
            
            # 验证必需的Cookie
            if not cookies_dict.get('JSESSIONID'):
                logger.error("缺少必需的Cookie: JSESSIONID")
                return {'success': False, 'message': '缺少必需的Cookie: JSESSIONID'}
            if not cookies_dict.get('TGC'):
                logger.error("缺少必需的Cookie: TGC")
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
                '''
                # ============ 测试爬取指定URL ============
                try:
                    # 测试爬取指定URL（可在后端修改此URL）
                    test_url = "https://tis.sustech.edu.cn/Xskbcx/queryXskbcxList"
                    logger.info(f"开始测试爬取URL: {test_url}")
                    test_result = scraper.test_fetch_url(test_url, "POST")
                    if test_result.get('success'):
                        logger.info(f"URL爬取成功，状态码: {test_result.get('status_code')}")
                        logger.info(f"响应内容预览: {str(test_result.get('content'))[:300]}")
                    else:
                        logger.warning(f"URL爬取失败: {test_result.get('error')}")
                except Exception as e:
                    logger.error(f"测试爬取URL时发生错误: {str(e)}")
                    import traceback
                    logger.error(f"错误堆栈: {traceback.format_exc()}")
                # ============ 测试爬取指定URL结束 ============
                '''
                # 生成tis_result.txt
                try:
                    logger.info("开始爬取课程表...")
                    schedule_result = scraper.scrape_schedule()
                    if schedule_result.get('success'):
                        logger.info(f"课程表爬取成功，共 {schedule_result.get('total_courses', 0)} 门课程")
                        from service.scraper.tis_scraper import OUTPUT_FILE
                        logger.info(f"tis_result.txt 已更新: {OUTPUT_FILE}")
                    else:
                        logger.warning(f"课程表爬取失败: {schedule_result.get('message')}")
                except Exception as e:
                    logger.error(f"生成tis_result.txt时发生错误: {str(e)}")
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
    
    def sync_tis_data(self, user_id: str, week_override: Optional[str] = None) -> Dict:
        """同步TIS数据
        
        Args:
            user_id: 用户ID
            week_override: 可选的周次覆盖参数
        
        Returns:
            包含同步结果的字典
        """
        try:
            logger.info(f"同步TIS数据: user_id={user_id}")
            
            # 检查是否已绑定
            if user_id not in self._bound_users:
                return {'success': False, 'message': '未绑定TIS账号，请先绑定'}
            
            # 从绑定信息中获取cookies
            cookies_str = self._bound_users[user_id].get('cookies', '')
            if not cookies_str:
                return {'success': False, 'message': '绑定信息中没有Cookie'}
            
            try:
                cookies_dict = json.loads(cookies_str)
            except json.JSONDecodeError as e:
                logger.error(f"Cookie格式错误: {str(e)}")
                return {'success': False, 'message': 'Cookie格式错误'}
            
            session = self._create_session_with_cookies(cookies_dict)
            
            scraper = TisScraper(session=session)
            schedule_result = scraper.scrape_schedule(week_override)
            
            if schedule_result['success']:
                course_count = schedule_result.get('total_courses', 0)
                week = schedule_result.get('week', '')
                
                logger.info(f"TIS数据同步成功: 用户={schedule_result.get('user')}, 学期={schedule_result.get('term')}, 周次={week}, 课程数={course_count}")
                
                return {
                    'success': True,
                    'message': f'同步完成，第{week}周共 {course_count} 门课程',
                    'schedule': schedule_result.get('schedule', {}),
                    'term': schedule_result.get('term', ''),
                    'week': week,
                    'total_courses': course_count
                }
            else:
                logger.error(f"TIS数据同步失败: {schedule_result.get('message')}")
                return {'success': False, 'message': schedule_result.get('message', '同步失败')}
        
        except Exception as e:
            logger.error(f"同步TIS数据失败: {str(e)}")
            return {'success': False, 'message': f'同步TIS数据失败: {str(e)}'}
    

