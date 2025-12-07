# server.py
# 功能：
#   1) Web 页面（/）：显示一个"智能盆栽监控系统"的假数据仪表盘
#   2) /api/stt ：接收 ESP32 发送的原始 PCM，做语音识别，返回对话响应
#   3) /api/tts ：将文本转换为语音PCM返回给ESP32
#   4) 对话模式管理：支持"hello world"开启，"bye bye"关闭

from flask import Flask, request, jsonify, Response
import io
import wave
import speech_recognition as sr

import pyttsx3
import audioop
import tempfile
import os

import cv2
import time
import threading

from gesture_recognition import GestureRecognizer
from config import CAM_STREAM_URL, POE_API_KEY, POE_BOT_NAME

# POE API 客户端
import fastapi_poe as fp

app = Flask(__name__)

latest_gesture = None       # 最近一次识别到的手势字符串
latest_gesture_time = 0.0   # 对应的时间戳
gesture_lock = threading.Lock()

# ========= 对话状态管理 =========
class ConversationManager:
    def __init__(self):
        self.conversation_mode = False  # 对话模式标志
        self.last_response = ""  # 存储最新的回复文本
        self.conversation_history = []  # 存储对话历史
        self.poe_client = None  # POE API 客户端
        self._init_poe_client()

    def _init_poe_client(self):
        """Initialize POE API client"""
        try:
            self.poe_client = fp.get_bot_response
            print(f"[POE] POE API client initialized successfully, using model: {POE_BOT_NAME}")
        except Exception as e:
            print(f"[POE] POE API client initialization failed: {e}")
            self.poe_client = None

    def is_active(self):
        """检查对话模式是否激活"""
        return self.conversation_mode

    def activate(self):
        """Activate conversation mode"""
        self.conversation_mode = True
        self.conversation_history = []  # Clear conversation history
        print("[Conversation] Conversation mode activated")

    def deactivate(self):
        """Deactivate conversation mode"""
        self.conversation_mode = False
        self.conversation_history = []  # Clear conversation history
        print("[Conversation] Conversation mode deactivated")

    def process_text(self, text):
        """Process recognized text and return response"""
        if not text:
            print("[Conversation] No text recognized")
            return None, None

        text_lower = text.lower()
        print(f"[Conversation] Processing text: '{text_lower}' | Mode: {self.conversation_mode}")

        # Check if it's a start conversation command
        if not self.conversation_mode:
            # Strict match for "hello world" or "hello" alone
            if "hello world" in text_lower or text_lower.strip() == "hello":
                self.activate()
                response = "Hello! I'm your smart plant. How can I help you today?"
                return response, "start_conversation"
            else:
                # Not in conversation mode, ignore input
                print("[Conversation] Not in conversation mode, ignoring input")
                return None, None

        # In conversation mode
        print("[Conversation] Conversation mode active, processing user input")

        # Check if it's an end conversation command
        if "bye bye" in text_lower or "bye-bye" in text_lower or "goodbye" in text_lower or "good bye" in text_lower:
            response = "Have a good day! Goodbye!"
            self.deactivate()
            return response, "end_conversation"

        # Generate response using LLM
        response = self.generate_response_with_llm(text)
        print(f"[Conversation] Generated response: '{response}'")
        return response, "continue"

    def generate_response_with_llm(self, text):
        """Generate conversation response using POE API LLM"""
        if not self.poe_client:
            print("[LLM] POE client not initialized, using fallback response")
            return "Sorry, I'm having trouble thinking right now. Please try again later."

        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": text
            })

            # Build full conversation context
            system_prompt = "You are a friendly and helpful AI assistant. You can chat with users about any topic and answer their questions. Keep your responses concise and friendly (1-2 sentences). Do not use emojis in your responses."

            # Build message list
            messages = [fp.ProtocolMessage(role="system", content=system_prompt)]
            for msg in self.conversation_history:
                messages.append(fp.ProtocolMessage(role=msg["role"], content=msg["content"]))

            print(f"[LLM] Sending request to POE API, model: {POE_BOT_NAME}")

            # Call POE API - need to handle async generator properly
            import asyncio

            async def get_response():
                response_text = ""
                chunk_count = 0
                try:
                    print("[LLM] Starting to iterate through POE API response stream...")
                    async for partial in self.poe_client(
                        messages=messages,
                        bot_name=POE_BOT_NAME,
                        api_key=POE_API_KEY
                    ):
                        chunk_count += 1
                        print(f"[LLM] Received chunk #{chunk_count}, type: {type(partial).__name__}")

                        # Collect full text from streaming response
                        if isinstance(partial, fp.PartialResponse):
                            # POE API streaming: accumulate all text chunks
                            if partial.text:
                                response_text += partial.text
                            # Safe print that handles emojis and special characters
                            preview = partial.text[:100].encode('ascii', 'replace').decode('ascii') if partial.text else ""
                            print(f"[LLM] PartialResponse text length: {len(partial.text)}, content preview: '{preview}'")
                        elif isinstance(partial, fp.MetaResponse):
                            print(f"[LLM] MetaResponse received (end of stream)")
                        else:
                            print(f"[LLM] Unknown response type: {type(partial)}")

                    print(f"[LLM] Stream ended. Total chunks: {chunk_count}, Final response length: {len(response_text)}")
                except Exception as e:
                    print(f"[LLM] Error in async response: {e}")
                    import traceback
                    traceback.print_exc()
                return response_text if response_text else None

            # Run async function in sync context
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            response_text = loop.run_until_complete(get_response())

            # Check if we got a valid response
            if not response_text:
                print("[LLM] Warning: Empty response from POE API")
                # Remove the user message we just added since we didn't get a response
                self.conversation_history.pop()
                return "Sorry, I didn't get that. Could you please repeat?"

            # Add bot response to history (POE API uses "bot" not "assistant")
            self.conversation_history.append({
                "role": "bot",
                "content": response_text
            })

            # Limit history length, keep only last 10 rounds
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            # Safe print that handles emojis and special characters
            safe_text = response_text.encode('ascii', 'replace').decode('ascii')
            print(f"[LLM] Received response: {safe_text}")
            return response_text

        except Exception as e:
            print(f"[LLM] POE API call failed: {e}")
            import traceback
            traceback.print_exc()
            # Return fallback response on failure
            return "Sorry, I'm having trouble thinking right now. Please try again later."

