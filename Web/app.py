"""
智能盆栽Web监控系统
提供湿度监控和对话控制界面
支持ESP32音频和图像数据处理
"""

from flask import Flask, render_template, jsonify, request
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

app = Flask(__name__)

# 数据文件路径
DATA_DIR = "data"
HUMIDITY_FILE = os.path.join(DATA_DIR, "humidity_data.json")
CONVERSATION_FILE = os.path.join(DATA_DIR, "conversation_log.json")

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

# 线程锁
data_lock = Lock()

# 对话状态
conversation_state = {
    "active": False,
    "started_at": None
}

# ============ 语音识别处理类 ============
class ServerVoiceRecognizer:
    """服务端语音识别器 - 处理ESP32上传的PCM音频"""
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.conversation_mode = False

    def pcm_to_audio(self, pcm_bytes, sample_rate=16000, sample_width=2):
        """将PCM字节转换为AudioData对象"""
        try:
            audio_data = sr.AudioData(pcm_bytes, sample_rate, sample_width)
            return audio_data
        except Exception as e:
            print(f"PCM转换错误: {e}")
            return None

    def recognize_speech(self, pcm_bytes):
        """识别PCM音频"""
        try:
            audio_data = self.pcm_to_audio(pcm_bytes)
            if not audio_data:
                return None

            # 使用Google语音识别
            text = self.recognizer.recognize_google(audio_data, language='en-US')
            return text.lower()
        except sr.UnknownValueError:
            print("无法识别语音")
            return None
        except sr.RequestError as e:
            print(f"识别服务出错: {e}")
            return None
        except Exception as e:
            print(f"识别错误: {e}")
            return None

    def process_conversation(self, text):
        """处理对话逻辑"""
        if not text:
            return None, None

        # 检查是否是开启对话指令
        if not conversation_state["active"]:
            if "hello world" in text or "helloworld" in text:
                conversation_state["active"] = True
                conversation_state["started_at"] = datetime.now().isoformat()
                response = "Hello! I'm your smart plant. How can I help you today?"
                return text, response
            else:
                return text, None

        # 检查是否是关闭对话指令
        if "bye bye" in text or "bye-bye" in text or "goodbye" in text or "good bye" in text:
            response = "Have a good day! Goodbye!"
            return text, response

        # 生成回复
        response = self.generate_response(text)
        return text, response

    def generate_response(self, text):
        """生成回复"""
        text = text.lower()

        if "how are you" in text or "how r u" in text:
            return "I'm doing great! Thanks for asking. How about you?"
        elif "what is your name" in text or "your name" in text:
            return "I'm your smart plant assistant. You can call me Planty!"
        elif "hello" in text or "hi" in text:
            return "Hello there! How can I assist you?"
        elif "help" in text:
            return "I can chat with you! Try asking me questions or just say 'bye bye' when you're done."
        elif "thank" in text:
            return "You're welcome! Happy to help!"
        elif "weather" in text:
            return "I'm a plant, so I love sunny weather! But I can't check the actual weather for you yet."
        elif "water" in text:
            return "Remember to water your plants regularly! But not too much - we don't like soggy roots!"
        elif "sing" in text or "song" in text:
            return "I'm a plant, not a singer! But I appreciate good music!"
        elif "joke" in text:
            return "Why did the plant go to therapy? Because it had too many deep roots!"
        else:
            return "I heard you! That's interesting. Tell me more!"

