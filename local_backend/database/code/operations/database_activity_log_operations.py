from local_backend.database.code.command.database_command import (
    upsert_activity_log,
    upsert_activity_logs_batch,
    list_activity_logs,
)


class ActivityLogOperations:

    def record(self, user_id: str, log_date: str, hour: int, count: int = 1) -> None:
        upsert_activity_log(user_id, log_date, hour, count)

    def record_batch(self, user_id: str, logs: list[dict]) -> None:
        if not logs:
            return
        upsert_activity_logs_batch(logs, user_id)

    def query(self, user_id: str, from_date: str | None = None, to_date: str | None = None) -> list[dict]:
        return list_activity_logs(user_id, from_date, to_date)

    def get_heatmap(self, user_id: str, from_date: str | None = None, to_date: str | None = None) -> dict:
        """
        Return aggregated heatmap data: { 'YYYY-MM-DD': { hour: count } }
        """
        rows = self.query(user_id, from_date, to_date)
        result = {}
        for row in rows:
            date = row["log_date"]
            hour = row["hour"]
            count = row["count"]
            if date not in result:
                result[date] = {}
            result[date][hour] = count
        return result
