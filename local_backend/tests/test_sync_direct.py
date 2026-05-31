#!/usr/bin/env python3
"""
直接测试数据库同步功能 - 绕过 API 层，直接测试数据库操作
"""

import sys
import os

import pytest

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), 'local_backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'server_backend'))

from local_backend.database.code.command.database_command import (
    create_schedule, get_schedule, list_schedule_by_user, delete_schedule,
    create_data, get_data, list_data_by_user, delete_data, upsert_user, get_user,
    create_category, list_categories_by_user, delete_category
)
from server_backend.database.code.command.database_command import (
    create_schedule as server_create_schedule,
    list_schedule_by_user as server_list_schedule_by_user,
    delete_schedule as server_delete_schedule,
    create_data as server_create_data,
    list_data_by_user as server_list_data_by_user,
    delete_data as server_delete_data,
    upsert_user as server_upsert_user,
    create_category as server_create_category,
    list_categories_by_user as server_list_categories_by_user,
    delete_category as server_delete_category
)

# 测试用户
TEST_USER_ID = "sync_direct_test@mail.sustech.edu.cn"
TEST_USER_NAME = "Sync Direct Test User"

# 测试数据
TEST_SCHEDULE = {
    "user_id": TEST_USER_ID,
    "schedule_event_type": "meeting",
    "schedule_priority": 1,
    "schedule_title": "Direct Sync Test Schedule",
    "schedule_start_time": "2026-06-01 09:00:00",
    "schedule_end_time": "2026-06-01 10:00:00",
    "schedule_location": "Direct Test Location",
    "schedule_description": "This is a direct sync test schedule",
    "schedule_related_link": None,
    "schedule_recurrence_rule": None,
    "schedule_color_tag": "#FF5733"
}

TEST_TASK = {
    "user_id": TEST_USER_ID,
    "data_category_id": 1,
    "data_content_type": "task",
    "data_classification_code": 3,
    "data_title": "Direct Sync Test Task",
    "data_content_text": "This is a direct sync test task",
    "data_link_url": None,
    "data_release_time": None,
    "data_ddl_time": "2026-06-10 23:59:59",
    "data_is_previewable": 0,
    "data_created_at": "2026-01-01 00:00:00"
}


