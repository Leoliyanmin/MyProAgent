import datetime
from typing import Optional, Dict

from local_backend.database.code.command.database_command import (
    get_user_setting,
    upsert_user_setting,
)


class UserSettingOperations:
    def get(self, user_id: str) -> Optional[Dict]:
        return get_user_setting(user_id)

    def save(self, user_id: str, **kwargs) -> None:
        upsert_user_setting(user_id, **kwargs)
