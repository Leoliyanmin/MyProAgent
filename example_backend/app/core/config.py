import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()
SERVICES = {
    "bb": "https://bb.sustech.edu.cn/webapps/bb-sso-BBLEARN/index.jsp",
    "tis": "https://tis.sustech.edu.cn/cas"
}

# 配置
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
CAS_LOGIN_URL = "https://cas.sustech.edu.cn/cas/login"


DATABASE_URL = os.environ.get('SUSTECH_ASSISTANT_DATABASE_URL')
SECRETE_KEY = os.environ.get('SUSTECH_ASSISTANT_SECRETE_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
BASE_URL = os.environ.get('BASE_URL')

BB_PORTAL_AJAX = "https://bb.sustech.edu.cn/webapps/portal/execute/tabs/tabAction"
BB_PARAMS = {
    "action": "refreshAjaxModule",
    "modId": "_3_1",          # 我的课程 模块ID
    "tabId": "_1_1",          # 首页 tab
    "tab_tab_group_id": "_1_1"
}
COURSE_OUT_JSON = "data/courses.json"

JWT_ENCODE_ALGORITHM = 'HS256'
TOKEN_EXPIRE_MINUTES = timedelta(minutes=60*24)

BASE_DIR = Path(__file__).resolve().parent
EMAIL_KEYS_DIR = Path(os.environ.get('EMAIL_KEYS_DIR', BASE_DIR / "keys"))
EMAIL_PRIVATE_KEY_PATH = Path(
    os.environ.get('EMAIL_PRIVATE_KEY_PATH', EMAIL_KEYS_DIR / "email_private.pem")
)
EMAIL_PUBLIC_KEY_PATH = Path(
    os.environ.get('EMAIL_PUBLIC_KEY_PATH', EMAIL_KEYS_DIR / "email_public.pem")
)
EMAIL_CREDENTIAL_SECRET_KEY = os.environ.get('EMAIL_CREDENTIAL_SECRET_KEY')