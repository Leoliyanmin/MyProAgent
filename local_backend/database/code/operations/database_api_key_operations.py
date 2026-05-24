import json
import uuid
import datetime
from local_backend.database.code.command.database_command import (
    create_api_key,
    list_api_keys_by_user,
    get_api_key,
    update_api_key,
    delete_api_key,
    get_active_api_keys,
    get_api_key_by_id,
)


def _generate_key_id() -> str:
    ts_hex = hex(int(datetime.datetime.utcnow().timestamp() * 1000))[2:]
    rand_hex = uuid.uuid4().hex[:8]
    return f"{ts_hex}_{rand_hex}"


def _mask_api_key(key: str) -> str:
    if not key or len(key) <= 8:
        return key or ""
    return key[:4] + "\u2022\u2022\u2022\u2022" + key[-4:]


class ApiKeyOperations:

    def create(self, user_id: str, provider: str, api_key_plain: str,
               api_base: str, model: str = "", key_id: str = "") -> str:
        if not key_id:
            key_id = _generate_key_id()
        create_api_key(user_id, key_id, provider, api_key_plain, api_base, model)
        return key_id

    def list_for_user(self, user_id: str) -> list[dict]:
        rows = list_api_keys_by_user(user_id)
        for r in rows:
            r["api_key_masked"] = _mask_api_key(
                get_api_key_by_id(r["key_id"]).get("api_key", "") if get_api_key_by_id(r["key_id"]) else ""
            )
        return rows

    def get(self, key_id: str) -> dict | None:
        return get_api_key(key_id)

    def update(self, key_id: str, **kwargs) -> None:
        mapping = {
            "provider": "provider", "api_key_plain": "api_key_plain",
            "api_base": "api_base", "model": "model",
            "is_active": "is_active", "last_test_success": "last_test_success",
        }
        params = {mapping[k]: v for k, v in kwargs.items() if k in mapping and v is not None}
        if params:
            update_api_key(key_id, **params)

    def delete(self, key_id: str) -> None:
        delete_api_key(key_id)

    def get_active(self, user_id: str) -> list[dict]:
        return get_active_api_keys(user_id)

    def get_full(self, key_id: str) -> dict | None:
        return get_api_key_by_id(key_id)

    def test(self, provider: str, api_key: str, api_base: str, model: str = "") -> dict:
        import httpx
        base = api_base.rstrip("/") if api_base else "https://api.openai.com/v1"
        url = f"{base}/chat/completions"
        test_model = model.strip() if model else "gpt-3.5-turbo"
        payload = {
            "model": test_model,
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 1,
        }
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    return {"success": True, "message": f"{provider} \u8fde\u63a5\u6210\u529f"}
                elif resp.status_code == 401:
                    return {"success": False, "message": "API Key \u65e0\u6548 (401 Unauthorized)"}
                elif resp.status_code == 403:
                    return {"success": False, "message": "API Key \u6743\u9650\u4e0d\u8db3 (403 Forbidden)"}
                elif resp.status_code == 429:
                    return {"success": False, "message": "\u8bf7\u6c42\u8fc7\u4e8e\u9891\u7e41 (429)\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5"}
                else:
                    return {"success": False, "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except httpx.ConnectError:
            return {"success": False, "message": f"\u65e0\u6cd5\u8fde\u63a5\u5230 {base}\uff0c\u8bf7\u68c0\u67e5 API Base URL"}
        except httpx.ReadTimeout:
            return {"success": False, "message": "\u8fde\u63a5\u8d85\u65f6\uff0c\u8bf7\u68c0\u67e5\u7f51\u7edc\u6216 API Base URL"}
        except Exception as e:
            return {"success": False, "message": f"\u6d4b\u8bd5\u5931\u8d25: {type(e).__name__}: {e}"}
