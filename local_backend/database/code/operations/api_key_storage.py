"""JSONL-based API key storage for user settings.

Stores API keys per-user, per-provider in local_backend/data/api_keys.jsonl.
Designed for later migration to the database.
"""

import json
import datetime
from pathlib import Path
from typing import Optional


def _get_storage_path() -> Path:
    """Return path to api_keys.jsonl, creating parent dir if needed."""
    p = Path(__file__).resolve().parent.parent.parent / "data" / "api_keys.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _read_all_lines() -> list[dict]:
    """Read all lines from the JSONL file."""
    path = _get_storage_path()
    if not path.exists():
        return []
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def _write_all_lines(entries: list[dict]) -> None:
    """Atomically write all lines to the JSONL file."""
    path = _get_storage_path()
    temp_path = path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    temp_path.replace(path)


def _mask_api_key(key: str) -> str:
    """Mask an API key for display: first 4 + •••• + last 4."""
    if not key or len(key) <= 8:
        return key or ""
    return key[:4] + "••••" + key[-4:]


def list_api_keys(user_id: str) -> list[dict]:
    """List all API keys for a given user, with masked keys for safe display.

    Returns a list of dicts with: provider, api_key_masked, api_base,
    model, is_active, updated_at, last_test_success.
    """
    all_entries = _read_all_lines()
    results = []
    for entry in all_entries:
        if entry.get("user_id") == user_id:
            results.append({
                "provider": entry.get("provider", ""),
                "api_key_masked": _mask_api_key(entry.get("api_key", "")),
                "api_base": entry.get("api_base", ""),
                "model": entry.get("model", ""),
                "is_active": entry.get("is_active", False),
                "updated_at": entry.get("updated_at", ""),
                "last_test_success": entry.get("last_test_success"),
            })
    return results


def save_api_key(user_id: str, provider: str, api_key: str, api_base: str,
                 model: str = "", last_test_success: Optional[bool] = None) -> None:
    """Save or update an API key for a user+provider pair.

    If an entry already exists for the same user_id+provider, it is replaced.
    Otherwise a new entry is appended.
    """
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = _read_all_lines()

    found = False
    for i, entry in enumerate(entries):
        if entry.get("user_id") == user_id and entry.get("provider") == provider:
            entry["api_key"] = api_key
            entry["api_base"] = api_base
            entry["model"] = model
            entry["updated_at"] = now
            entry["last_test_success"] = last_test_success
            found = True
            break

    if not found:
        entries.append({
            "user_id": user_id,
            "provider": provider,
            "api_key": api_key,
            "api_base": api_base,
            "model": model,
            "is_active": False,
            "updated_at": now,
            "last_test_success": last_test_success,
        })

    _write_all_lines(entries)


def delete_api_key(user_id: str, provider: str) -> None:
    """Delete an API key entry for a given user+provider."""
    entries = _read_all_lines()
    entries = [
        e for e in entries
        if not (e.get("user_id") == user_id and e.get("provider") == provider)
    ]
    _write_all_lines(entries)


def toggle_api_key(user_id: str, provider: str) -> dict:
    """Toggle the is_active flag for a given user+provider pair.

    If toggling ON, all other keys for this user are set to inactive first
    (only one active key at a time).
    Returns {"success": bool, "is_active": bool}.
    """
    entries = _read_all_lines()
    target_found = False
    new_active = False

    for entry in entries:
        if entry.get("user_id") != user_id:
            continue
        if entry.get("provider") == provider:
            current = entry.get("is_active", False)
            new_active = not current
            entry["is_active"] = new_active
            target_found = True
        elif new_active:
            # If we're activating this one, deactivate all others
            entry["is_active"] = False

    if not target_found:
        return {"success": False, "is_active": False}

    # If activating, need a second pass to deactivate others
    # (handles case where target is after others in the list)
    if new_active:
        for entry in entries:
            if entry.get("user_id") == user_id and entry.get("provider") != provider:
                entry["is_active"] = False

    _write_all_lines(entries)
    return {"success": True, "is_active": new_active}


def test_api_key(provider: str, api_key: str, api_base: str) -> dict:
    """Test connectivity for a given API key by making a lightweight API call.

    Returns {"success": bool, "message": str}.
    """
    import httpx

    base = api_base.rstrip("/") if api_base else "https://api.openai.com/v1"
    url = f"{base}/chat/completions"

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        with httpx.Client(timeout=httpx.Timeout(connect=8.0, read=15.0)) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                return {"success": True, "message": f"{provider} 连接成功"}
            elif resp.status_code == 401:
                return {"success": False, "message": "API Key 无效 (401 Unauthorized)"}
            elif resp.status_code == 403:
                return {"success": False, "message": "API Key 权限不足 (403 Forbidden)"}
            elif resp.status_code == 429:
                return {"success": False, "message": "请求过于频繁 (429)，请稍后重试"}
            else:
                body = resp.text[:200]
                return {"success": False, "message": f"HTTP {resp.status_code}: {body}"}
    except httpx.ConnectError:
        return {"success": False, "message": f"无法连接到 {base}，请检查 API Base URL 和网络"}
    except httpx.ReadTimeout:
        return {"success": False, "message": "连接超时，请检查网络或 API Base URL"}
    except Exception as e:
        return {"success": False, "message": f"测试失败: {type(e).__name__}: {e}"}
