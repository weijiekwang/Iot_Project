# merged server.py
# 功能总览：
#   1) Web 前端页面（原 app.py 的 index + 湿度/对话面板）
#   2) /api/humidity 系列：湿度数据存取
#   3) /api/conversation 系列：对话状态与日志
#   4) /api/gesture：接收 ESP32 图像并做手势识别
#   5) /api/speech：接收 ESP32 音频并做语音对话（带简单 bot）
#   6) /api/stt：给 ESP32 使用的简单语音转文字接口（只返回 text）
#   7) /api/tts_test：给 ESP32 扬声器测试的 TTS PCM 流

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    Response,
)
from datetime import datetime, timedelta
import json
import os
from threading import Lock
import io
import tempfile
import speech_recognition as sr
import cv2
import numpy as np
import mediapipe as mp
from collections import deque
import time as time_module

import wave
import pyttsx3
import audioop

# 如果你的模板在 ./templates，静态文件在 ./static，可以显式指定
app = Flask(__name__, template_folder="templates", static_folder="static")

# =========================
#      数据与全局状态
# =========================

DATA_DIR = "data"
HUMIDITY_FILE = os.path.join(DATA_DIR, "humidity_data.json")
CONVERSATION_FILE = os.path.join(DATA_DIR, "conversation_log.json")

os.makedirs(DATA_DIR, exist_ok=True)

data_lock = Lock()

conversation_state = {
    "active": False,
    "started_at": None,
}

# =========================
#      语音识别（服务端）
# =========================

class ServerVoiceRecognizer:
    """服务端语音识别器 - 处理 ESP32 上传的 PCM 音频"""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.conversation_mode = False

    def pcm_to_audio(self, pcm_bytes, sample_rate=16000, sample_width=2):
        """将 PCM 字节转换为 SpeechRecognition 的 AudioData 对象"""
        try:
            audio_data = sr.AudioData(pcm_bytes, sample_rate, sample_width)
            return audio_data
        except Exception as e:
            print(f"PCM 转换错误: {e}")
            return None

    def recognize_speech(self, pcm_bytes, language="en-US"):
        """识别 PCM 音频 -> 文本"""
        try:
            audio_data = self.pcm_to_audio(pcm_bytes)
            if not audio_data:
                return None

            text = self.recognizer.recognize_google(
                audio_data,
                language=language,
            )
            return text
        except sr.UnknownValueError:
            print("无法识别语音")
            return None
        except sr.RequestError as e:
            print(f"识别服务出错: {e}")
            return None
        except Exception as e:
            print(f"识别错误: {e}")
            return None

    def process_conversation(self, text: str):
        """
        根据识别结果做简单对话逻辑：
          - hello world / helloworld 开启对话
          - bye bye / goodbye 等结束对话
          - 其它内容根据关键词生成简单回复
        """
        if not text:
            return None, None

        text_lower = text.lower()

        # 检查是否是开启对话指令
        if not conversation_state["active"]:
            if "hello world" in text_lower or "helloworld" in text_lower:
                conversation_state["active"] = True
                conversation_state["started_at"] = datetime.now().isoformat()
                response = "Hello! I'm your smart plant. How can I help you today?"
                return text, response
            else:
                return text, None

        # 检查是否是关闭对话指令
        if (
            "bye bye" in text_lower
            or "bye-bye" in text_lower
            or "goodbye" in text_lower
            or "good bye" in text_lower
        ):
            response = "Have a good day! Goodbye!"
            return text, response

        # 生成回复
        response = self.generate_response(text_lower)
        return text, response

    def generate_response(self, text_lower: str) -> str:
        """简单的关键字回复"""
        if "how are you" in text_lower or "how r u" in text_lower:
            return "I'm doing great! Thanks for asking. How about you?"
        elif "what is your name" in text_lower or "your name" in text_lower:
            return "I'm your smart plant assistant. You can call me Planty!"
        elif "hello" in text_lower or "hi" in text_lower:
            return "Hello there! How can I assist you?"
        elif "help" in text_lower:
            return "I can chat with you! Try asking me questions or just say 'bye bye' when you're done."
        elif "thank" in text_lower:
            return "You're welcome! Happy to help!"
        elif "weather" in text_lower:
            return "I'm a plant, so I love sunny weather! But I can't check the actual weather for you yet."
        elif "water" in text_lower:
            return "Remember to water your plants regularly! But not too much - we don't like soggy roots!"
        elif "sing" in text_lower or "song" in text_lower:
            return "I'm a plant, not a singer! But I appreciate good music!"
        elif "joke" in text_lower:
            return "Why did the plant go to therapy? Because it had too many deep roots!"
        else:
            return "I heard you! That's interesting. Tell me more!"


