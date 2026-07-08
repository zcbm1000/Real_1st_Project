import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
NOTICE_FILE       = os.path.join(BASE_DIR, "db", "notices.json")

# ── Notices ───────────────────────────────────────
def load_notices():
    try:
        if not os.path.exists(NOTICE_FILE):
            return []
        with open(NOTICE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading notices:", e)
        return []

def save_notices(notices):
    try:
        os.makedirs(os.path.dirname(NOTICE_FILE), exist_ok=True)
        with open(NOTICE_FILE, "w", encoding="utf-8") as f:
            json.dump(notices, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Error saving notices:", e)

def get_next_notice_id():
    notices = load_notices()
    if not notices:
        return 1
    return max(n.get("id", 0) for n in notices) + 1
