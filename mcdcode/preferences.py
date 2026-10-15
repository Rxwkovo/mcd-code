"""Local evidence for the host's taste memory; no inferred tastes or MCP writes."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import tempfile

from .service import DataError


class PreferenceMemory:
    def __init__(self, root: Path):
        self.path = Path(root) / ".local" / "preferences.json"

    def load(self):
        if not self.path.exists():
            return {"schema_version": 1, "enabled": True, "notes": [], "order_choices": []}
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
            if (not isinstance(state, dict) or state.get("schema_version") != 1
                    or not isinstance(state.get("enabled"), bool)
                    or not isinstance(state.get("notes"), list)
                    or not all(isinstance(note, str) for note in state["notes"])
                    or not isinstance(state.get("order_choices"), list)
                    or not all(isinstance(choice, dict)
                               and isinstance(choice.get("order_key"), str)
                               and isinstance(choice.get("items"), list)
                               and all(isinstance(item, dict) and isinstance(item.get("name"), str)
                                       and type(item.get("quantity")) is int and item["quantity"] > 0
                                       for item in choice["items"])
                               for choice in state["order_choices"])):
                raise ValueError("invalid memory")
            return state
        except (OSError, ValueError):
            raise DataError("偏好记录暂时无法读取；请检查本机文件，不会覆盖原记录。") from None

    def save(self, state):
        state["updated_at"] = datetime.now(timezone(timedelta(hours=8))).isoformat()
        text = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
        token = os.environ.get("MCD_TOKEN")
        if token and token in text:
            raise DataError("偏好内容含凭据，未保存。")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             prefix="preferences-", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(text)
            os.replace(temporary, self.path)
        finally:
            if temporary and temporary.exists():
                temporary.unlink()
        return state

    def update(self, action, text=""):
        text = text.strip()
        state = self.load()
        if action == "清空":
            state = {"schema_version": 1, "enabled": False, "notes": [], "order_choices": []}
        elif action in ("暂停", "恢复"):
            state["enabled"] = action == "恢复"
        elif action == "记住" and text.strip():
            if text.strip() not in state["notes"]:
                state["notes"].append(text.strip())
        elif action == "忘掉" and text.strip():
            state["notes"] = [note for note in state["notes"] if text not in note]
            choices = []
            for choice in state["order_choices"]:
                items = [item for item in choice.get("items", []) if text not in item.get("name", "")]
                if items:
                    choices.append({**choice, "items": items})
            state["order_choices"] = choices
        else:
            raise DataError("用法：/偏好 [记住 内容|忘掉 关键词|暂停|恢复|清空]")
        return self.save(state)

    def record_order(self, order_id, items):
        """Call only after a successful confirmed create-order; never import history."""
        state = self.load()
        if not state["enabled"]:
            return False
        key = hashlib.sha256(str(order_id).encode("utf-8")).hexdigest()
        if any(choice.get("order_key") == key for choice in state["order_choices"]):
            return False
        observed = [{"name": item["name"], "quantity": item["quantity"]} for item in items
                    if isinstance(item.get("name"), str) and item["name"]
                    and type(item.get("quantity")) is int and item["quantity"] > 0]
        if not observed:
            return False
        state["order_choices"].append({
            "order_key": key,
            "observed_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
            "source": "confirmed_create_order", "payment_status": "unverified", "items": observed,
        })
        self.save(state)
        return True