# =========================
#      手势识别（服务端）
# =========================

class ServerGestureRecognizer:
    """服务端动作识别器 - 处理 ESP32 上传的 JPEG 图像"""

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0,  # 轻量级模型
        )

        self.nose_y_history = deque(maxlen=15)
        self.nose_x_history = deque(maxlen=15)
        self.wrist_history = deque(maxlen=10)
        self.clap_history = deque(maxlen=10)

        self.last_gesture_time = 0
        self.gesture_cooldown = 2.0

    def jpeg_to_frame(self, jpeg_bytes):
        try:
            nparr = np.frombuffer(jpeg_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            print(f"JPEG 解码错误: {e}")
            return None

    def calculate_distance(self, p1, p2):
        return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    # --- 以下各类检测逻辑直接来自原 app.py ---

    def detect_wave(self, landmarks, image_width, image_height):
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]

        wrist_pos = None
        is_hand_raised = False

        if right_wrist.y < right_shoulder.y and right_wrist.y < nose.y + 0.1:
            wrist_pos = (right_wrist.x * image_width, right_wrist.y * image_height)
            is_hand_raised = True
        elif left_wrist.y < left_shoulder.y and left_wrist.y < nose.y + 0.1:
            wrist_pos = (left_wrist.x * image_width, left_wrist.y * image_height)
            is_hand_raised = True

        if is_hand_raised and wrist_pos:
            self.wrist_history.append(wrist_pos)

            if len(self.wrist_history) >= 8:
                positions = list(self.wrist_history)
                x_positions = [p[0] for p in positions]
                x_changes = [
                    x_positions[i] - x_positions[i - 1]
                    for i in range(1, len(x_positions))
                ]

                direction_changes = 0
                for i in range(1, len(x_changes)):
                    if (x_changes[i] > 5 and x_changes[i - 1] < -5) or (
                        x_changes[i] < -5 and x_changes[i - 1] > 5
                    ):
                        direction_changes += 1

                if direction_changes >= 2:
                    return True
        else:
            self.wrist_history.clear()

        return False

    def detect_raise_hands(self, landmarks, image_height):
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value]
        right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value]

        left_hand_raised = (
            left_wrist.y < nose.y
            and left_wrist.y < left_shoulder.y - 0.1
            and left_elbow.y < left_shoulder.y
        )

        right_hand_raised = (
            right_wrist.y < nose.y
            and right_wrist.y < right_shoulder.y - 0.1
            and right_elbow.y < right_shoulder.y
        )

        return left_hand_raised and right_hand_raised

    def detect_clap(self, landmarks, image_width, image_height):
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

        left_wrist_pos = (left_wrist.x * image_width, left_wrist.y * image_height)
        right_wrist_pos = (right_wrist.x * image_width, right_wrist.y * image_height)

        hands_distance = self.calculate_distance(left_wrist_pos, right_wrist_pos)

        hands_in_position = (
            left_wrist.y > left_shoulder.y - 0.2
            and left_wrist.y < left_shoulder.y + 0.3
            and right_wrist.y > right_shoulder.y - 0.2
            and right_wrist.y < right_shoulder.y + 0.3
        )

        if hands_in_position:
            self.clap_history.append(hands_distance)

            if len(self.clap_history) >= 8:
                distances = list(self.clap_history)
                min_distance = min(distances)
                max_distance = max(distances)

                if max_distance - min_distance > 80:
                    close_count = sum(
                        1 for d in distances if d < min_distance + 40
                    )
                    far_count = sum(1 for d in distances if d > max_distance - 40)

                    if close_count >= 2 and far_count >= 2:
                        return True
        else:
            self.clap_history.clear()

        return False

    def detect_nod(self, landmarks, image_height):
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        nose_y = nose.y * image_height

        self.nose_y_history.append(nose_y)

        if len(self.nose_y_history) >= 12:
            positions = list(self.nose_y_history)
            max_y = max(positions)
            min_y = min(positions)
            movement_range = max_y - min_y

            if movement_range < 8:
                return False

            peaks = 0
            valleys = 0

            for i in range(2, len(positions) - 2):
                if (
                    positions[i] > positions[i - 1] + 3
                    and positions[i] > positions[i - 2] + 2
                    and positions[i] > positions[i + 1] + 3
                ):
                    peaks += 1
                elif (
                    positions[i] < positions[i - 1] - 3
                    and positions[i] < positions[i - 2] - 2
                    and positions[i] < positions[i + 1] - 3
                ):
                    valleys += 1

            if peaks >= 1 and valleys >= 1:
                return True

        return False

    def detect_shake(self, landmarks, image_width):
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        nose_x = nose.x * image_width

        self.nose_x_history.append(nose_x)

        if len(self.nose_x_history) >= 10:
            positions = list(self.nose_x_history)
            max_x = max(positions)
            min_x = min(positions)
            movement_range = max_x - min_x

            if movement_range < 25:
                return False

            direction_changes = 0
            for i in range(1, len(positions) - 1):
                if (
                    positions[i] > positions[i - 1] + 5
                    and positions[i] > positions[i + 1] + 5
                ):
                    direction_changes += 1
                elif (
                    positions[i] < positions[i - 1] - 5
                    and positions[i] < positions[i + 1] - 5
                ):
                    direction_changes += 1

            if direction_changes >= 2:
                return True

        return False

    def recognize_gesture(self, jpeg_bytes):
        """综合调用各个子检测，返回 'Hi' / 'Yes' / 'No' / 'Wow' / 'Good' 等"""
        try:
            frame = self.jpeg_to_frame(jpeg_bytes)
            if frame is None:
                return None

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            results = self.pose.process(image)

            gesture_detected = None
            current_time = time_module.time()

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                h, w, _ = frame.shape

                if current_time - self.last_gesture_time > self.gesture_cooldown:
                    if self.detect_raise_hands(landmarks, h):
                        gesture_detected = "Wow"
                        self.last_gesture_time = current_time
                    elif self.detect_clap(landmarks, w, h):
                        gesture_detected = "Good"
                        self.last_gesture_time = current_time
                        self.clap_history.clear()
                    elif self.detect_wave(landmarks, w, h):
                        gesture_detected = "Hi"
                        self.last_gesture_time = current_time
                        self.wrist_history.clear()
                    elif self.detect_nod(landmarks, h):
                        gesture_detected = "Yes"
                        self.last_gesture_time = current_time
                        self.nose_y_history.clear()
                    elif self.detect_shake(landmarks, w):
                        gesture_detected = "No"
                        self.last_gesture_time = current_time
                        self.nose_x_history.clear()

            return gesture_detected

        except Exception as e:
            print(f"手势识别错误: {e}")
            return None


