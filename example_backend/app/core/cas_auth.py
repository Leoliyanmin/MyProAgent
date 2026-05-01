import requests
from fastapi import HTTPException
from urllib3.exceptions import InsecureRequestWarning
import warnings

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
CAS_LOGIN_URL = "https://cas.sustech.edu.cn/cas/login"

def cas_login(sid: str, password: str, service_url: str):
    """CAS登录并获取TGT Cookie"""
    try:
        # 获取登录页面和execution token
        session = requests.Session()
        session.headers.update({"user-agent": UA})
        login_page = session.get(CAS_LOGIN_URL, params={"service": service_url}, verify=False)
        
        if login_page.status_code != 200:
            raise HTTPException(status_code=502, detail="CAS服务不可用")
        
        # 解析execution token （CAS登录表单的动态令牌，防止CSRF攻击）
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
        login_response = session.post(
            CAS_LOGIN_URL,
            data=login_data,
            allow_redirects=False,
            verify=False
        )

        if login_response.status_code != 302 or "Location" not in login_response.headers:
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 返回有效的CAS会话
        print(session.cookies.get_dict())
        return session.cookies.get_dict()
    
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail="CAS服务请求失败") from e


def get_service_ticket(cas_cookies: dict, service_url: str):
    """获取特定服务的ST票据"""
    try:
        session = requests.Session()
        session.headers.update({"user-agent": UA})
        session.cookies.update(cas_cookies)

        # 请求服务票据
        response = session.get(
            CAS_LOGIN_URL,
            params={"service": service_url},
            allow_redirects=False,
            verify=False
        )

        if response.status_code != 302 or "Location" not in response.headers:
            raise ValueError("获取服务票据失败")
        
        # 从重定向URL中提取票据
        location = response.headers["Location"]
        if "ticket=" not in location:
            raise ValueError("票据未找到")
        
        return location.split("ticket=")[1].split("&")[0]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务票据失败: {str(e)}")
