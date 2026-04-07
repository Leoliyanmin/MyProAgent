from typing import Optional, List
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import User, Schedule, Task, AgentChat, SyncRecord


class UserRepository:
    def create_user(self, user_data: dict):
        db = SessionLocal()
        try:
            db_user = User(
                email=user_data['email'],
                hashed_password=user_data['hashed_password'],
                full_name=user_data.get('full_name'),
                student_id=user_data.get('student_id'),
                is_active=True
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except Exception as e:
            db.rollback()
            print(f"Error creating user: {e}")
            return None
        finally:
            db.close()

    def get_user_by_email(self, email: str):
        db = SessionLocal()
        try:
            return db.query(User).filter(User.email == email).first()
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
        finally:
            db.close()

    def get_user_by_id(self, user_id: int):
        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            print(f"Error getting user by id: {e}")
            return None
        finally:
            db.close()


class SyncRepository:
    def sync_schedules(self, user_id: int, schedules: list):
        db = SessionLocal()
        try:
            synced_count = 0
            for schedule_data in schedules:
                # 检查是否存在
                existing = db.query(Schedule).filter(
                    Schedule.user_id == user_id,
                    Schedule.title == schedule_data.get('title'),
                    Schedule.start_time == schedule_data.get('start_time')
                ).first()
                
                if existing:
                    # 更新
                    for key, value in schedule_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                else:
                    # 创建
                    schedule = Schedule(
                        user_id=user_id,
                        title=schedule_data.get('title'),
                        description=schedule_data.get('description'),
                        start_time=schedule_data.get('start_time'),
                        end_time=schedule_data.get('end_time'),
                        location=schedule_data.get('location'),
                        event_type=schedule_data.get('event_type', 'personal'),
                        source=schedule_data.get('source', 'sync')
                    )
                    db.add(schedule)
                synced_count += 1
            
            # 记录同步
            sync_record = SyncRecord(
                user_id=user_id,
                data_type='schedules',
                synced_count=synced_count
            )
            db.add(sync_record)
            
            db.commit()
            return synced_count
        except Exception as e:
            db.rollback()
            print(f"Error syncing schedules: {e}")
            return 0
        finally:
            db.close()

    def sync_tasks(self, user_id: int, tasks: list):
        db = SessionLocal()
        try:
            synced_count = 0
            for task_data in tasks:
                # 检查是否存在
                existing = db.query(Task).filter(
                    Task.user_id == user_id,
                    Task.title == task_data.get('title')
                ).first()
                
                if existing:
                    # 更新
                    for key, value in task_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                else:
                    # 创建
                    task = Task(
                        user_id=user_id,
                        title=task_data.get('title'),
                        description=task_data.get('description'),
                        due_date=task_data.get('due_date'),
                        priority=task_data.get('priority', 'medium'),
                        status=task_data.get('status', 'pending')
                    )
                    db.add(task)
                synced_count += 1
            
            # 记录同步
            sync_record = SyncRecord(
                user_id=user_id,
                data_type='tasks',
                synced_count=synced_count
            )
            db.add(sync_record)
            
            db.commit()
            return synced_count
        except Exception as e:
            db.rollback()
            print(f"Error syncing tasks: {e}")
            return 0
        finally:
            db.close()

    def sync_chats(self, user_id: int, chats: list):
        db = SessionLocal()
        try:
            synced_count = 0
            for chat_data in chats:
                # 检查是否存在
                existing = db.query(AgentChat).filter(
                    AgentChat.user_id == user_id,
                    AgentChat.session_id == chat_data.get('session_id'),
                    AgentChat.message == chat_data.get('message'),
                    AgentChat.role == chat_data.get('role')
                ).first()
                
                if not existing:
                    # 创建
                    chat = AgentChat(
                        user_id=user_id,
                        session_id=chat_data.get('session_id'),
                        message=chat_data.get('message'),
                        role=chat_data.get('role'),
                        tool_calls=chat_data.get('tool_calls')
                    )
                    db.add(chat)
                    synced_count += 1
            
            # 记录同步
            sync_record = SyncRecord(
                user_id=user_id,
                data_type='chats',
                synced_count=synced_count
            )
            db.add(sync_record)
            
            db.commit()
            return synced_count
        except Exception as e:
            db.rollback()
            print(f"Error syncing chats: {e}")
            return 0
        finally:
            db.close()

    def get_synced_data(self, user_id: int, data_type: str):
        db = SessionLocal()
        try:
            if data_type == 'schedules':
                return db.query(Schedule).filter(Schedule.user_id == user_id).all()
            elif data_type == 'tasks':
                return db.query(Task).filter(Task.user_id == user_id).all()
            elif data_type == 'chats':
                return db.query(AgentChat).filter(AgentChat.user_id == user_id).all()
            return []
        except Exception as e:
            print(f"Error getting synced data: {e}")
            return []
        finally:
            db.close()
