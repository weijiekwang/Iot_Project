import cv2
from gesture_recognition import GestureRecognizer
from config import CAM_STREAM_URL

def main():
    recog = GestureRecognizer()

    print("尝试打开 ESP32-CAM 流：", CAM_STREAM_URL)
    cap = cv2.VideoCapture(CAM_STREAM_URL)

    if not cap.isOpened():
        print("错误：无法打开 ESP32-CAM 视频流")
        return

    print("打开成功，开始手势识别（按 q 退出）...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("读取失败，跳过这一帧")
            continue

        # 可选：左右镜像，让动作方向更符合直觉
        frame = cv2.flip(frame, 1)

        processed, gesture = recog.process_frame(frame)

        if gesture:
            print("检测到手势:", gesture)
            cv2.putText(processed, f"Detected: {gesture}",
                        (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                        (0, 255, 0), 3)

        cv2.imshow("ESP32-CAM Gesture", processed)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
