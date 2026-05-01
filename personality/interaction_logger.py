import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class InteractionLogger:
    def __init__(self, log_dir: Optional[Path] = None):
        if log_dir is None:
            log_dir = Path(__file__).parent / "interactions"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_interaction(self, interaction_data: Dict[str, Any]) -> str:
        conversation_id = str(uuid.uuid4())
        interaction_data.setdefault("metadata", {})
        interaction_data["metadata"]["conversation_id"] = conversation_id
        interaction_data["metadata"]["timestamp"] = datetime.now().isoformat()

        log_file = self.log_dir / f"{conversation_id}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(interaction_data, f, ensure_ascii=False, indent=2)

        return conversation_id

    def get_interaction(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        log_file = self.log_dir / f"{conversation_id}.json"
        if not log_file.exists():
            return None
        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_user_interactions(self, user_id: str, limit: int = 100) -> list:
        interactions = []
        for log_file in self.log_dir.glob("*.json"):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("metadata", {}).get("user_id") == user_id:
                        interactions.append(data)
            except (json.JSONDecodeError, IOError):
                continue
        interactions.sort(
            key=lambda x: x.get("metadata", {}).get("timestamp", ""),
            reverse=True
        )
        return interactions[:limit]

    def delete_interaction(self, conversation_id: str) -> bool:
        log_file = self.log_dir / f"{conversation_id}.json"
        if log_file.exists():
            log_file.unlink()
            return True
        return False
