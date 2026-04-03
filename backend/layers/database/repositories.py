from typing import Optional, List
from sqlalchemy.orm import Session
from layers.database.connection import SessionLocal
from layers.database.models import User, Schedule, Task, AgentChat


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

    def update_user(self, user_id: int, update_data: dict):
        db = SessionLocal()
        try:
            db_user = db.query(User).filter(User.id == user_id).first()
            if db_user:
                for key, value in update_data.items():
                    if hasattr(db_user, key):
                        setattr(db_user, key, value)
                db.commit()
                db.refresh(db_user)
                return db_user
            return None
        except Exception as e:
            db.rollback()
            print(f"Error updating user: {e}")
            return None
        finally:
            db.close()

    def delete_user(self, user_id: int):
        db = SessionLocal()
        try:
            db_user = db.query(User).filter(User.id == user_id).first()
            if db_user:
                db.delete(db_user)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            print(f"Error deleting user: {e}")
            return False
        finally:
            db.close()


class ScheduleRepository:
    def create_schedule(self, schedule_data: dict):
        db = SessionLocal()
        try:
            db_schedule = Schedule(
                user_id=schedule_data['user_id'],
                title=schedule_data['title'],
                description=schedule_data.get('description'),
                start_time=schedule_data['start_time'],
                end_time=schedule_data['end_time'],
                location=schedule_data.get('location'),
                event_type=schedule_data.get('event_type', 'personal'),
                source=schedule_data.get('source', 'manual')
            )
            db.add(db_schedule)
            db.commit()
            db.refresh(db_schedule)
            return db_schedule
        except Exception as e:
            db.rollback()
            print(f"Error creating schedule: {e}")
            return None
        finally:
            db.close()

    def get_schedules_by_user(self, user_id: int):
        db = SessionLocal()
        try:
            return db.query(Schedule).filter(Schedule.user_id == user_id).all()
        except Exception as e:
            print(f"Error getting schedules by user: {e}")
            return []
        finally:
            db.close()

    def get_schedule_by_id(self, schedule_id: int):
        db = SessionLocal()
        try:
            return db.query(Schedule).filter(Schedule.id == schedule_id).first()
        except Exception as e:
            print(f"Error getting schedule by id: {e}")
            return None
        finally:
            db.close()

    def update_schedule(self, schedule_id: int, update_data: dict):
        db = SessionLocal()
        try:
            db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if db_schedule:
                for key, value in update_data.items():
                    if hasattr(db_schedule, key):
                        setattr(db_schedule, key, value)
                db.commit()
                db.refresh(db_schedule)
                return db_schedule
            return None
        except Exception as e:
            db.rollback()
            print(f"Error updating schedule: {e}")
            return None
        finally:
            db.close()

    def delete_schedule(self, schedule_id: int):
        db = SessionLocal()
        try:
            db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if db_schedule:
                db.delete(db_schedule)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            print(f"Error deleting schedule: {e}")
            return False
        finally:
            db.close()


class TaskRepository:
    def create_task(self, task_data: dict):
        db = SessionLocal()
        try:
            db_task = Task(
                user_id=task_data['user_id'],
                title=task_data['title'],
                description=task_data.get('description'),
                due_date=task_data.get('due_date'),
                priority=task_data.get('priority', 'medium'),
                status=task_data.get('status', 'pending')
            )
            db.add(db_task)
            db.commit()
            db.refresh(db_task)
            return db_task
        except Exception as e:
            db.rollback()
            print(f"Error creating task: {e}")
            return None
        finally:
            db.close()

    def get_tasks_by_user(self, user_id: int):
        db = SessionLocal()
        try:
            return db.query(Task).filter(Task.user_id == user_id).all()
        except Exception as e:
            print(f"Error getting tasks by user: {e}")
            return []
        finally:
            db.close()

    def get_task_by_id(self, task_id: int):
        db = SessionLocal()
        try:
            return db.query(Task).filter(Task.id == task_id).first()
        except Exception as e:
            print(f"Error getting task by id: {e}")
            return None
        finally:
            db.close()

    def update_task(self, task_id: int, update_data: dict):
        db = SessionLocal()
        try:
            db_task = db.query(Task).filter(Task.id == task_id).first()
            if db_task:
                for key, value in update_data.items():
                    if hasattr(db_task, key):
                        setattr(db_task, key, value)
                db.commit()
                db.refresh(db_task)
                return db_task
            return None
        except Exception as e:
            db.rollback()
            print(f"Error updating task: {e}")
            return None
        finally:
            db.close()

    def delete_task(self, task_id: int):
        db = SessionLocal()
        try:
            db_task = db.query(Task).filter(Task.id == task_id).first()
            if db_task:
                db.delete(db_task)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            print(f"Error deleting task: {e}")
            return False
        finally:
            db.close()


class AgentChatRepository:
    def create_chat(self, chat_data: dict):
        db = SessionLocal()
        try:
            db_chat = AgentChat(
                user_id=chat_data['user_id'],
                session_id=chat_data['session_id'],
                message=chat_data['message'],
                role=chat_data['role'],
                tool_calls=chat_data.get('tool_calls')
            )
            db.add(db_chat)
            db.commit()
            db.refresh(db_chat)
            return db_chat
        except Exception as e:
            db.rollback()
            print(f"Error creating chat: {e}")
            return None
        finally:
            db.close()

    def get_chats_by_session(self, session_id: str):
        db = SessionLocal()
        try:
            return db.query(AgentChat).filter(AgentChat.session_id == session_id).all()
        except Exception as e:
            print(f"Error getting chats by session: {e}")
            return []
        finally:
            db.close()

    def get_chats_by_user(self, user_id: int):
        db = SessionLocal()
        try:
            return db.query(AgentChat).filter(AgentChat.user_id == user_id).all()
        except Exception as e:
            print(f"Error getting chats by user: {e}")
            return []
        finally:
            db.close()