# 创建全局对话管理器
conversation_manager = ConversationManager()

# ========= 简单网页（假数据） =========

INDEX_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>智能盆栽监控系统</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "PingFang SC", "Microsoft YaHei", sans-serif;
            min-height: 100vh;
            background: linear-gradient(135deg, #5b8def, #8a6de9);
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 32px;
            color: #fff;
        }
        .container {
            width: 100%;
            max-width: 1200px;
            background: rgba(255,255,255,0.12);
            border-radius: 24px;
            box-shadow: 0 20px 45px rgba(0,0,0,0.25);
            backdrop-filter: blur(18px);
            padding: 24px 32px 32px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }
        .title {
            font-size: 28px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .title span.icon {
            font-size: 30px;
        }
        .subtitle {
            font-size: 14px;
            opacity: 0.85;
        }
        .chips {
            display: flex;
            gap: 8px;
            font-size: 13px;
        }
        .chip {
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(255,255,255,0.12);
        }
        .main {
            display: grid;
            grid-template-columns: 2.1fr 1fr;
            gap: 20px;
        }
        .gesture-display {
            background: rgba(255,255,255,0.08);
            border-radius: 14px;
            padding: 20px;
            text-align: center;
            margin-bottom: 16px;
        }
        .gesture-label {
            font-size: 13px;
            opacity: 0.75;
            margin-bottom: 8px;
        }
        .gesture-value {
            font-size: 42px;
            font-weight: 700;
            color: #9db5ff;
            min-height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            letter-spacing: 1px;
        }
        .gesture-value.no-gesture {
            font-size: 20px;
            opacity: 0.5;
        }
        .gesture-time {
            font-size: 11px;
            opacity: 0.6;
            margin-top: 8px;
        }
        .card {
            background: rgba(15,20,40,0.85);
            border-radius: 18px;
            padding: 16px 20px 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.25);
        }
        .card h2 {
            font-size: 18px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card h2 span.icon {
            font-size: 20px;
        }
        .divider {
            height: 2px;
            background: linear-gradient(90deg, #6f8cff, #b46dff);
            margin: 6px 0 14px;
            opacity: 0.85;
        }
        .stats-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 18px;
        }
        .stat-box {
            background: linear-gradient(135deg, #5566e8, #8b63e8);
            border-radius: 16px;
            padding: 12px;
            text-align: center;
        }
        .stat-value {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .stat-label {
            font-size: 13px;
            opacity: 0.9;
        }
        .fake-chart {
            margin-top: 10px;
            padding: 12px 10px 6px;
            background: rgba(255,255,255,0.04);
            border-radius: 14px;
        }
        .chart-title {
            font-size: 13px;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .chart-title span.legend {
            width: 10px;
            height: 10px;
            border-radius: 6px;
            background: #9db5ff;
        }
        .chart-bars {
            display: flex;
            align-items: flex-end;
            gap: 6px;
            height: 120px;
        }
        .bar {
            flex: 1;
            border-radius: 6px 6px 0 0;
            background: linear-gradient(180deg, #9db5ff, #5c73ff);
            opacity: 0.8;
        }
        .bar:nth-child(2n) { height: 55%; }
        .bar:nth-child(3n) { height: 80%; }
        .bar:nth-child(4n) { height: 35%; }
        .bar:nth-child(5n) { height: 90%; }
        .bar:nth-child(7) { height: 65%; }
        .bar:nth-child(9) { height: 75%; }
        .bar:nth-child(10) { height: 60%; }
        .y-axis {
            font-size: 10px;
            opacity: 0.7;
            display: flex;
            justify-content: space-between;
            margin-top: 6px;
        }
        .control-buttons {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 6px;
        }
        .btn {
            width: 100%;
            border-radius: 999px;
            border: none;
            padding: 10px 14px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            color: #fff;
        }
        .btn span.status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #ff5d70;
            box-shadow: 0 0 0 3px rgba(255,93,112,0.35);
        }
        .btn-green {
            background: linear-gradient(135deg, #1bbf72, #10a95b);
        }
        .btn-red {
            background: linear-gradient(135deg, #ff5d70, #eb4455);
        }
        .btn-blue {
            background: linear-gradient(135deg, #4285f4, #597cf5);
        }
        .btn-amber {
            background: linear-gradient(135deg, #f59e0b, #fbbf24);
        }
        .btn-ghost {
            background: rgba(255,255,255,0.08);
        }
        .hint {
            font-size: 11px;
            opacity: 0.8;
            margin-top: 8px;
            line-height: 1.5;
        }
        @media (max-width: 900px) {
            .main { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div>
            <div class="title">
                <span class="icon">🌱</span>
                <span>智能盆栽监控系统</span>
            </div>
            <div class="subtitle">实时湿度监控 · 语音对话 · 动作识别（当前数据为示例假数据）</div>
        </div>
        <div class="chips">
            <div class="chip">实时监控</div>
            <div class="chip">语音助手</div>
            <div class="chip">ESP32</div>
        </div>
    </div>

    <div class="main">
        <div class="card">
            <h2><span class="icon">💧</span> 湿度监控（过去 24 小时）</h2>
            <div class="divider"></div>
            <div class="stats-row">
                <div class="stat-box">
                    <div class="stat-value">66</div>
                    <div class="stat-label">当前湿度 (%)</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">70.8</div>
                    <div class="stat-label">平均湿度 (%)</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">21</div>
                    <div class="stat-label">数据点数</div>
                </div>
            </div>
            <div class="fake-chart">
                <div class="chart-title">
                    <span class="legend"></span>
                    <span>湿度变化趋势（示意图，仅前端假数据）</span>
                </div>
                <div class="chart-bars">
                    <div class="bar" style="height:65%;"></div>
                    <div class="bar"></div>
                    <div class="bar"></div>
                    <div class="bar"></div>
                    <div class="bar"></div>
                    <div class="bar"></div>
                    <div class="bar"></div>
                    <div class="bar"></div>
                    <div class="bar"></div>
                    <div class="bar"></div>
                </div>
                <div class="y-axis">
                    <span>60%</span><span>70%</span><span>80%</span><span>90%</span><span>100%</span>
                </div>
            </div>
        </div>

        <div class="card">
            <h2><span class="icon">👋</span> 手势识别</h2>
            <div class="divider"></div>
            <div class="gesture-display">
                <div class="gesture-label">当前识别手势</div>
                <div class="gesture-value no-gesture" id="gestureValue">等待识别...</div>
                <div class="gesture-time" id="gestureTime">-</div>
            </div>
        </div>

        <div class="card">
            <h2><span class="icon">💬</span> 对话控制</h2>
            <div class="divider"></div>
            <div class="control-buttons">
                <button class="btn btn-ghost">
                    <span>当前状态：对话已关闭（示例）</span>
                </button>
                <button class="btn btn-green">
                    <span class="status-dot" style="background:#2cff7c;"></span>
                    <span>开启对话（示例按钮）</span>
                </button>
                <button class="btn btn-red">
                    <span class="status-dot"></span>
                    <span>关闭对话（示例按钮）</span>
                </button>
                <button class="btn btn-blue">
                    <span>刷新数据（示例按钮）</span>
                </button>
                <button class="btn btn-green">
                    <span>💧 浇水（示例按钮）</span>
                </button>
                <button class="btn btn-amber">
                    <span>????????</span>
                </button>
            </div>
            <p class="hint">
                💡 提示：<br>
                · ESP32 通过 <code>/api/stt</code> 上传麦克风音频，由服务器转文字；<br>
                · ESP32 通过 <code>/api/tts_test</code> 获取合成语音 PCM，在本地扬声器播放。
            </p>
        </div>
    </div>
</div>

<script>
    // 定时获取手势识别结果
    function updateGesture() {
        fetch('/api/gesture_status')
            .then(response => response.json())
            .then(data => {
                const gestureValue = document.getElementById('gestureValue');
                const gestureTime = document.getElementById('gestureTime');

                if (data.gesture) {
                    // 有手势识别结果
                    gestureValue.textContent = data.gesture;
                    gestureValue.classList.remove('no-gesture');

                    // 显示时间
                    const date = new Date(data.timestamp * 1000);
                    const timeStr = date.toLocaleTimeString('zh-CN');
                    gestureTime.textContent = '识别时间: ' + timeStr;
                } else {
                    // 没有手势
                    gestureValue.textContent = '等待识别...';
                    gestureValue.classList.add('no-gesture');
                    gestureTime.textContent = '-';
                }
            })
            .catch(error => {
                console.error('获取手势失败:', error);
            });
    }

    // 每500毫秒更新一次
    setInterval(updateGesture, 500);

    // 页面加载时立即更新一次
    updateGesture();
</script>
</body>
</html>
"""
# ================== ESP32-CAM 手势识别后台线程（带监看） ==================

latest_gesture = None       # 最近一次识别到的手势
latest_gesture_time = 0.0   # 时间戳
gesture_lock = threading.Lock()


def gesture_worker():
    """
    后台线程：从 ESP32-CAM 拉视频流，持续做手势识别。
    同时在本机弹出一个预览窗口（按 q 关闭预览窗口，但线程继续跑）。
    出错时会自动重连。
    """
    global latest_gesture, latest_gesture_time

    print("[Gesture] Using stream URL:", CAM_STREAM_URL)

    cap = None
    fail_count = 0

    # Preview window enabled (press q to close window, but gesture recognition continues)
    preview_enabled = True

    # Create one recognizer instance for reuse
    recog = GestureRecognizer()

    while True:
        # If not opened or broken, try to reconnect
        if cap is None or not cap.isOpened():
            try:
                print("[Gesture] Trying to open ESP32-CAM video stream...")
                cap = cv2.VideoCapture(CAM_STREAM_URL)
                if not cap.isOpened():
                    print("[Gesture] Failed to open, retrying in 2 seconds")
                    time.sleep(2.0)
                    continue
                print("[Gesture] Video stream opened successfully, starting background gesture recognition...")
                fail_count = 0
            except Exception as e:
                print("[Gesture] Exception opening stream:", e)
                time.sleep(2.0)
                continue

        # Read frame normally
        ret, frame = cap.read()
        if not ret:
            fail_count += 1
            print(f"[Gesture] Failed to read frame (consecutive failures: {fail_count}), continuing")

            # If too many consecutive failures, reconnect
            if fail_count >= 20:
                print("[Gesture] Too many consecutive failures, releasing and reconnecting video stream")
                try:
                    cap.release()
                except Exception:
                    pass
                cap = None
                fail_count = 0
                time.sleep(1.0)
            else:
                time.sleep(0.1)
            continue

        # Successfully read frame, reset failure count
        fail_count = 0

        # Optional: mirror
        frame = cv2.flip(frame, 1)

        try:
            processed, gesture = recog.process_frame(frame)
        except Exception as e:
            print("[Gesture] Exception processing frame:", e)
            time.sleep(0.05)
            continue

        # Preview display
        if preview_enabled:
            try:
                cv2.imshow("ESP32-CAM Gesture Preview", processed)
                # Press q to close preview window (window only, gesture recognition continues)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("[Gesture] Preview window closed (gesture recognition still running in background)")
                    cv2.destroyWindow("ESP32-CAM Gesture Preview")
                    preview_enabled = False
            except Exception as e:
                print("[Gesture] Preview window exception:", e)
                preview_enabled = False

        # Write gesture result to global variable
        if gesture:
            with gesture_lock:
                latest_gesture = gesture
                latest_gesture_time = time.time()
            print("[Gesture] Detected gesture:", gesture)

        # Control CPU usage
        time.sleep(0.02)


@app.route("/", methods=["GET"])
def index():
    return INDEX_HTML


# ========= STT：ESP32 -> 服务器（音频转文字） =========

recognizer = sr.Recognizer()

@app.route("/api/stt", methods=["POST"])
def stt_endpoint():
    """
    接收 ESP32 发送的原始 PCM（16kHz,16bit,mono），
    转成 WAV 后，用 SpeechRecognition 调用 Google STT，
    并返回对话响应和TTS音频。
    """
    raw = request.data
    if not raw:
        return jsonify({"error": "no audio data"}), 400

    print(f"[STT] Received audio bytes: {len(raw)}")

    # 检查音频数据是否有效
    if len(raw) < 1000:
        print(f"[STT] WARNING: Audio data too short ({len(raw)} bytes)")

    # 检查音频是否全是静音（全为0或非常接近0）
    import struct
    samples = struct.unpack(f'{len(raw)//2}h', raw)
    max_amplitude = max(abs(s) for s in samples)
    avg_amplitude = sum(abs(s) for s in samples) / len(samples)
    print(f"[STT] Audio stats - Max amplitude: {max_amplitude}, Avg amplitude: {avg_amplitude:.2f}")

    if max_amplitude < 100:
        print("[STT] WARNING: Audio appears to be silent or very quiet!")

    # 把原始 PCM 包装成 WAV（内存中）
    wav_buf = io.BytesIO()
    with wave.open(wav_buf, "wb") as wf:
        wf.setnchannels(1)        # 单声道
        wf.setsampwidth(2)        # 16bit
        wf.setframerate(16000)    # 16kHz
        wf.writeframes(raw)

    wav_buf.seek(0)

    text = ""
    try:
        with sr.AudioFile(wav_buf) as source:
            # 调整环境噪音阈值，提高识别率
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.record(source)

        # 检查音频长度
        print(f"[STT] Audio duration: {len(audio.frame_data)} bytes")

        # 现在用英文，如果想识别中文改成 language="zh-CN"
        text = recognizer.recognize_google(audio, language="en-US")
        print(f"[STT] User said: {text}")

    except sr.UnknownValueError:
        print("[STT] Speech was not understood (no speech detected or too noisy)")
        text = ""
    except sr.RequestError as e:
        print(f"[STT] API request failed: {e}")
        return jsonify({"error": "stt_request_failed"}), 500
    except Exception as e:
        print(f"[STT] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "internal_error"}), 500

    # Process conversation logic
    print(f"[STT] Processing conversation, recognized text: '{text}'")
    response_text, action = conversation_manager.process_text(text)

    # If there's a response, store it for TTS requests
    if response_text:
        print(f"[BOT] Response: {response_text}")
        # Store latest response for /api/tts endpoint
        conversation_manager.last_response = response_text
    else:
        print("[BOT] No response generated")

    # Return result (no audio data to avoid ESP32 memory issues)
    result = {
        "text": text,
        "response": response_text if response_text else "",
        "action": action if action else "",
        "conversation_active": conversation_manager.is_active(),
        "has_audio": response_text is not None and response_text != ""
    }

    print(f"[API] Returning result: text='{text}', response='{response_text}', action='{action}', conversation_active={conversation_manager.is_active()}")
    return jsonify(result)


# ========= TTS：服务器 -> ESP32（文字转语音 PCM） =========

# HARDCODED REPLY - COMMENTED OUT (now using LLM responses)
# REPLY_TEXT = "I love Columbia, test test test"

def generate_tts_pcm(text: str) -> bytes:
    """
    用 pyttsx3 生成 text 的 WAV，再转成 16kHz 16bit mono PCM。
    返回：纯 PCM bytes（不含 WAV 头）。
    """
    engine = pyttsx3.init()
    tmp_name = None

    try:
        # 1. 生成临时 WAV 文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_name = tmp.name

        engine.save_to_file(text, tmp_name)
        engine.runAndWait()

        # 2. 读取 WAV 内容
        with wave.open(tmp_name, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            frames = wf.readframes(n_frames)

        # 3. 转单声道
        if n_channels != 1:
            frames = audioop.tomono(frames, sampwidth, 1.0, 1.0)
            n_channels = 1

        # 4. 转 16bit
        if sampwidth != 2:
            frames = audioop.lin2lin(frames, sampwidth, 2)
            sampwidth = 2

        # 5. 重采样到 16000Hz
        if framerate != 16000:
            frames, _ = audioop.ratecv(
                frames, sampwidth, n_channels,
                framerate, 16000, None
            )
            framerate = 16000

        print(f"[TTS] Generated PCM length={len(frames)} bytes")
        return frames

    finally:
        if tmp_name and os.path.exists(tmp_name):
            os.remove(tmp_name)


# PRE-GENERATED TTS - COMMENTED OUT (now dynamically generating from LLM responses)
# print("[TTS] Pre-generating TTS PCM ...")
# TTS_PCM = generate_tts_pcm(REPLY_TEXT)
# print("[TTS] Ready.")

print("[TTS] TTS engine ready (will generate dynamically from LLM responses)")


@app.route("/api/tts", methods=["GET"])
def tts_endpoint():
    """
    根据存储的最新回复文本生成TTS音频，流式返回PCM数据。
    ESP32直接接收并播放，不需要base64解码，节省内存。
    """
    response_text = conversation_manager.last_response

    if not response_text:
        # 如果没有回复文本，返回空音频
        return Response(b"", mimetype="application/octet-stream")

    try:
        # 实时生成TTS音频
        tts_pcm = generate_tts_pcm(response_text)
        print(f"[TTS] Sending {len(tts_pcm)} bytes to ESP32")

        # 清空已使用的回复文本
        conversation_manager.last_response = ""

        return Response(tts_pcm, mimetype="application/octet-stream")

    except Exception as e:
        print(f"[TTS] Error: {e}")
        return Response(b"", mimetype="application/octet-stream")


@app.route("/api/tts_test", methods=["GET"])
def tts_test():
    """
    Test endpoint - generates a simple test TTS audio.
    ESP32 can play it directly as 16kHz 16bit mono PCM.
    """
    # Generate test audio on-the-fly instead of using pre-generated
    test_text = "TTS test successful. System is ready."
    try:
        tts_pcm = generate_tts_pcm(test_text)
        return Response(tts_pcm, mimetype="application/octet-stream")
    except Exception as e:
        print(f"[TTS Test] Error: {e}")
        return Response(b"", mimetype="application/octet-stream")

@app.route("/api/gesture_status", methods=["GET"])
def gesture_status():
    """
    返回最近一次识别到的手势。
    如果超过 3 秒没有新的手势，则认为当前没有手势（返回 null）。
    """
    with gesture_lock:
        g = latest_gesture
        t = latest_gesture_time

    now = time.time()
    if t == 0 or (now - t) > 3.0:
        # 超过 3 秒没更新，当作没有手势
        g_out = None
    else:
        g_out = g

    return jsonify({
        "gesture": g_out,
        "timestamp": t
    })



if __name__ == "__main__":
    print("=" * 60)
    print("Smart Plant Web Monitoring System + ESP32 STT/TTS Server")
    print("=" * 60)
    print("Local access:   http://localhost:8000")
    print("LAN access:     http://<your-laptop-IP>:8000")
    print("STT endpoint:   POST /api/stt")
    print("TTS test:       GET  /api/tts_test")
    print("=" * 60)
    # Start background gesture recognition thread
    t = threading.Thread(target=gesture_worker, daemon=True)
    t.start()
    # Start Flask server
    app.run(host="0.0.0.0", port=8000, debug=False)

# ================== ESP32-CAM 手势识别后台线程 ==================

latest_gesture = None       # 最近一次识别到的手势
latest_gesture_time = 0.0   # 时间戳
gesture_lock = threading.Lock()
