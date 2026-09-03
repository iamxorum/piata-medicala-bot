import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

STATE_PATH = DATA_DIR / "state.json"
SUBSCRIBERS_PATH = DATA_DIR / "subscribers.json"


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"seen_ids": [], "first_run_done": False}


def save_state(state: dict, max_seen_ids: int) -> None:
    state["seen_ids"] = state["seen_ids"][-max_seen_ids:]
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def load_subscribers() -> dict:
    if SUBSCRIBERS_PATH.exists():
        return json.loads(SUBSCRIBERS_PATH.read_text(encoding="utf-8"))
    return {"chat_ids": [], "update_offset": 0}


def save_subscribers(subscribers: dict) -> None:
    SUBSCRIBERS_PATH.write_text(json.dumps(subscribers, indent=2, ensure_ascii=False), encoding="utf-8")