voice_recognizer = ServerVoiceRecognizer()
gesture_recognizer = ServerGestureRecognizer()

# =========================
#      数据读写工具函数
# =========================

def load_humidity_data():
    if os.path.exists(HUMIDITY_FILE):
        try:
            with open(HUMIDITY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_humidity_data(data):
    with data_lock:
        with open(HUMIDITY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def load_conversation_log():
    if os.path.exists(CONVERSATION_FILE):
        try:
            with open(CONVERSATION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_conversation_log(log):
    with data_lock:
        with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)


def get_last_24h_humidity():
    all_data = load_humidity_data()
    now = datetime.now()
    past_24h = now - timedelta(hours=24)
    filtered_data = [
        entry
        for entry in all_data
        if datetime.fromisoformat(entry["timestamp"]) >= past_24h
    ]
    return filtered_data


def generate_sample_data():
    now = datetime.now()
    sample_data = []
    for i in range(24, 0, -1):
        timestamp = now - timedelta(hours=i)
        humidity = 65 + (i % 5) * 3 + ((-1) ** i) * 2
        sample_data.append(
            {
                "timestamp": timestamp.isoformat(),
                "humidity": humidity,
            }
        )

    save_humidity_data(sample_data)
    return sample_data


if not os.path.exists(HUMIDITY_FILE):
    generate_sample_data()

# =========================
#      Web 页面 & REST API
# =========================

@app.route("/")
def index():
    """主页：渲染 app.py 的 index.html 页面"""
    return render_template("index.html")


@app.route("/health")
def health():
    """简单健康检查，方便调试"""
    return jsonify({"status": "ok"})


@app.route("/api/humidity")
def get_humidity():
    data = get_last_24h_humidity()
    return jsonify({"success": True, "data": data, "count": len(data)})


@app.route("/api/humidity/add", methods=["POST"])
def add_humidity():
    data = request.json or {}
    humidity = data.get("humidity", 0)

    all_data = load_humidity_data()
    all_data.append(
        {
            "timestamp": datetime.now().isoformat(),
            "humidity": humidity,
        }
    )
    save_humidity_data(all_data)

    return jsonify({"success": True, "message": "湿度数据已添加"})


@app.route("/api/conversation/status")
def get_conversation_status():
    return jsonify(
        {
            "success": True,
            "active": conversation_state["active"],
            "started_at": conversation_state["started_at"],
        }
    )


@app.route("/api/conversation/start", methods=["POST"])
def start_conversation():
    conversation_state["active"] = True
    conversation_state["started_at"] = datetime.now().isoformat()

    log = load_conversation_log()
    log.append(
        {
            "timestamp": datetime.now().isoformat(),
            "type": "system",
            "message": "对话模式已开启",
        }
    )
    save_conversation_log(log)

    return jsonify({"success": True, "message": "对话已开启", "active": True})


@app.route("/api/conversation/stop", methods=["POST"])
def stop_conversation():
    conversation_state["active"] = False

    log = load_conversation_log()
    log.append(
        {
            "timestamp": datetime.now().isoformat(),
            "type": "system",
            "message": "对话模式已关闭",
        }
    )
    save_conversation_log(log)

    return jsonify({"success": True, "message": "对话已关闭", "active": False})


@app.route("/api/conversation/log")
def get_conversation_log_api():
    log = load_conversation_log()
    recent_log = log[-50:] if len(log) > 50 else log
    return jsonify({"success": True, "data": recent_log})


@app.route("/api/gesture", methods=["POST"])
def log_gesture():
    try:
        jpeg_bytes = request.data
        if not jpeg_bytes:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "No image data received",
                        "gesture": None,
                    }
                ),
                400,
            )

        print(f"接收到图像数据: {len(jpeg_bytes)} 字节")

        gesture = gesture_recognizer.recognize_gesture(jpeg_bytes)

        if gesture:
            log = load_conversation_log()
            log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": "gesture",
                    "gesture": gesture,
                    "message": f"动作: {gesture}",
                }
            )
            save_conversation_log(log)
            print(f"✅ 识别到动作: {gesture}")
        else:
            print("ℹ️  未识别到动作")

        return jsonify({"success": True, "gesture": gesture})

    except Exception as e:
        print(f"❌ 动作识别错误: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "gesture": None,
                }
            ),
            500,
        )


