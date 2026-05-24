from typing import Optional
from local_backend.database.code.operations.database_api_key_operations import ApiKeyOperations, _mask_api_key as _mask


_ops = ApiKeyOperations()


def list_api_keys(user_id: str) -> list[dict]:
    rows = _ops.list_for_user(user_id)
    results = []
    for r in rows:
        full = _ops.get_full(r["key_id"])
        results.append({
            "key_id": r.get("key_id", ""),
            "provider": r.get("provider", ""),
            "api_key_masked": _mask(full["api_key"]) if full else "",
            "api_base": r.get("api_base", ""),
            "model": r.get("model", ""),
            "is_active": bool(r.get("is_active", False)),
            "updated_at": r.get("updated_at", ""),
            "last_test_success": r.get("last_test_success"),
        })
    results.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
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
    if key_id:
        existing = _ops.get(key_id)
        if existing and existing.get("user_id") == user_id:
            _ops.update(
                key_id,
                provider=provider,
                api_key_plain=api_key.strip() or None,
                api_base=api_base,
                model=model,
                last_test_success=1 if last_test_success else 0 if last_test_success is not None else None,
            )
            return key_id
        key_id = ""
    return _ops.create(user_id, provider, api_key, api_base, model, key_id)


def delete_api_key(user_id: str, key_id: str) -> None:
    existing = _ops.get(key_id)
    if existing and existing.get("user_id") == user_id:
        _ops.delete(key_id)


def get_active_api_keys(user_id: str) -> list[dict]:
    return _ops.get_active(user_id)


def toggle_api_key(user_id: str, key_id: str) -> dict:
    existing = _ops.get(key_id)
    if not existing or existing.get("user_id") != user_id:
        return {"success": False, "is_active": False}
    new_active = 0 if existing.get("is_active") else 1
    _ops.update(key_id, is_active=new_active)
    return {"success": True, "is_active": bool(new_active)}


def test_api_key(provider: str, api_key: str, api_base: str, model: str = "") -> dict:
    return _ops.test(provider, api_key, api_base, model)
