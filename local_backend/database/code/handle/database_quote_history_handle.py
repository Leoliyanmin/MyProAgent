from local_backend.database.code.operations.database_quote_history_operations import (
    insert_quote_history,
    get_history_by_date,
)


class QuoteHistoryHandle:

    def add(self, user_id: str, quote_text: str, source: str = "custom",
            quote_author: str = "", quote_from: str = "") -> dict:
        try:
            insert_quote_history(user_id, quote_text, source, quote_author, quote_from)
            return {"ok": True, "status": 200, "message": "已记录"}
        except Exception as e:
            return {"ok": False, "status": 500, "message": str(e)}

    def get_by_date(self, user_id: str, date: str | None = None) -> dict:
        try:
            rows = get_history_by_date(user_id, date)
            return {"ok": True, "status": 200, "data": rows}
        except Exception as e:
            return {"ok": False, "status": 500, "message": str(e)}
