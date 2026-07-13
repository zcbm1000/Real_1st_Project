from flask import Blueprint, render_template, request, redirect, session, url_for, jsonify
from utils.json_manager import load_members, save_members
from email.message import EmailMessage
from datetime import datetime
import random
import smtplib
import os


auth_bp = Blueprint("auth", __name__, url_prefix="/member")

# 로그인 START
# 로그인 화면 불러오는 작업
@auth_bp.route("/signin_form")
def signin_form():
    if session.get("signinedMemberId"):
        return redirect("/")
    return render_template("member/signin_form.html")


@auth_bp.route("/signin", methods=["POST"])
def signin():
    # 사용자가 입력한 값 불러오기 만일 없을경우 빈공백으로 처리, 
    # strip는 불필요한 공백 및 특정문자 제거할때 이용
    m_id = request.form.get("mId", "").strip()
    m_pw = request.form.get("mPw", "").strip()

    # 멤버로드 한뒤 id 값 가지고 오기
    members = load_members()
    member  = members.get(m_id)

    # 멤버 안에있는 패스워드 값이 틀릴경우 메세지를 날림
    # 파이선 데이터를 JSON 형태의 응답으로 변환하는 함수 jsonify()
    if not member or member.get("pw") != m_pw:
        return jsonify({"success": False, "message": "id_pw_mismatch"})

    # 세션에 사용자가 입력한 값을 넣는 과정
    session["signinedMemberId"]   = m_id
    session["signinedMemberName"] = member.get("name", m_id)
    session["signinedMemberRole"] = member.get("role", "user")

    # 멤버에서 approved 값이 False일경우 해당 주소의 경로로 이동
    if not member.get("approved", False):
        return jsonify({"success": True, "redirect": "/?pending=1"})

    # 멤버에서 꺼내온 값이 어드민일경우 다른 페이지로 이동하지말고 그대로 대기
    if member.get("role") == "admin":
        return jsonify({"success": True, "redirect": "stay"})

    # 그게 둘다 아닐경우 메인홈페이지로 이동
    return jsonify({"success": True, "redirect": "/"})
# 로그인 END

# 회원가입 START
# 회원가입 화면 불러오는 작업
@auth_bp.route("/signup_form")
def signup_form():
    return render_template("member/signup_form.html")


@auth_bp.route("/signup", methods=["POST"])
def signup():
    # 사용자가 입력한 값을 가져오는 작업
    m_id    = request.form.get("mId",    "").strip()
    m_pw    = request.form.get("mPw",    "").strip()
    m_pw2   = request.form.get("mPw2",   "").strip()
    m_name  = request.form.get("mName",  "").strip()
    m_email = request.form.get("mEmail", "").strip()
    m_phone = request.form.get("mPhone", "").strip()

    # 멤버 로드 작업
    members = load_members()

    # 입력한 아이디가 중복일경우
    if m_id in members:
        return render_template("member/signup_form.html", error="이미 사용 중인 ID입니다.")
    
    # 입력한 비밀번호가 맞지 않을경우
    if m_pw != m_pw2:
        return render_template("member/signup_form.html", error="비밀번호가 일치하지 않습니다.")
    # 하나라도 입력되지않았으면
    if not all([m_id, m_pw, m_name, m_email, m_phone]):
        return render_template("member/signup_form.html", error="모든 항목을 입력해 주세요.")

    # 해당 형태로 json으로 저장하는 방식
    members[m_id] = {
        "pw":       m_pw,
        "name":     m_name,
        "email":    m_email,
        "phone":    m_phone,
        "role":     "user",
        "approved": False,
    }
    # 데이터 저장
    save_members(members)
    return redirect("/?signup_success=1")


@auth_bp.route("/check_id", methods=["POST"])
def check_id():
    # 사용자가 입력한 아이디를 가지고오고 json에있는 데이터를 로드한뒤,
    # 중복점검을 함
    m_id    = request.form.get("mId", "").strip()
    members = load_members()
    # bool 값을 참(True)이나 거짓(False)으로 바꾸는 도구.
    return jsonify({"available": m_id not in members and bool(m_id)})
# 회원가입 END

# 회원수정 START
@auth_bp.route("/modify_form")
def modify_form():
    # 현재 로그인한 정보를 가져오는 작업
    member_id = session.get("signinedMemberId")
    
    # 로그인한 상태가 아니라면 해당 주소로 이동
    if not member_id:
        return redirect(url_for("auth.signin_form"))
    
    # 멤버 목록을 로드
    members = load_members()
    # 로그인한 정보가 목록에 잇는지 확인
    # 회원 정보를 가져오고, 없으면 빈 딕셔너리를 반환
    member  = members.get(member_id, {})
    return render_template("member/modify_form.html", member=member, member_id=member_id)


