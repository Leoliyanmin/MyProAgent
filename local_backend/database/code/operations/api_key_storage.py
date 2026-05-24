"""JSONL-based API key storage for user settings.

Stores API keys per-user, per-provider, per-model in local_backend/data/api_keys.jsonl.
Supports multiple keys for the same provider with different models.
Each entry has a unique key_id for stable referencing.
"""

import json
import datetime
import uuid
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


def _generate_key_id() -> str:
    """Generate a unique, short, sortable key ID."""
    ts_hex = hex(int(datetime.datetime.utcnow().timestamp() * 1000))[2:]
    rand_hex = uuid.uuid4().hex[:8]
    return f"{ts_hex}_{rand_hex}"


def _migrate_entries(entries: list[dict]) -> list[dict]:
    """Ensure all entries have a key_id. Writes back if migration occurred."""
    needs_write = False
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    for entry in entries:
        if "key_id" not in entry:
            entry["key_id"] = _generate_key_id()
            entry["updated_at"] = entry.get("updated_at") or now
            needs_write = True
    if needs_write:
        _write_all_lines(entries)
    return entries


def list_api_keys(user_id: str) -> list[dict]:
    """List all API keys for a given user, with masked keys for safe display.

    Returns a list of dicts with: key_id, provider, api_key_masked, api_base,
    model, is_active, updated_at, last_test_success.
    """
    all_entries = _migrate_entries(_read_all_lines())
    results = []
    for entry in all_entries:
        if entry.get("user_id") == user_id:
            results.append({
                "key_id": entry.get("key_id", ""),
                "provider": entry.get("provider", ""),
                "api_key_masked": _mask_api_key(entry.get("api_key", "")),
                "api_base": entry.get("api_base", ""),
                "model": entry.get("model", ""),
                "is_active": entry.get("is_active", False),
                "updated_at": entry.get("updated_at", ""),
                "last_test_success": entry.get("last_test_success"),
            })
    # Sort by updated_at descending (newest first)
    results.sort(key=lambda r: r.get("updated_at", ""), reverse=True)
    return results


def save_api_key(
    user_id: str,
    provider: str,
    api_key: str,
    api_base: str,
    model: str = "",
    key_id: str = "",
    last_test_success: Optional[bool] = None,
) -> str:
    """Save or update an API key.

    - If key_id is provided, update that specific entry (for editing);
      if api_key is empty, keep the existing key unchanged.
    - If key_id is empty, create a new entry.

    Returns the key_id of the saved entry.
    """
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = _migrate_entries(_read_all_lines())

    if key_id:
        for entry in entries:
            if entry.get("user_id") == user_id and entry.get("key_id") == key_id:
                if api_key.strip():
                    entry["api_key"] = api_key
                entry["api_base"] = api_base
                entry["model"] = model or entry.get("model", "")
                entry["updated_at"] = now
                if last_test_success is not None:
                    entry["last_test_success"] = last_test_success
                _write_all_lines(entries)
                return key_id
        key_id = ""

    new_id = _generate_key_id()
    entries.append({
        "key_id": new_id,
        "user_id": user_id,
        "provider": provider,
        "api_key": api_key,
        "api_base": api_base,
        "model": model,
        "is_active": True,
        "updated_at": now,
        "last_test_success": last_test_success,
    })
    _write_all_lines(entries)
    return new_id


def delete_api_key(user_id: str, key_id: str) -> None:
    """Delete an API key entry by its unique key_id."""
    entries = _migrate_entries(_read_all_lines())
    entries = [
        e for e in entries
        if not (e.get("user_id") == user_id and e.get("key_id") == key_id)
    ]
    _write_all_lines(entries)


def get_active_api_keys(user_id: str) -> list[dict]:
    """Return all active API keys for a user (with full unmasked keys).

    Returns a list of dicts with: key_id, provider, api_key, api_base, model.
    """
    all_entries = _migrate_entries(_read_all_lines())
    results = []
    for entry in all_entries:
        if entry.get("user_id") == user_id and entry.get("is_active", False):
            results.append({
                "key_id": entry.get("key_id", ""),
                "provider": entry.get("provider", ""),
                "api_key": entry.get("api_key", ""),
                "api_base": entry.get("api_base", ""),
                "model": entry.get("model", ""),
            })
    return results


def toggle_api_key(user_id: str, key_id: str) -> dict:
    """Toggle the is_active flag for a given entry by key_id.

    Returns {"success": bool, "is_active": bool}.
    """
    entries = _migrate_entries(_read_all_lines())
    target_found = False
    new_active = False

    for entry in entries:
        if entry.get("user_id") == user_id and entry.get("key_id") == key_id:
            current = entry.get("is_active", False)
            new_active = not current
            entry["is_active"] = new_active
            entry["updated_at"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            target_found = True
            break

    if not target_found:
        return {"success": False, "is_active": False}

    _write_all_lines(entries)
    return {"success": True, "is_active": new_active}


def test_api_key(provider: str, api_key: str, api_base: str, model: str = "") -> dict:
    """Test connectivity for a given API key by making a lightweight API call.

    Returns {"success": bool, "message": str}.
    """
    import httpx

    base = api_base.rstrip("/") if api_base else "https://api.openai.com/v1"
    url = f"{base}/chat/completions"

    test_model = model.strip() if model else "gpt-3.5-turbo"
    payload = {
        "model": test_model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
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
