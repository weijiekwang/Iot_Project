# server.py - 智能盆栽服务器（整合版）
# 功能：
# 1. 接收ESP32的音频，进行语音识别和对话
# 2. 接收ESP32的图片，进行动作识别
# 3. 管理对话状态
# 4. 记录数据到Web系统

from flask import Flask, request, jsonify
import io
import wave
import speech_recognition as sr
import cv2
import numpy as np
import mediapipe as mp
from datetime import datetime
import requests

app = Flask(__name__)

# 语音识别器
recognizer = sr.Recognizer()

# MediaPipe姿态检测
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# 对话状态
conversation_active = False

# Web服务器地址（本机的Web监控系统）
WEB_SERVER_URL = "http://localhost:8080"


def recognize_speech_from_pcm(pcm_data):
    """从PCM数据识别语音"""
    try:
        # 转换为WAV格式
        wav_buf = io.BytesIO()
        with wave.open(wav_buf, "wb") as wf:
            wf.setnchannels(1)      # 单声道
            wf.setsampwidth(2)       # 16-bit
            wf.setframerate(16000)   # 16kHz
            wf.writeframes(pcm_data)
        
        wav_buf.seek(0)
        
        # 语音识别
        with sr.AudioFile(wav_buf) as source:
            audio = recognizer.record(source)
        
        text = recognizer.recognize_google(audio, language="en-US")
        return text
        
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        print(f"Speech recognition error: {e}")
        return ""


def process_conversation(text):
    """处理对话逻辑"""
    global conversation_active
    
    if not text:
        return None
    
    text_lower = text.lower()
    
    # 检查开启对话
    if not conversation_active:
        if "hello world" in text_lower:
            conversation_active = True
            # 通知Web系统
            try:
                requests.post(f"{WEB_SERVER_URL}/api/conversation/start")
            except:
                pass
            return {
                "user": text,
                "bot": "Hello! I'm your smart plant. How can I help you?",
                "action": "start_conversation"
            }
        else:
            return None
    
    # 检查结束对话
    if "bye bye" in text_lower or "goodbye" in text_lower:
        conversation_active = False
        # 通知Web系统
        try:
            requests.post(f"{WEB_SERVER_URL}/api/conversation/stop")
        except:
            pass
        return {
            "user": text,
            "bot": "Have a good day! Goodbye!",
            "action": "end_conversation"
        }
    
    # 生成回复
    response = generate_response(text_lower)
    
    # 记录到Web系统
    try:
        requests.post(f"{WEB_SERVER_URL}/api/speech",
                     json={"user": text, "bot": response})
    except:
        pass
    
    return {
        "user": text,
        "bot": response,
        "action": "continue"
    }


def generate_response(text):
    """生成简单的对话回复"""
    if "how are you" in text:
        return "I'm growing well! Thanks for asking."
    elif "water" in text:
        return "Remember to water me regularly!"
    elif "name" in text:
        return "I'm your smart plant. You can call me Planty!"
    elif "joke" in text:
        return "Why did the plant go to therapy? Too many deep roots!"
    elif "thank" in text:
        return "You're welcome! Happy to help!"
    elif "weather" in text:
        return "I love sunny weather! Perfect for photosynthesis!"
    elif "help" in text:
        return "I can chat with you! Ask me anything about plants!"
    else:
        return "That's interesting! Tell me more!"


def detect_gesture_from_image(img_bytes):
    """从图片中检测动作"""
    try:
        # 解码图片
        nparr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return None
        
        # 转换颜色空间
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 姿态检测
        results = pose.process(image_rgb)
        
        if not results.pose_landmarks:
            return None
        
        # 简单的动作识别（示例）
        landmarks = results.pose_landmarks.landmark
        
        # 检测双手举高
        left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]
        nose = landmarks[mp_pose.PoseLandmark.NOSE.value]
        
        if left_wrist.y < nose.y and right_wrist.y < nose.y:
            return "Wow"
        
        # 其他动作检测可以继续添加...
        
        return None
        
    except Exception as e:
        print(f"Gesture detection error: {e}")
        return None


@app.route("/", methods=["GET"])
def index():
    return "Smart Plant Server is running."


@app.route("/api/speech", methods=["POST"])
def speech_endpoint():
    """语音识别和对话接口"""
    # 接收PCM音频数据
    pcm_data = request.data
    
    if not pcm_data:
        return jsonify({"error": "no audio data"}), 400
    
    print(f"[Audio] Received {len(pcm_data)} bytes")
    
    # 语音识别
    text = recognize_speech_from_pcm(pcm_data)
    print(f"[STT] {text}")
    
    # 对话处理
    result = process_conversation(text)
    
    if result:
        print(f"[Bot] {result['bot']}")
        return jsonify(result)
    else:
        return jsonify({
            "user": text,
            "bot": "",
            "action": "none"
        })


@app.route("/api/gesture", methods=["POST"])
def gesture_endpoint():
    """动作识别接口"""
    # 接收JPEG图片
    img_data = request.data
    
    if not img_data:
        return jsonify({"error": "no image data"}), 400
    
    print(f"[Image] Received {len(img_data)} bytes")
    
    # 动作识别
    gesture = detect_gesture_from_image(img_data)
    
    if gesture:
        print(f"[Gesture] {gesture}")
        
        # 记录到Web系统
        try:
            requests.post(f"{WEB_SERVER_URL}/api/gesture",
                         json={"gesture": gesture})
        except:
            pass
        
        return jsonify({"gesture": gesture})
    else:
        return jsonify({"gesture": None})


@app.route("/api/conversation/status", methods=["GET"])
def conversation_status():
    """获取对话状态"""
    return jsonify({"active": conversation_active})


if __name__ == "__main__":
    print("=" * 60)
    print("Smart Plant Server Starting...")
    print("=" * 60)
    print("Listening on: http://0.0.0.0:8000")
    print("Make sure to:")
    print("1. Update ESP32 config with this IP")
    print("2. Start Web server on port 8080")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=8000, debug=True)
