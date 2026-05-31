import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from presentation.dependencies import get_current_user_id

router = APIRouter(prefix="/dashboard-presets", tags=["Dashboard Presets"])

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "db" / "local.db"


def _get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


class PresetUpsert(BaseModel):
    preset_name: str
    preset_data: str
    preset_id: int | None = None


@router.get("/")
async def list_presets(user_id: str = Depends(get_current_user_id)):
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT preset_id, preset_name, preset_data, created_at, updated_at "
            "FROM dashboard_preset WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


@router.post("/")
async def save_preset(body: PresetUpsert, user_id: str = Depends(get_current_user_id)):
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        if body.preset_id:
            conn.execute(
                "UPDATE dashboard_preset SET preset_name = ?, preset_data = ?, updated_at = ? "
                "WHERE preset_id = ? AND user_id = ?",
                (body.preset_name, body.preset_data, now, body.preset_id, user_id)
            )
            preset_id = body.preset_id
        else:
            existing = conn.execute(
                "SELECT preset_id FROM dashboard_preset WHERE user_id = ? AND preset_name = ?",
                (user_id, body.preset_name)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE dashboard_preset SET preset_data = ?, updated_at = ? WHERE preset_id = ?",
                    (body.preset_data, now, existing["preset_id"])
                )
                preset_id = existing["preset_id"]
            else:
                cur = conn.execute(
                    "INSERT INTO dashboard_preset (user_id, preset_name, preset_data, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (user_id, body.preset_name, body.preset_data, now, now)
                )
                preset_id = cur.lastrowid
        conn.commit()
    return {"success": True, "preset_id": preset_id}


@router.delete("/{preset_id}")
async def delete_preset(preset_id: int, user_id: str = Depends(get_current_user_id)):
    with _get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM dashboard_preset WHERE preset_id = ? AND user_id = ?",
            (preset_id, user_id)
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Preset not found")
        conn.commit()
    return {"success": True}
