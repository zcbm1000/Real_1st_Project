from flask import Blueprint, render_template, redirect, url_for, session
from utils.notices_Json_manager import load_notices

notice_bp = Blueprint("notice", __name__, url_prefix="/notice")

# pinned 값 True 맨위에 고정 시켜주는것 / false 일반글
@notice_bp.route("/")
def list_notices():
    notices = load_notices()  # 노션 제이슨 불러오는것
    pinned  = [n for n in notices if n.get("pinned")]   # 반복문을 돌려 패딩값을 가져옴
    regular = sorted(
        [n for n in notices if not n.get("pinned")],
        key=lambda x: x["id"], reverse=True
    )
    return render_template("notice/list.html", notices=pinned + regular)


@notice_bp.route("/<int:notice_id>")
def detail(notice_id):
    notices = load_notices()
    notice  = next((n for n in notices if n["id"] == notice_id), None)
    if not notice:
        return redirect(url_for("notice.list_notices"))
    return render_template("notice/detail.html", notice=notice)
