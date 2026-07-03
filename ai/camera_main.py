import cv2
from ultralytics import YOLO
import os
import time

# ====================== 설정 ======================
# 모델 경로 (현재 프로젝트 구조에 맞춰 수정)
MODEL_PATH = 'runs/detect/train-15/weights/best.pt'  # 👈 아까 완료된 train-15 경로로 반영했습니다.

ESP32_URL = "http://192.168.137.104:81/stream"
CONFIDENCE_THRESHOLD = 0.20

# ☀️ 렌즈 밝기 및 대비 설정
BRIGHTNESS = 0    
CONTRAST = 1.0      
# =================================================

print("🔥 Fire & Smoke Detection (수동 수집 버전) 시작...")

# 모델 로드
print("📦 모델 로드 중...")
model = YOLO(MODEL_PATH)
print(f"✅ 모델 로드 완료! ({MODEL_PATH})")

# ESP32 카메라 연결
print("📷 ESP32 카메라 연결 시도...")
cap = cv2.VideoCapture(ESP32_URL)

if not cap.isOpened():
    print("❌ ESP32 연결 실패!")
    print("   1. ESP32가 WiFi에 잘 연결되어 있는지")
    print("   2. IP 주소 확인 (192.168.137.245)")
    print("   3. 브라우저에서 http://192.168.137.104:81/stream 열리는지 테스트")
    exit()

print("✅ ESP32 카메라 연결 성공!")
print("📢 [S] 키를 누르면 수동으로 캡처본이 저장됩니다. (종료는 [Q] 키)")

start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ 프레임 읽기 실패... 재시도")
        time.sleep(1)
        continue

    # 영상 밝기/대비 보정
    adjusted_frame = cv2.convertScaleAbs(frame, alpha=CONTRAST, beta=BRIGHTNESS)

    # YOLO 추론
    results = model(adjusted_frame, conf=CONFIDENCE_THRESHOLD, verbose=False)

    # ❌ [자동 저장 코드 구역 완전 삭제 완료] ❌
    
    # 결과 화면에 그리기
    annotated_frame = results[0].plot()

    # FPS 표시
    fps = int(1 / (time.time() - start_time)) if 'start_time' in locals() else 0
    cv2.putText(annotated_frame, f"FPS: {fps}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
    start_time = time.time()

    # 화면 창 표시
    cv2.imshow("Fire & Smoke Detection - ESP32", annotated_frame)

    # 입력된 키보드 값 감지
    key = cv2.waitKey(1) & 0xFF

    # 📸 [단축키 S] 누르면 현재 프레임 '수동' 저장
    if key == ord('s'):
        # 캡처본을 저장할 폴더 생성
        os.makedirs("captures", exist_ok=True)
        
        # 파일명을 현재 시간으로 설정
        filename = f"captures/capture_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
        
        # ⭐️ 중요: 박스가 쳐진 annotated_frame이 아니라, 다음 학습(라벨링)에 곧바로 사용할 수 있는 깨끗한 '원본 frame'을 저장합니다.
        cv2.imwrite(filename, frame) 
        print(f"📸 [수동 수집] 애매한 순간 저장 완료! -> {filename}")

    # 'q' 키로 종료
    if key == ord('q'):
        break

# 종료 정리
cap.release()
cv2.destroyAllWindows()
print("프로그램 종료")