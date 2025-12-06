# server.py
# 功能：
#   1) Web 页面（/）：显示一个“智能盆栽监控系统”的假数据仪表盘
#   2) /api/stt ：接收 ESP32 发送的原始 PCM，做语音识别，返回 {"text": "..."}
#   3) /api/tts_test ：在 PC 上把一句话变成 16kHz 16bit mono PCM，给 ESP32 播放

from flask import Flask, request, jsonify, Response
import io
import wave
import speech_recognition as sr

import pyttsx3
import audioop
import tempfile
import os

app = Flask(__name__)

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
            </div>
            <p class="hint">
                💡 提示：<br>
                · ESP32 通过 <code>/api/stt</code> 上传麦克风音频，由服务器转文字；<br>
                · ESP32 通过 <code>/api/tts_test</code> 获取合成语音 PCM，在本地扬声器播放。
            </p>
        </div>
    </div>
</div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return INDEX_HTML


# ========= STT：ESP32 -> 服务器（音频转文字） =========

recognizer = sr.Recognizer()

@app.route("/api/stt", methods=["POST"])
def stt_endpoint():
    """
    接收 ESP32 发送的原始 PCM（16kHz,16bit,mono），
    转成 WAV 后，用 SpeechRecognition 调用 Google STT。
    """
    raw = request.data
    if not raw:
        return jsonify({"error": "no audio data"}), 400

    print(f"[STT] Received audio bytes: {len(raw)}")

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
            audio = recognizer.record(source)

        # 现在用英文，如果想识别中文改成 language="zh-CN"
        text = recognizer.recognize_google(audio, language="en-US")
        print(f"[STT] {text}")

    except sr.UnknownValueError:
        print("[STT] Speech was not understood.")
        text = ""
    except sr.RequestError as e:
        print(f"[STT] API request failed: {e}")
        return jsonify({"error": "stt_request_failed"}), 500
    except Exception as e:
        print(f"[STT] Unexpected error: {e}")
        return jsonify({"error": "internal_error"}), 500

    return jsonify({
        "text": text,
        "raw_bytes": len(raw)
    })


# ========= TTS：服务器 -> ESP32（文字转语音 PCM） =========

REPLY_TEXT = "I love Columbia, test test test"

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


print("[TTS] Pre-generating TTS PCM ...")
TTS_PCM = generate_tts_pcm(REPLY_TEXT)
print("[TTS] Ready.")


@app.route("/api/tts_test", methods=["GET"])
def tts_test():
    """
    返回预生成好的 TTS PCM，类型为 application/octet-stream，
    ESP32 端直接当成 16kHz 16bit mono PCM 播放即可。
    """
    return Response(TTS_PCM, mimetype="application/octet-stream")


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
