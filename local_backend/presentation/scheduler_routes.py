from fastapi import APIRouter, Depends, HTTPException
from service.scheduler_service import scheduler_service
from service.blackboard_service import BlackboardService
from database.code.operations.database_user_operations import list_users

router = APIRouter(prefix="/api/v1/scheduler", tags=["Scheduler"])
blackboard_service = BlackboardService()

@router.get("/status")
async def get_scheduler_status():
    """获取定时任务调度器状态"""
    jobs = scheduler_service.get_jobs()
    
    return {
        "success": True,
        "is_running": scheduler_service.is_running,
        "jobs": jobs
    }

@router.post("/start")
async def start_scheduler(interval_minutes: int = 60):
    """启动定时任务调度器"""
    scheduler_service.start(sync_interval_minutes=interval_minutes)
    
    return {
        "success": True,
        "message": f"定时任务调度器已启动，同步间隔: {interval_minutes} 分钟"
    }

@router.post("/stop")
async def stop_scheduler():
    """停止定时任务调度器"""
    scheduler_service.stop()
    
    return {
        "success": True,
        "message": "定时任务调度器已停止"
    }

@router.post("/trigger-sync")
async def trigger_manual_sync(user_id: str = None):
    """手动触发同步任务
    
    Args:
        user_id: 指定用户ID进行同步，不传则同步所有已绑定用户
    """
    if user_id:
        # 同步指定用户
        try:
            status = blackboard_service.get_blackboard_status(user_id)
            if not status.get('is_bound'):
                raise HTTPException(status_code=400, detail="用户未绑定Blackboard")
            
            result = blackboard_service.sync_blackboard_data(user_id)
            return {
                "success": True,
                "message": f"用户 {user_id} 同步完成",
                "result": result
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # 同步所有已绑定用户
        users = list_users()
        synced_count = 0
        failed_count = 0
        results = []
        
        for user in users:
            uid = user.get('user_id')
            if not uid:
                continue
            
            try:
                status = blackboard_service.get_blackboard_status(uid)
                if status.get('is_bound'):
                    result = blackboard_service.sync_blackboard_data(uid)
                    if result.get('success'):
                        synced_count += 1
                    else:
                        failed_count += 1
                    results.append({"user_id": uid, "success": result.get('success'), "message": result.get('message')})
            except Exception as e:
                failed_count += 1
                results.append({"user_id": uid, "success": False, "message": str(e)})
        
        return {
            "success": True,
            "message": f"批量同步完成: 成功 {synced_count} 人, 失败 {failed_count} 人",
            "results": results
        }

@router.get("/sync-history")
async def get_sync_history():
    """获取同步历史记录（模拟实现）"""
    return {
        "success": True,
        "message": "同步历史功能待实现",
        "history": []
    }