# ============ 动作识别处理类 ============
class ServerGestureRecognizer:
    """服务端动作识别器 - 处理ESP32上传的JPEG图像"""
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0  # 使用轻量级模型
        )

        # 用于跟踪历史数据
        self.nose_y_history = deque(maxlen=15)
        self.nose_x_history = deque(maxlen=15)
        self.wrist_history = deque(maxlen=10)
        self.clap_history = deque(maxlen=10)

        # 冷却时间
        self.last_gesture_time = 0
        self.gesture_cooldown = 2.0

    def jpeg_to_frame(self, jpeg_bytes):
        """将JPEG字节转换为OpenCV图像"""
        try:
            nparr = np.frombuffer(jpeg_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            print(f"JPEG解码错误: {e}")
            return None

    def calculate_distance(self, point1, point2):
        """计算两点之间的距离"""
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

    def detect_wave(self, landmarks, image_width, image_height):
        """检测挥手"""
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
                x_changes = [x_positions[i] - x_positions[i-1] for i in range(1, len(x_positions))]

                direction_changes = 0
                for i in range(1, len(x_changes)):
                    if (x_changes[i] > 5 and x_changes[i-1] < -5) or \
                       (x_changes[i] < -5 and x_changes[i-1] > 5):
                        direction_changes += 1

                if direction_changes >= 2:
                    return True
        else:
            self.wrist_history.clear()

        return False

    def detect_raise_hands(self, landmarks, image_height):
        """检测双手举高"""
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value]
        right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value]

        left_hand_raised = (
            left_wrist.y < nose.y and
            left_wrist.y < left_shoulder.y - 0.1 and
            left_elbow.y < left_shoulder.y
        )

        right_hand_raised = (
            right_wrist.y < nose.y and
            right_wrist.y < right_shoulder.y - 0.1 and
            right_elbow.y < right_shoulder.y
        )

        return left_hand_raised and right_hand_raised

    def detect_clap(self, landmarks, image_width, image_height):
        """检测鼓掌"""
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

        left_wrist_pos = (left_wrist.x * image_width, left_wrist.y * image_height)
        right_wrist_pos = (right_wrist.x * image_width, right_wrist.y * image_height)

        hands_distance = self.calculate_distance(left_wrist_pos, right_wrist_pos)

        hands_in_position = (
            left_wrist.y > left_shoulder.y - 0.2 and
            left_wrist.y < left_shoulder.y + 0.3 and
            right_wrist.y > right_shoulder.y - 0.2 and
            right_wrist.y < right_shoulder.y + 0.3
        )

        if hands_in_position:
            self.clap_history.append(hands_distance)

            if len(self.clap_history) >= 8:
                distances = list(self.clap_history)
                min_distance = min(distances)
                max_distance = max(distances)

                if max_distance - min_distance > 80:
                    close_count = sum(1 for d in distances if d < min_distance + 40)
                    far_count = sum(1 for d in distances if d > max_distance - 40)

                    if close_count >= 2 and far_count >= 2:
                        return True
        else:
            self.clap_history.clear()

        return False

    def detect_nod(self, landmarks, image_height):
        """检测点头"""
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
                if (positions[i] > positions[i-1] + 3 and
                    positions[i] > positions[i-2] + 2 and
                    positions[i] > positions[i+1] + 3):
                    peaks += 1
                elif (positions[i] < positions[i-1] - 3 and
                      positions[i] < positions[i-2] - 2 and
                      positions[i] < positions[i+1] - 3):
                    valleys += 1

            if peaks >= 1 and valleys >= 1:
                return True

        return False

    def detect_shake(self, landmarks, image_width):
        """检测摇头"""
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
                if (positions[i] > positions[i-1] + 5 and
                    positions[i] > positions[i+1] + 5):
                    direction_changes += 1
                elif (positions[i] < positions[i-1] - 5 and
                      positions[i] < positions[i+1] - 5):
                    direction_changes += 1

            if direction_changes >= 2:
                return True

        return False

    def recognize_gesture(self, jpeg_bytes):
        """识别手势"""
        try:
            frame = self.jpeg_to_frame(jpeg_bytes)
            if frame is None:
                return None

            # 转换为RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # 进行姿态检测
            results = self.pose.process(image)

            gesture_detected = None
            current_time = time_module.time()

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                h, w, _ = frame.shape

                # 检查冷却时间
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

# 创建全局识别器实例
voice_recognizer = ServerVoiceRecognizer()
gesture_recognizer = ServerGestureRecognizer()