@auth_bp.route("/modify", methods=["POST"])
def modify():
    # 현재 로그인한 정보를 가져오는 작업
    member_id = session.get("signinedMemberId")
    # 로그인한 상태가 아니라면 해당 주소로 이동
    if not member_id:
        return redirect(url_for("auth.signin_form"))

    # 사용자가 입력한 값을 가져옴
    m_pw    = request.form.get("mPw",    "").strip()
    m_email = request.form.get("mEmail", "").strip()
    m_phone = request.form.get("mPhone", "").strip()

    # 멤버 목록을 로드
    members = load_members()
    # 로그인한 정보가 목록에 잇는지 확인
    # {} 명부에서 그 아이디를 찾기 못햇다면 비어있는정보를 빽
    member  = members.get(member_id, {})

    # 사용자가 입력한 값을 바꿈
    if m_pw:
        member["pw"] = m_pw
    if m_email:
        member["email"] = m_email
    if m_phone:
        member["phone"] = m_phone

    # 수정한 정보는 전체 회원 정부에 다시 저장을 하나,
    # 현재 로그인되어잇는 사람의 정보만 업데이트 함
    members[member_id] = member
    # 해당 내용을 저장
    save_members(members)
    return jsonify({"success": True, "message": "정보가 변경되었습니다."})
# 회원수정 END

# 로그아웃 START
@auth_bp.route("/signout")
def signout():
    session.clear()
    return redirect("/")
# 로그아웃 END

# 회원찾기 START
# 더이상 필요없는 임시 인증데이터들을 서버의 기억을 지우는 함수
def clear_auth_session():
    # 데이터를 리스트값으로 담기
    keys = ['is_email_verified', 'verified_email', 'otp', 'otp_email', 'otp_time']
    # 반복문을 돌려서 지우기 시작
    for key in keys:
        session.pop(key, None)

# 아이디 찾기 화면을 불러오는 작업
@auth_bp.route('/id_find_form')
def id_find_form():
    clear_auth_session()
    return render_template('member/id_find_form.html')

# 비밀번호 찾기 화면을 불러오는 작업
@auth_bp.route('/pw_find_form')
def pw_find_form():
    clear_auth_session()
    return render_template('member/pw_find_form.html')


@auth_bp.route('/send_verification', methods=['POST'])
def send_verification():

    clear_auth_session()

    # 사용자가 입력한 이메일 찾기
    email_to = request.form.get('mMail')

    # 이메일 주소가 없다면 메세지창 확인
    if not email_to:
        return jsonify({"status": "error", "message": "이메일 주소가 없습니다."})

    # 0~9 사이의 숫자 6개를 무작위로 생성하여 하나의 인증번호(opt)로 만듦
    otp = ''.join(str(random.randint(0, 9)) for _ in range(6))

    # 세션에 저장 하는 작업
    session['otp'] = otp    # 검증용 OTP 값
    session['otp_email'] = email_to     # OTP를 보낸 대상 이메일 (나중에 인증 시 이 이메일과 일치하는지 확인하기 위함)
    session['otp_time'] = datetime.now().timestamp()    # 생성 시간을 타임스탬프(숫자)로 저장하여, 나중에 만료 시간을 확인

    # 이메일내용을 담을 하나의 EmailMessage 객체 생성
    otpMail = EmailMessage()
    otpMail['Subject'] = "이메일 인증 번호 안내"
    otpMail['To'] = email_to
    # 이메일 본문 내용를 집어넣는 set_content() 함수
    otpMail.set_content(f"당신의 인증번호는 [{otp}] 입니다.")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(
                os.getenv('EMAIL_ID'),
                os.getenv('EMAIL_PASSWORD')
                )
            server.send_message(otpMail)
        return jsonify({"status": "success", "message": "인증번호가 발송되었습니다."})
    except Exception as e:
        print("메일 발송 에러 :", e)
        return jsonify({"status": "error", "message": "메일 발송에 실패했습니다."})


