from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from core.cas_auth import cas_login, get_service_ticket
from core.config import SERVICES, TOKEN_EXPIRE_MINUTES
from model.schemas import LoginRequest

from util.get_cookies import get_cookies_for_user
from util.bb_course import get_bb_courses
from util.tis_schedule import fetch_tis_schedule_data, fetch_and_process_schedule
# from util.bb_download import download_all_courses, load_courses
from util.tis_query import query_tis_data
from util.download_photo import download_student_photo
from util.bb_calendar import get_bb_calendar
from util.tis_grade import query_grades
from crud.schedule import save_schedule_to_db
from crud.user import create_user
from crud.ddl import save_ddl_to_db
from core.database import get_db
from sqlalchemy.orm import Session
from core import security
from model import schemas

def sso_login(form_data: OAuth2PasswordRequestForm,
              db: Session = Depends(get_db)):
    """单点登录以及爬取初始服务的数据"""
    sid = form_data.username      # 用 username 字段当 sid
    password = form_data.password # 直接拿密码

    # 获取所有服务的cookies
    cookies_data = get_cookies_for_user(sid, password)

    if "error" in cookies_data:
        raise HTTPException(status_code=401, detail="认证失败，请检查学号和密码")
    
    # 获取tis个人信息
    tis_info = query_tis_data()

    # 获取个人照片信息
    photo_info = download_student_photo()

    grade_info = query_grades()
    
    create_user(db, sid, tis_info, photo_info, grade_info)

    # 获取并保存Blackboard课程
    courses = get_bb_courses()

    # 获取并保存TIS课表
    schedule = fetch_and_process_schedule()
    save_schedule_to_db(db, sid, schedule)

    # 获取bb上的ddl信息
    calendar = get_bb_calendar()
    print(calendar)
    save_ddl_to_db(db, sid, calendar)

    # 生成JWT token
    token = security.generate_access_jwt(sid, TOKEN_EXPIRE_MINUTES)

    return schemas.Token(access_token=token)

    # # 验证请求的服务
    # invalid_services = [s for s in request.services if s not in SERVICES]
    # if invalid_services:
    #     raise HTTPException(status_code=400, detail=f"无效的服务: {', '.join(invalid_services)}")
    
    # # 初始登录服务
    # initial_service = SERVICES[request.services[0]]
    
    # # CAS登录
    # cas_cookies = cas_login(request.sid, request.password, initial_service)

    # # 获取各服务的票据
    # results= {}
    # for service in request.services:
    #     try:
    #         ticket = get_service_ticket(cas_cookies, SERVICES[service])
    #         results[service] = {
    #             "service_url": SERVICES[service],
    #             "ticket": ticket,
    #             "login_url": f"{SERVICES[service]}?ticket={ticket}"
    #         }
    #     except HTTPException as e:
    #         results[service] = {"error": e.detail}
    
    

def list_services():
    """获取所有可用服务"""
    return {
        "available_services": list(SERVICES.keys()),
        "service_details": SERVICES
    }