@pytest.mark.skip(reason="uses deprecated schedule table; schema has been migrated to event table")
def test_direct_sync():
    """直接测试数据库同步"""
    print("="*60)
    print("开始直接数据库同步测试")
    print("="*60)
    
    # 1. 在 Local 创建测试用户
    print("\n[步骤1] 在 Local 创建测试用户")
    try:
        upsert_user(
            user_id=TEST_USER_ID,
            username=TEST_USER_NAME,
            user_email=TEST_USER_ID,
            user_is_active=1,
            user_created_at="2026-01-01 00:00:00",
            user_last_login="2026-01-01 00:00:00",
            user_source_device_id="test_device"
        )
        print("[OK] Local 用户创建成功")
    except Exception as e:
        print("[WARN] 创建用户可能已存在或失败: %s" % e)
    
    # 2. 在 Local 创建测试日程
    print("\n[步骤2] 在 Local 创建测试日程")
    local_schedule_id = create_schedule(**TEST_SCHEDULE)
    print("[OK] Local 日程创建成功，ID: %d" % local_schedule_id)

    # 2.5 在 Local 准备 category（任务需要外键）
    local_category_created = False
    local_categories = list_categories_by_user(TEST_USER_ID)
    if local_categories:
        local_category_id = local_categories[0]["category_id"]
        print("[OK] Local category 已存在，ID: %d" % local_category_id)
    else:
        local_category_id = create_category(
            user_id=TEST_USER_ID,
            category_kind="task",
            category_title="Direct Sync Local Task Category",
            category_content=None,
            category_link=None,
            category_created_at="2026-01-01 00:00:00",
        )
        local_category_created = True
        print("[OK] Local category 创建成功，ID: %d" % local_category_id)
    
    # 3. 在 Local 创建测试任务
    print("\n[步骤3] 在 Local 创建测试任务")
    local_task_payload = dict(TEST_TASK)
    local_task_payload["data_category_id"] = local_category_id
    local_task_id = create_data(**local_task_payload)
    print("[OK] Local 任务创建成功，ID: %d" % local_task_id)
    
    # 4. 从 Local 获取数据
    print("\n[步骤4] 从 Local 获取数据")
    local_schedules = list_schedule_by_user(TEST_USER_ID)
    local_tasks = list_data_by_user(TEST_USER_ID)
    print("[INFO] Local 日程数量: %d" % len(local_schedules))
    print("[INFO] Local 任务数量: %d" % len(local_tasks))
    
    # 5. 模拟同步到 Server（直接调用 Server 的数据库操作）
    print("\n[步骤5] 模拟同步数据到 Server")
    
    # 先在 Server 创建用户
    try:
        server_upsert_user(
            user_id=TEST_USER_ID,
            username=TEST_USER_NAME,
            user_email=TEST_USER_ID,
            user_password_hash="test_hash",
            user_salt="test_salt",
            user_is_active=1,
            user_created_at="2026-01-01 00:00:00",
            user_last_login="2026-01-01 00:00:00",
            user_auto_login_token=None,
            user_source_device_id="test_device"
        )
        print("[OK] Server 用户创建成功")
    except Exception as e:
        print("[WARN] Server 用户可能已存在或失败: %s" % e)
    
    # 在 Server 创建 category（任务需要外键）
    server_category_created = False
    try:
        server_categories = server_list_categories_by_user(TEST_USER_ID)
        if server_categories:
            server_category_id = server_categories[0]["category_id"]
            print("[OK] Server category 已存在，ID: %d" % server_category_id)
        else:
            server_category_id = server_create_category(
                user_id=TEST_USER_ID,
                category_kind="task",
                category_title="Default Task Category",
                category_content=None,
                category_link=None,
                category_created_at="2026-01-01 00:00:00"
            )
            server_category_created = True
            print("[OK] Server category 创建成功，ID: %d" % server_category_id)
    except Exception as e:
        print("[WARN] Server category 可能已存在或失败: %s" % e)
        server_categories = server_list_categories_by_user(TEST_USER_ID)
        if not server_categories:
            raise
        server_category_id = server_categories[0]["category_id"]
    
    # 同步日程
    for schedule in local_schedules:
        server_create_schedule(
            user_id=schedule['user_id'],
            schedule_event_type=schedule.get('schedule_event_type', 'meeting'),
            schedule_title=schedule['schedule_title'],
            schedule_start_time=schedule['schedule_start_time'],
            schedule_end_time=schedule['schedule_end_time'],
            schedule_location=schedule.get('schedule_location'),
            schedule_description=schedule.get('schedule_description'),
            schedule_related_link=schedule.get('schedule_related_link'),
            schedule_recurrence_rule=schedule.get('schedule_recurrence_rule'),
            schedule_color_tag=schedule.get('schedule_color_tag'),
            schedule_priority=schedule.get('schedule_priority', 2),
        )
    print("[OK] 日程同步到 Server 成功")
    
    # 同步任务
    for task in local_tasks:
        server_create_data(
            user_id=task['user_id'],
            data_category_id=server_category_id,
            data_content_type=task.get('data_content_type', 'task'),
            data_classification_code=task.get('data_classification_code', 3),
            data_title=task['data_title'],
            data_content_text=task.get('data_content_text'),
            data_link_url=task.get('data_link_url'),
            data_release_time=task.get('data_release_time'),
            data_ddl_time=task.get('data_ddl_time'),
            data_is_previewable=task.get('data_is_previewable', 0),
            data_created_at=task.get('data_created_at', '2026-01-01 00:00:00')
        )
    print("[OK] 任务同步到 Server 成功")
    
    # 6. 验证 Server 端数据
    print("\n[步骤6] 验证 Server 端数据")
    server_schedules = server_list_schedule_by_user(TEST_USER_ID)
    server_tasks = server_list_data_by_user(TEST_USER_ID)
    print("[INFO] Server 日程数量: %d" % len(server_schedules))
    print("[INFO] Server 任务数量: %d" % len(server_tasks))
    
    # 验证日程标题
    schedule_found = any(s.get("schedule_title") == TEST_SCHEDULE["schedule_title"] for s in server_schedules)
    if schedule_found:
        print("[OK] 日程已成功同步到 Server")
    else:
        print("[FAIL] 日程同步失败")
    
    # 验证任务标题
    task_found = any(t.get("data_title") == TEST_TASK["data_title"] for t in server_tasks)
    if task_found:
        print("[OK] 任务已成功同步到 Server")
    else:
        print("[FAIL] 任务同步失败")
    
    # 7. 模拟从 Server 拉取数据到 Local
    print("\n[步骤7] 模拟从 Server 拉取数据")
    
    # 先清空 Local 数据（模拟刷新）
    for s in local_schedules:
        delete_schedule(s['schedule_id'])
    for t in local_tasks:
        delete_data(t['data_id'])
    print("[OK] Local 数据已清空")
    
    # 从 Server 拉取日程
    for schedule in server_schedules:
        create_schedule(
            user_id=schedule['user_id'],
            schedule_event_type=schedule.get('schedule_event_type', 'meeting'),
            schedule_title=schedule['schedule_title'],
            schedule_start_time=schedule['schedule_start_time'],
            schedule_end_time=schedule['schedule_end_time'],
            schedule_location=schedule.get('schedule_location'),
            schedule_description=schedule.get('schedule_description'),
            schedule_related_link=schedule.get('schedule_related_link'),
            schedule_recurrence_rule=schedule.get('schedule_recurrence_rule'),
            schedule_color_tag=schedule.get('schedule_color_tag'),
            schedule_priority=schedule.get('schedule_priority', 2),
        )
    print("[OK] 从 Server 拉取日程成功")
    
    # 从 Server 拉取任务
    for task in server_tasks:
        create_data(
            user_id=task['user_id'],
            data_category_id=local_category_id,
            data_content_type=task.get('data_content_type', 'task'),
            data_classification_code=task.get('data_classification_code', 3),
            data_title=task['data_title'],
            data_content_text=task.get('data_content_text'),
            data_link_url=task.get('data_link_url'),
            data_release_time=task.get('data_release_time'),
            data_ddl_time=task.get('data_ddl_time'),
            data_is_previewable=task.get('data_is_previewable', 0),
            data_created_at=task.get('data_created_at', '2026-01-01 00:00:00')
        )
    print("[OK] 从 Server 拉取任务成功")
    
    # 8. 最终验证数据一致性
    print("\n[步骤8] 最终数据一致性验证")
    final_local_schedules = list_schedule_by_user(TEST_USER_ID)
    final_local_tasks = list_data_by_user(TEST_USER_ID)
    
    print("[INFO] 最终 Local 日程数量: %d" % len(final_local_schedules))
    print("[INFO] 最终 Local 任务数量: %d" % len(final_local_tasks))
    
    # 验证数据一致性
    all_tests_passed = True
    
    # 验证日程标题
    local_schedule_titles = {s["schedule_title"] for s in final_local_schedules}
    server_schedule_titles = {s["schedule_title"] for s in server_schedules}
    
    if local_schedule_titles == server_schedule_titles:
        print("[OK] 日程数据一致")
    else:
        print("[FAIL] 日程数据不一致")
        all_tests_passed = False
    
    # 验证任务标题
    local_task_titles = {t["data_title"] for t in final_local_tasks}
    server_task_titles = {t["data_title"] for t in server_tasks}
    
    if local_task_titles == server_task_titles:
        print("[OK] 任务数据一致")
    else:
        print("[FAIL] 任务数据不一致")
        all_tests_passed = False
    
    # 9. 清理测试数据
    print("\n[步骤9] 清理测试数据")
    for s in final_local_schedules:
        delete_schedule(s['schedule_id'])
    for t in final_local_tasks:
        delete_data(t['data_id'])
    for s in server_schedules:
        server_delete_schedule(s['schedule_id'])
    for t in server_tasks:
        server_delete_data(t['data_id'])
    if local_category_created:
        delete_category(local_category_id)
    if server_category_created:
        server_delete_category(server_category_id)
    print("[OK] 测试数据已清理")
    
    print("\n" + "="*60)
    if all_tests_passed:
        print("[SUCCESS] 所有同步测试通过！Local 和 Server 数据一致")
    else:
        print("[FAIL] 同步测试失败，请检查日志")
    print("="*60)


if __name__ == "__main__":
    test_direct_sync()