@app.route("/api/speech", methods=["POST"])
def log_speech():
    """
    原 app.py 对话接口：
      - 接收 ESP32 PCM
      - 识别文本
      - 根据对话状态生成 bot 回复
    """
    try:
        pcm_bytes = request.data
        if not pcm_bytes:
            return (
                jsonify({"success": False, "error": "No audio data received"}),
                400,
            )

        print(f"接收到音频数据: {len(pcm_bytes)} 字节")

        user_text = voice_recognizer.recognize_speech(pcm_bytes, language="en-US")

        if not user_text:
            print("ℹ️  无法识别语音")
            return jsonify({"success": True, "user": "", "bot": ""})

        print(f"✅ 识别到: {user_text}")

        user_text, bot_text = voice_recognizer.process_conversation(user_text)

        log = load_conversation_log()
        if user_text:
            log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": "user",
                    "message": user_text,
                }
            )
        if bot_text:
            log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": "bot",
                    "message": bot_text,
                }
            )
            print(f"🤖 回复: {bot_text}")
        save_conversation_log(log)

        action = ""
        if user_text and (
            "bye bye" in user_text.lower()
            or "goodbye" in user_text.lower()
        ):
            action = "end_conversation"
            conversation_state["active"] = False
            print("❌ 对话已结束")

        return jsonify(
            {
                "success": True,
                "user": user_text or "",
                "bot": bot_text or "",
                "action": action,
            }
        )

    except Exception as e:
        print(f"❌ 语音识别错误: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "user": "",
                    "bot": "",
                }
            ),
            500,
        )

