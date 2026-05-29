from typing import Optional
from sqlalchemy.orm import Session
from model.entities import User
from crud.credits import create_credits


def create_user(
    db: Session,
    sid: int,
    tis_info: dict,
    photo_info: dict,
    grade_info: dict,
    interest: Optional[str] = None,
) -> User:
    """
    创建并存入一个新的用户，如果已存在则直接返回
    """
    user = db.query(User).filter(User.user_id == sid).first()
    if user:
        return user  # 已存在则直接返回

    name = tis_info.get("姓名")
    pinyin_name = tis_info.get("姓名拼音")
    photo = photo_info.get("base64")
    gender_code = tis_info.get("性别代码")
    gender = "男" if gender_code == "1" else "女"
    birth_date = tis_info.get("出生日期")
    college = tis_info.get("所属书院名称")
    dormitory = tis_info.get("宿舍号")
    phone = tis_info.get("联系电话")
    email = tis_info.get("电子邮箱")
    department = tis_info.get("院系名称")

    gpa = grade_info.get("GPA")
    rank = grade_info.get("Rank")

    user = User(
        user_id=sid,
        name=name,
        pinyin_name=pinyin_name,
        photo=photo,
        gender=gender,
        birth_date=birth_date,
        college=college,
        dormitory=dormitory,
        phone=phone,
        email=email,
        gpa=gpa,
        rank=rank,
        department=department,
        interest=interest,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 创建学分数据
    create_credits(db, user_id=sid)

    return user


def get_user_by_sid(db: Session, sid: str):
    """
    根据学号获取用户
    """
    return db.query(User).filter(User.user_id == sid).first()


def get_user_by_email(db: Session, email: str):
    """根据邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()


def update_user_interest(db: Session, sid: int, interest: str) -> Optional[User]:
    """更新用户兴趣爱好"""
    user = db.query(User).filter(User.user_id == sid).first()
    if not user:
        return None

    user.interest = interest
    db.commit()
    db.refresh(user)
    return user
