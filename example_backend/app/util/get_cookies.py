#!/usr/bin/env python3
"""
获取BB和TIS登录后的cookies脚本
通过CAS单点登录获取各系统的完整cookies
"""

import requests
import json
import sys
import os
from typing import Dict, Any, Optional
from urllib3.exceptions import InsecureRequestWarning
import warnings

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from core.config import SERVICES, UA, CAS_LOGIN_URL
except ImportError:
    # 如果无法导入，使用默认配置
    SERVICES = {
        'cas': 'https://cas.sustech.edu.cn/cas/login',
        'bb': 'https://bb.sustech.edu.cn',
        'tis': 'https://tis.sustech.edu.cn'
    }
    UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    CAS_LOGIN_URL = 'https://cas.sustech.edu.cn/cas/login'

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

class CookieExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"user-agent": UA})
        self.cas_cookies = {}
        self.service_cookies = {}
    
    def cas_login(self, sid: str, password: str, service_url: str) -> Dict[str, str]:
        """CAS登录并获取TGT Cookie"""
        
        try:
            # 获取登录页面和execution token
            login_page = self.session.get(CAS_LOGIN_URL, params={"service": service_url}, verify=False)
            
            if login_page.status_code != 200:
                raise Exception(f"CAS服务不可用: {login_page.status_code}")
            
            # 解析execution token
            execution_token = ""
            if 'name="execution"' in login_page.text:
                execution_token = login_page.text.split('name="execution" value="')[1].split('"')[0]
            
            # 准备登录数据
            login_data = {
                'username': sid,
                'password': password,
                'execution': execution_token,
                '_eventId': 'submit',
                'geolocation': ''
            }

            # 提交登录请求
            login_response = self.session.post(
                CAS_LOGIN_URL,
                data=login_data,
                allow_redirects=False,
                verify=False
            )

            if login_response.status_code != 302 or "Location" not in login_response.headers:
                raise Exception("用户名或密码错误")
            
            # 保存CAS cookies
            self.cas_cookies = self.session.cookies.get_dict()
            return self.cas_cookies
        
        except Exception as e:
            raise
    
    def get_service_ticket(self, service_url: str) -> str:
        """获取特定服务的ST票据"""
        try:
            # 请求服务票据
            response = self.session.get(
                CAS_LOGIN_URL,
                params={"service": service_url},
                allow_redirects=False,
                verify=False
            )

            if response.status_code != 302 or "Location" not in response.headers:
                raise Exception("获取服务票据失败")
            
            # 从重定向URL中提取票据
            location = response.headers["Location"]
            if "ticket=" not in location:
                raise Exception("票据未找到")
            
            ticket = location.split("ticket=")[1].split("&")[0]
            return ticket
        
        except Exception as e:
            raise
    
    def get_bb_cookies(self, ticket: str) -> Dict[str, str]:
        """获取BB系统的cookies"""
        
        try:
            # 使用票据访问BB系统
            bb_url = f"{SERVICES['bb']}?ticket={ticket}"
            response = self.session.get(bb_url, allow_redirects=True, verify=False)
            
            if response.status_code != 200:
                raise Exception(f"BB系统访问失败: {response.status_code}")
            
            # 获取BB系统的cookies
            bb_cookies = {}
            for cookie in self.session.cookies:
                if 'bb.sustech.edu.cn' in cookie.domain or 'blackboard' in cookie.name.lower():
                    bb_cookies[cookie.name] = cookie.value
            
            return bb_cookies
        
        except Exception as e:
            return {}
    
    def get_tis_cookies(self, ticket: str) -> Dict[str, str]:
        """获取TIS系统的cookies"""
        
        try:
            # 使用票据访问TIS系统
            tis_url = f"{SERVICES['tis']}?ticket={ticket}"
            response = self.session.get(tis_url, allow_redirects=True, verify=False)
            
            if response.status_code != 200:
                raise Exception(f"TIS系统访问失败: {response.status_code}")
            
            # 获取TIS系统的cookies
            tis_cookies = {}
            for cookie in self.session.cookies:
                if 'tis.sustech.edu.cn' in cookie.domain or 'tis' in cookie.name.lower():
                    tis_cookies[cookie.name] = cookie.value
            
            return tis_cookies
        
        except Exception as e:
            return {}
    
    def validate_cookies(self, service: str, cookies: Dict[str, str]) -> bool:
        """验证cookies是否有效"""
        if not cookies:
            return False
        
        try:
            if service == "bb":
                # 尝试访问BB的受保护页面
                test_url = "https://bb.sustech.edu.cn/webapps/portal/execute/tabs/tabAction"
                response = self.session.get(test_url, verify=False)
                return response.status_code == 200 and "login" not in response.url.lower()
            
            elif service == "tis":
                # 尝试访问TIS的受保护页面
                test_url = "https://tis.sustech.edu.cn/Xskbcx/queryXskbcxList"
                response = self.session.get(test_url, verify=False)
                return response.status_code == 200 and "login" not in response.url.lower()
            
        except Exception as e:
            return False
        
        return False
    
    def extract_all_cookies(self, sid: str, password: str) -> Dict[str, Any]:
        
        results = {
            "sid": sid,
            "cas_cookies": {},
            "services": {}
        }
        
        try:
            # 1. CAS登录
            initial_service = SERVICES["bb"]  # 使用BB作为初始服务
            self.cas_login(sid, password, initial_service)
            results["cas_cookies"] = self.cas_cookies
            
            # 2. 获取各服务的cookies
            for service_name, service_url in SERVICES.items():
                
                try:
                    # 获取服务票据
                    ticket = self.get_service_ticket(service_url)
                    
                    # 获取服务cookies
                    if service_name == "bb":
                        service_cookies = self.get_bb_cookies(ticket)
                    elif service_name == "tis":
                        service_cookies = self.get_tis_cookies(ticket)
                    else:
                        service_cookies = {}
                    
                    # 验证cookies
                    is_valid = self.validate_cookies(service_name, service_cookies)
                    
                    results["services"][service_name] = {
                        "service_url": service_url,
                        "ticket": ticket,
                        "cookies": service_cookies,
                        "cookie_count": len(service_cookies),
                        "is_valid": is_valid,
                        "login_url": f"{service_url}?ticket={ticket}"
                    }
                    
                    
                except Exception as e:
                    results["services"][service_name] = {
                        "error": str(e),
                        "cookies": {},
                        "cookie_count": 0,
                        "is_valid": False
                    }
            
            return results
        
        except Exception as e:
            results["error"] = str(e)
            return results
    
    def save_cookies_to_file(self, cookies_data: Dict[str, Any], filename: str = "util/data/cookies.json"):
        """保存cookies到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(cookies_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass
    

def get_cookies_for_user(sid: str, password: str, output_file: str = "util/data/cookies.json") -> Dict[str, Any]:
    """
    为指定用户获取所有系统的cookies
    
    Args:
        sid: 学号
        password: 密码
        output_file: 输出文件名
        
    Returns:
        cookies数据字典
    """
    extractor = CookieExtractor()
    
    try:
        # 提取cookies
        cookies_data = extractor.extract_all_cookies(sid, password)
        
        
        # 保存到文件
        extractor.save_cookies_to_file(cookies_data, output_file)
        print(f"保存到: {output_file}")
        
        return cookies_data
        
    except Exception as e:
        print(f"失败: {e}")
        return {"error": str(e)}

'''
python -c "from util.get_cookies import get_cookies_for_user; result = get_cookies_for_user('12311020', '5616298laz'); 
print('获取cookies结果:', '成功' if result and 'error' not in result else '失败')"
'''