# =========================
#   简单 STT 接口 (/api/stt)
#   给 ESP32 当前 I2S 流式上传用
# =========================

@app.route("/api/stt", methods=["POST"])
def stt_endpoint():
    """
    接收 ESP32 发送的原始 PCM（16kHz,16bit,mono），
    使用同一个 ServerVoiceRecognizer 做 STT，
    返回 {"text": "...", "raw_bytes": N}
    """
    raw = request.data
    if not raw:
        return jsonify({"error": "no audio data"}), 400

    print(f"[INFO] /api/stt 收到音频: {len(raw)} 字节")

    text = voice_recognizer.recognize_speech(raw, language="en-US")
    if text is None:
        text = ""

    print(f"[STT] text = {text!r}")

    return jsonify({"text": text, "raw_bytes": len(raw)})


# =========================
#   TTS：/api/tts_test
#   生成固定句子的 16kHz 16bit mono PCM
# =========================

REPLY_TEXT = "I love Columbia, test test test"

def generate_tts_pcm(text: str) -> bytes:
    """
    用 pyttsx3 生成 text 的 WAV，再转成 16kHz 16bit mono PCM。
    返回纯 PCM bytes（不含 WAV 头）。
    """
    engine = pyttsx3.init()
    tmp_name = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_name = tmp.name

        engine.save_to_file(text, tmp_name)
        engine.runAndWait()

        with wave.open(tmp_name, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            frames = wf.readframes(n_frames)

        if n_channels != 1:
            frames = audioop.tomono(frames, sampwidth, 1.0, 1.0)
            n_channels = 1

        if sampwidth != 2:
            frames = audioop.lin2lin(frames, sampwidth, 2)
            sampwidth = 2

        if framerate != 16000:
            frames, _ = audioop.ratecv(
                frames,
                sampwidth,
                n_channels,
                framerate,
                16000,
                None,
            )
            framerate = 16000

        print(f"[TTS] Generated PCM length={len(frames)} bytes")
        return frames

    finally:
        if tmp_name and os.path.exists(tmp_name):
            os.remove(tmp_name)


print("[TTS] Pre-generating TTS PCM ...")
TTS_PCM = generate_tts_pcm(REPLY_TEXT)
print("[TTS] Ready.")


@app.route("/api/tts_test", methods=["GET"])
def tts_test():
    """
    返回预生成好的 TTS PCM，类型为 application/octet-stream，
    ESP32 端直接当成 16kHz,16bit,mono PCM 播放即可。
    """
    return Response(TTS_PCM, mimetype="application/octet-stream")


# =========================
#          启动
# =========================

if __name__ == "__main__":
    print("=" * 60)
    print("🌱 智能盆栽 Web 监控系统 + ESP32 STT/TTS Server")
    print("=" * 60)
    print("本机访问:   http://localhost:8000")
    print("局域网访问: http://<你的笔记本IP>:8000")
    print("STT 接口:   POST /api/stt")
    print("TTS 测试:   GET  /api/tts_test")
    print("=" * 60)

    app.run(host="0.0.0.0", port=8000, debug=True)
