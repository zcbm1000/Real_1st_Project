import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FIRE_LOG_FILE     = os.path.join(BASE_DIR, "db", "fire_logs.json")

# ── Fire Logs ─────────────────────────────────────
def load_fire_logs():
    try:
        if not os.path.exists(FIRE_LOG_FILE):
            return []
        with open(FIRE_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading fire logs:", e)
        return []

def save_fire_logs(logs):
    try:
        os.makedirs(os.path.dirname(FIRE_LOG_FILE), exist_ok=True)
        with open(FIRE_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Error saving fire logs:", e)

def get_next_log_id():
    logs = load_fire_logs()
    if not logs:
        return 1
    return max(l.get("id", 0) for l in logs) + 1
