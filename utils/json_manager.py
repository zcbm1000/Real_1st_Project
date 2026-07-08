import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MEMBER_FILE       = os.path.join(BASE_DIR, "db", "members.json")

# ── Members ──────────────────────────────────────
def load_members():
    try:
        if not os.path.exists(MEMBER_FILE):
            return {}
        with open(MEMBER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading members:", e)
        return {}

def save_members(members):
    try:
        os.makedirs(os.path.dirname(MEMBER_FILE), exist_ok=True)
        with open(MEMBER_FILE, "w", encoding="utf-8") as f:
            json.dump(members, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Error saving members:", e)

def get_approved_members_with_contact():
    members = load_members()
    return [
        {"id": mid, **info}
        for mid, info in members.items()
        if info.get("approved", False)
    ]