@auth_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    # 사용자가 입력한 정보 가져오는 작업
    user_email = request.form.get('mMail')
    user_otp = request.form.get('otp')

    # 유효성 검사
    if not user_email or not user_otp:
        return jsonify({"status": "error", "message": "데이터가 누락되었습니다."})

    # 담아두었던 세션 가져오는 작업
    saved_otp = session.get('otp')
    saved_email = session.get('otp_email')
    saved_time = session.get('otp_time')

    # 시간이 만료될경우 에러 메세지 확인
    if not saved_time or datetime.now().timestamp() - saved_time > 180:
        return jsonify({"status": "error", "message": "인증번호가 만료되었습니다."})

    # strip() 공백제거 함수
    if saved_otp and saved_email == user_email and str(saved_otp) == str(user_otp).strip():
        # 세션에 담는 작업
        session['is_email_verified'] = True
        session['verified_email'] = user_email
        # 인증관련 세션 데이터를 삭제 (없으면 none를 반환)
        session.pop('otp', None)
        session.pop('otp_email', None)
        session.pop('otp_time', None)
        return jsonify({"status": "success", "message": "인증에 성공했습니다."})

    return jsonify({"status": "error", "message": "인증번호가 일치하지 않습니다."})


@auth_bp.route('/id_find_confirm', methods=['POST'])
def id_find_confirm():
    # 세션에 데이터가 없을경우
    if not session.get('is_email_verified'):
        return "<script>alert('이메일 인증이 필요합니다.'); history.back();</script>"
    # 유저가 입력한 값가져오는 작업
    user_name = request.form.get('mName', '').strip()
    user_email = request.form.get('mMail', '').strip()

    # 이메일이 틀릴경우 해당 메세지 팝업
    if session.get('verified_email') != user_email:
        return "<script>alert('인증한 이메일과 입력한 이메일이 다릅니다.'); history.back();</script>"

    # 멤버 로드
    members = load_members()
    # 아직 회원을 찾지 못한 상태이므로 None으로 초기화
    found_id = None
    # 회원을 찾는 작업
    # items() 딕셔너리 의 key 와 value를 함께 가져오는 메서드
    for m_id, member in members.items():
        if member.get('name') == user_name and member.get('email') == user_email:
            found_id = m_id
            break

    if found_id:
        return render_template('member/id_find_result.html', found_id=found_id)

    return "<script>alert('일치하는 회원 정보가 없습니다.'); history.back();</script>"


@auth_bp.route('/pw_find_confirm', methods=['POST'])
def pw_find_confirm():

    # 세션에 데이터가 없을경우
    if not session.get('is_email_verified'):
        return "<script>alert('이메일 인증이 필요합니다.'); history.back();</script>"

    # 유저가 입력한 값가져오는 작업
    user_id = request.form.get('mId', '').strip()
    user_name = request.form.get('mName', '').strip()
    user_email = request.form.get('mMail', '').strip()

    # 이메일이 틀릴경우 해당 메세지 팝업
    if session.get('verified_email') != user_email:
        return "<script>alert('인증한 이메일과 입력한 이메일이 다릅니다.'); history.back();</script>"
    
    # 멤버 로드
    members = load_members()
    # 사용자가 입력한 데이터를 가져오는 작업
    member = members.get(user_id)

    # 회원정보가 존재하고 이름,이메일 모두 일치하면 True
    user_exists = bool(member) and member.get('name') == user_name and member.get('email') == user_email

    if user_exists:
        return render_template('member/pw_reset_form.html', mId=user_id)

    return "<script>alert('일치하는 회원 정보가 없습니다.'); history.back();</script>"


@auth_bp.route('/pw_reset', methods=['POST'])
def pw_reset():

    # 세션에 데이터가 없을경우
    if not session.get('is_email_verified'):
        return "<script>alert('이메일 인증이 필요합니다.'); history.back();</script>"

    # 유저가 입력한 값을 가져오는 작업
    user_id = request.form.get('mId', '').strip()
    m_pw    = request.form.get('mPw', '').strip()
    m_pw2   = request.form.get('mPw2', '').strip()

    # 멤버 로드 하고  id값만 가져오는 작업
    members = load_members()
    member  = members.get(user_id)

    if not member:
        return "<script>alert('일치하는 회원 정보가 없습니다.'); history.back();</script>"
    if not m_pw or m_pw != m_pw2:
        return "<script>alert('비밀번호가 일치하지 않습니다.'); history.back();</script>"

    # 새 비밀번호로 변경한후 회원정보에 다시 저장
    member['pw'] = m_pw
    members[user_id] = member
    save_members(members)

    # 데이터는 pop로 지움
    session.pop('is_email_verified', None)
    session.pop('verified_email', None)

    return "<script>alert('비밀번호가 변경되었습니다. 다시 로그인해주세요.'); location.href='/member/signin_form';</script>"
# 회원찾기 END