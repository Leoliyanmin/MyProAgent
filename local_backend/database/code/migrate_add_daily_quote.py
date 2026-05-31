"""迁移脚本：为 user_setting 表添加 daily_quote 列。"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "database" / "db" / "local.db"


def migrate():
    if not DB_PATH.exists():
        print(f"[migrate_daily_quote] 数据库不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    try:
        cursor = conn.execute("PRAGMA table_info(user_setting)")
        columns = {row[1] for row in cursor.fetchall()}
        if "daily_quote" in columns:
            print("[migrate_daily_quote] daily_quote 列已存在，跳过。")
            return
        conn.execute("ALTER TABLE user_setting ADD COLUMN daily_quote TEXT")
        conn.commit()
        print("[migrate_daily_quote] 已添加 daily_quote 列。")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
