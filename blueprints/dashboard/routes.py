from flask import Blueprint, render_template, Response, jsonify, session, redirect, url_for, request
from ai.camera_manager import get_frame, get_raw_frame, get_shared_frame, get_no_signal_frame
from utils.fire_Json_manager import load_fire_logs
from datetime import datetime, timedelta
import cv2
import requests
import time

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def generate_frames(camera_num, ai=True):

    while True:

        if ai:
            frame = get_frame(camera_num)
        else:
            frame = get_raw_frame(camera_num)

        if frame is None:
            frame = get_no_signal_frame()

        try:
            success, buffer = cv2.imencode(
                ".jpg",
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, 80]
            )

            if not success:
                print("[ERROR] imencode 실패")
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )

        except Exception as e:
            print("Frame encode error:", e)
            continue

        time.sleep(0.05)


@dashboard_bp.route("/video_feed/<int:camera_num>")
def video_feed(camera_num):
    return Response(
        generate_frames(camera_num, ai=True),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@dashboard_bp.route("/camera_feed/<int:camera_num>")
def camera_feed(camera_num):
    def generate():
        while True:
            frame = get_shared_frame(camera_num)
            if frame is None: continue
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@dashboard_bp.route("/monitor")
def monitor():
    return render_template("dashboard/monitor.html")

@dashboard_bp.route("/history")
def history():
    return render_template("dashboard/history.html")

@dashboard_bp.route("/log_detail/<int:log_id>")
def log_detail(log_id):
    logs = load_fire_logs()

    target_log = None
    for log in logs:
        if log.get("id") == log_id:
            target_log = log
            break

    if target_log is None:
        return "로그를 찾을 수 없습니다.", 404

    return render_template(
        "dashboard/log_detail.html",
        log=target_log
    )

# ── API ──────────────────────────────────────────────
@dashboard_bp.route("/api/logs")
def api_logs():
    """전체 로그 — 최신순, 필터 지원"""
    logs     = load_fire_logs()
    district = request.args.get("district") or request.args.get("drone")
    log_type = request.args.get("type")
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per", 10))

    if district and district != "all":
        logs = [l for l in logs if district in l.get("location", "")]
    if log_type and log_type != "all":
        logs = [l for l in logs if l.get("type") == log_type]

    logs.sort(key=lambda x: x.get("time", ""), reverse=True)

    total   = len(logs)
    start   = (page - 1) * per_page
    end     = start + per_page
    paged   = logs[start:end]

    return jsonify({"total": total, "page": page, "per_page": per_page, "logs": paged})


@dashboard_bp.route("/api/recent_logs")
def api_recent_logs():
    """관제 화면 최근 로그 10개"""
    logs = load_fire_logs()
    logs.sort(key=lambda x: x.get("time", ""), reverse=True)
    return jsonify(logs[:10])


@dashboard_bp.route("/api/latest_alert")
def api_latest_alert():
    """최신 화재 알림 — 7초 이내 발생한 항목"""
    logs = load_fire_logs()
    if not logs:
        return jsonify({"alert": False})
    logs.sort(key=lambda x: x.get("time", ""), reverse=True)
    latest = logs[0]
    try:
        log_time = datetime.strptime(latest["time"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() - log_time <= timedelta(seconds=7):
            return jsonify({"alert": True, "log": latest})
    except Exception:
        pass
    return jsonify({"alert": False})


@dashboard_bp.route("/api/stats")
def api_stats():
    """통계 데이터"""
    logs        = load_fire_logs()
    fire_count  = sum(1 for l in logs if l.get("type") == "화재")
    smoke_count = sum(1 for l in logs if l.get("type") == "연기")
    return jsonify({
        "total":  len(logs),
        "fire":   fire_count,
        "smoke":  smoke_count,
    })


# ── Discord 전송 뼈대 ──────────────────────────
@dashboard_bp.route("/api/send_discord", methods=["POST"])
def api_send_discord():
    WEBHOOK_URL = "https://discordapp.com/api/webhooks/1521402162247110708/dosKCCC0mVLCe0mbeVTCExC5W7HxyZaP8nEv8qAPNTNXbmIgGUQdKpBaruQ_Ig5b08Wl"

    data = request.get_json()
    received_row_key = data.get("log_id") 
    all_logs = load_fire_logs()

    target_log = None
    for log in all_logs:
        log_key = f"{log.get('drone_id')}_{log.get('time')}"
        if log_key == received_row_key:
            target_log = log
            break

    print(f"DEBUG: 전체 로그 데이터 구조 확인: {all_logs}")
    if not target_log:
        print(f"DEBUG: 일치하는 로그 없음. 검색 시도한 키: {received_row_key}")
        return jsonify({"success": False, "message": "로그 데이터를 찾을 수 없습니다."}), 404

    message = f"------드론 탐지 알림------\n- 위치: {target_log.get('location')}\n- 유형: {target_log.get('type')}"
    response = requests.post(WEBHOOK_URL, json={"content": message})
    
    return jsonify({"success": True, "message": f"Discord 전송 완료 (Log #{response.status_code})"})