def load_humidity_data():
    """加载湿度数据"""
    if os.path.exists(HUMIDITY_FILE):
        try:
            with open(HUMIDITY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_humidity_data(data):
    """保存湿度数据"""
    with data_lock:
        with open(HUMIDITY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def load_conversation_log():
    """加载对话记录"""
    if os.path.exists(CONVERSATION_FILE):
        try:
            with open(CONVERSATION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_conversation_log(log):
    """保存对话记录"""
    with data_lock:
        with open(CONVERSATION_FILE, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

def get_last_24h_humidity():
    """获取过去24小时的湿度数据"""
    all_data = load_humidity_data()
    now = datetime.now()
    past_24h = now - timedelta(hours=24)
    
    # 筛选过去24小时的数据
    filtered_data = [
        entry for entry in all_data
        if datetime.fromisoformat(entry['timestamp']) >= past_24h
    ]
    
    return filtered_data

def generate_sample_data():
    """生成示例数据（用于测试）"""
    now = datetime.now()
    sample_data = []
    
    # 生成过去24小时的示例数据（每小时一个数据点）
    for i in range(24, 0, -1):
        timestamp = now - timedelta(hours=i)
        # 模拟湿度数据：60-80之间波动
        humidity = 65 + (i % 5) * 3 + ((-1) ** i) * 2
        sample_data.append({
            "timestamp": timestamp.isoformat(),
            "humidity": humidity
        })
    
    save_humidity_data(sample_data)
    return sample_data

# 初始化示例数据
if not os.path.exists(HUMIDITY_FILE):
    generate_sample_data()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/humidity')
def get_humidity():
    """获取湿度数据API"""
    data = get_last_24h_humidity()
    return jsonify({
        "success": True,
        "data": data,
        "count": len(data)
    })

@app.route('/api/conversation/status')
def get_conversation_status():
    """获取对话状态API"""
    return jsonify({
        "success": True,
        "active": conversation_state["active"],
        "started_at": conversation_state["started_at"]
    })

@app.route('/api/conversation/start', methods=['POST'])
def start_conversation():
    """开启对话API"""
    conversation_state["active"] = True
    conversation_state["started_at"] = datetime.now().isoformat()
    
    # 记录到对话日志
    log = load_conversation_log()
    log.append({
        "timestamp": datetime.now().isoformat(),
        "type": "system",
        "message": "对话模式已开启"
    })
    save_conversation_log(log)
    
    return jsonify({
        "success": True,
        "message": "对话已开启",
        "active": True
    })

@app.route('/api/conversation/stop', methods=['POST'])
def stop_conversation():
    """关闭对话API"""
    conversation_state["active"] = False
    
    # 记录到对话日志
    log = load_conversation_log()
    log.append({
        "timestamp": datetime.now().isoformat(),
        "type": "system",
        "message": "对话模式已关闭"
    })
    save_conversation_log(log)
    
    return jsonify({
        "success": True,
        "message": "对话已关闭",
        "active": False
    })

@app.route('/api/conversation/log')
def get_conversation_log():
    """获取对话记录API"""
    log = load_conversation_log()
    # 只返回最近50条
    recent_log = log[-50:] if len(log) > 50 else log
    return jsonify({
        "success": True,
        "data": recent_log
    })

@app.route('/api/gesture', methods=['POST'])
def log_gesture():
    """接收ESP32图像并识别动作"""
    try:
        # 接收JPEG图像数据
        jpeg_bytes = request.data

        if not jpeg_bytes:
            return jsonify({
                "success": False,
                "error": "No image data received",
                "gesture": None
            }), 400

        print(f"接收到图像数据: {len(jpeg_bytes)} 字节")

        # 识别动作
        gesture = gesture_recognizer.recognize_gesture(jpeg_bytes)

        # 如果识别到动作，记录到对话日志
        if gesture:
            log = load_conversation_log()
            log.append({
                "timestamp": datetime.now().isoformat(),
                "type": "gesture",
                "gesture": gesture,
                "message": f"动作: {gesture}"
            })
            save_conversation_log(log)
            print(f"✅ 识别到动作: {gesture}")
        else:
            print("ℹ️  未识别到动作")

        return jsonify({
            "success": True,
            "gesture": gesture
        })

    except Exception as e:
        print(f"❌ 动作识别错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "gesture": None
        }), 500

@app.route('/api/speech', methods=['POST'])
def log_speech():
    """接收ESP32音频并进行语音识别和对话"""
    try:
        # 接收PCM音频数据
        pcm_bytes = request.data

        if not pcm_bytes:
            return jsonify({
                "success": False,
                "error": "No audio data received"
            }), 400

        print(f"接收到音频数据: {len(pcm_bytes)} 字节")

        # 识别语音
        user_text = voice_recognizer.recognize_speech(pcm_bytes)

        if not user_text:
            print("ℹ️  无法识别语音")
            return jsonify({
                "success": True,
                "user": "",
                "bot": ""
            })

        print(f"✅ 识别到: {user_text}")

        # 处理对话
        user_text, bot_text = voice_recognizer.process_conversation(user_text)

        # 记录到对话日志
        log = load_conversation_log()
        if user_text:
            log.append({
                "timestamp": datetime.now().isoformat(),
                "type": "user",
                "message": user_text
            })
        if bot_text:
            log.append({
                "timestamp": datetime.now().isoformat(),
                "type": "bot",
                "message": bot_text
            })
            print(f"🤖 回复: {bot_text}")
        save_conversation_log(log)

        # 检查是否需要结束对话
        action = ""
        if user_text and ("bye bye" in user_text or "goodbye" in user_text):
            action = "end_conversation"
            conversation_state["active"] = False
            print("❌ 对话已结束")

        return jsonify({
            "success": True,
            "user": user_text or "",
            "bot": bot_text or "",
            "action": action
        })

    except Exception as e:
        print(f"❌ 语音识别错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "user": "",
            "bot": ""
        }), 500

@app.route('/api/humidity/add', methods=['POST'])
def add_humidity():
    """添加湿度数据（供传感器调用）"""
    data = request.json
    humidity = data.get('humidity', 0)
    
    all_data = load_humidity_data()
    all_data.append({
        "timestamp": datetime.now().isoformat(),
        "humidity": humidity
    })
    save_humidity_data(all_data)
    
    return jsonify({
        "success": True,
        "message": "湿度数据已添加"
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🌱 智能盆栽Web监控系统")
    print("=" * 60)
    print("本地访问地址: http://localhost:8080")
    print("局域网访问地址: http://[你的IP]:8080")
    print("\n💡 提示:")
    print("  - 如需外网访问，请使用 ngrok 或 localtunnel")
    print("  - 按 Ctrl+C 停止服务器")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=8080)
