# server.py
# ESP32 STT/TTS + 简单 Web 仪表盘（假数据）

from flask import Flask, request, jsonify, Response
import io
import wave
import math
import random
import time

import speech_recognition as sr

app = Flask(__name__)

# =======================
# 1. 首页 HTML（内嵌字符串）
# =======================

INDEX_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>智能盆栽监控系统</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(135deg,#4b6cb7,#182848);
      min-height: 100vh;
      color: #fff;
    }
    .container {
      max-width: 1200px;
      margin: 40px auto;
      padding: 20px;
    }
    .card {
      background: rgba(255,255,255,0.1);
      border-radius: 16px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.25);
      padding: 24px;
      backdrop-filter: blur(12px);
    }
    .header {
      text-align: center;
      margin-bottom: 24px;
    }
    .header h1 {
      font-size: 32px;
      margin-bottom: 6px;
    }
    .header p {
      opacity: 0.8;
      font-size: 14px;
    }
    .grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 24px;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat-card {
      background: linear-gradient(135deg,#6a11cb,#2575fc);
      border-radius: 14px;
      padding: 18px;
      text-align: center;
    }
    .stat-label {
      font-size: 14px;
      opacity: 0.85;
    }
    .stat-value {
      font-size: 28px;
      font-weight: bold;
      margin-top: 8px;
    }
    .section-title {
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .section-title span {
      font-size: 20px;
    }
    canvas {
      width: 100%;
      height: 260px;
      background: rgba(0,0,0,0.05);
      border-radius: 12px;
    }
    .btn {
      display: block;
      width: 100%;
      border: none;
      border-radius: 999px;
      padding: 12px 16px;
      font-size: 15px;
      margin-bottom: 14px;
      cursor: pointer;
      color: #fff;
    }
    .btn-green { background: #16a34a; }
    .btn-red   { background: #dc2626; }
    .btn-blue  { background: #2563eb; }
    .status-dot {
      display: inline-block;
      width: 10px; height: 10px;
      border-radius: 50%;
      margin-right: 6px;
      background: #ef4444;
    }
    .status-dot.on { background: #22c55e; }
    .small {
      font-size: 12px;
      opacity: 0.7;
      margin-top: 6px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <div class="header">
        <h1>🌱 智能盆栽监控系统</h1>
        <p>实时监控 | 语音对话 | 动作识别（当前数据为示例假数据，ESP32 接口独立运行）</p>
      </div>

      <div class="grid">
        <!-- 左侧：湿度监控 -->
        <div>
          <div class="section-title">
            <span>📊</span>湿度监控（过去 24 小时）
          </div>
          <div class="stats">
            <div class="stat-card">
              <div class="stat-label">当前湿度(%)</div>
              <div class="stat-value" id="cur-humidity">66</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">平均湿度(%)</div>
              <div class="stat-value" id="avg-humidity">70.8</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">数据点数</div>
              <div class="stat-value" id="data-count">21</div>
            </div>
          </div>
          <canvas id="humidity-chart"></canvas>
          <div class="small">图表数据为随机示例，用于 UI 演示，不代表真实传感器读数。</div>
        </div>

        <!-- 右侧：对话控制 -->
        <div>
          <div class="section-title">
            <span>💬</span>对话控制
          </div>
          <button class="btn btn-red" id="status-btn">
            <span class="status-dot" id="status-dot"></span>
            对话已关闭
          </button>
          <button class="btn btn-green" onclick="fakeOpenDialog()">
            🟢 开启对话（示例）
          </button>
          <button class="btn btn-red" onclick="fakeCloseDialog()">
            🔴 关闭对话（示例）
          </button>
          <button class="btn btn-blue" onclick="reloadFakeData()">
            🔄 刷新假数据
          </button>
          <div class="small">
            ESP32 的麦克风 / 扬声器 / 摄像头通过独立接口 /api/stt 和 /api/tts_test 与本服务器通信，
            与本页示例 UI 相互独立。
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const chartCanvas = document.getElementById('humidity-chart');
    const ctx = chartCanvas.getContext('2d');
    const W = chartCanvas.width;
    const H = chartCanvas.height;

    function drawFakeChart() {
      ctx.clearRect(0, 0, W, H);
      ctx.strokeStyle = 'rgba(255,255,255,0.6)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      let points = [];
      for (let i = 0; i < 24; i++) {
        const x = (W - 40) * i / 23 + 20;
        const base = 65 + 10 * Math.sin(i / 24 * Math.PI * 4);
        const noise = (Math.random() - 0.5) * 8;
        const y = H - (base + noise - 50) / 40 * (H - 40) - 20;
        points.push({x, y});
      }
      for (let i = 0; i < points.length; i++) {
        if (i === 0) ctx.moveTo(points[i].x, points[i].y);
        else ctx.lineTo(points[i].x, points[i].y);
      }
      ctx.stroke();
    }

    function reloadFakeData() {
      const cur = 60 + Math.round(Math.random() * 20);
      const avg = 65 + Math.round(Math.random() * 15);
      const cnt = 18 + Math.floor(Math.random() * 10);
      document.getElementById('cur-humidity').innerText = cur;
      document.getElementById('avg-humidity').innerText = avg;
      document.getElementById('data-count').innerText = cnt;
      drawFakeChart();
    }

    function fakeOpenDialog() {
      document.getElementById('status-btn').innerText = '🟢 对话已开启';
      document.getElementById('status-dot').classList.add('on');
    }

    function fakeCloseDialog() {
      document.getElementById('status-btn').innerText = '❌ 对话已关闭';
      document.getElementById('status-dot').classList.remove('on');
    }

    reloadFakeData();
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    """返回内嵌 HTML 页面（不依赖 templates/index.html）"""
    return Response(INDEX_HTML, mimetype="text/html")


# =======================
# 2. STT：ESP32 音频上行 -> 文本
# =======================

recognizer = sr.Recognizer()

SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2      # 16-bit
CHANNELS = 1

@app.route("/api/stt", methods=["POST"])
def api_stt():
    """
    接收 ESP32 发送的原始 PCM (16kHz, 16bit, mono)，
    转成 WAV -> SpeechRecognition -> 文本。
    返回 JSON: { success: bool, transcript: str | None, error?: str }
    """
    try:
        raw = request.get_data()
        print(f"[STT] received {len(raw)} bytes")

        if not raw:
            return jsonify({"success": False, "transcript": None,
                            "error": "no audio data"}), 400

        # 封装成 WAV 放到内存
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(SAMPLE_WIDTH)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(raw)
        buf.seek(0)

        with sr.AudioFile(buf) as source:
            audio = recognizer.record(source)

        try:
            text = recognizer.recognize_google(audio, language="en-US")
        except sr.UnknownValueError:
            text = ""
        except Exception as e:
            print("[STT] recognize error:", e)
            return jsonify({"success": False, "transcript": None,
                            "error": str(e)}), 500

        print("[STT] transcript:", text)
        return jsonify({"success": True, "transcript": text})

    except Exception as e:
        print("[STT] fatal error:", e)
        return jsonify({"success": False, "transcript": None,
                        "error": str(e)}), 500


# =======================
# 3. TTS：简单 beep 测试 Speaker
# =======================

def generate_beep(duration_sec=2.0, freq=440.0):
    """
    生成 16kHz / 16bit / mono 的正弦波，作为测试用“语音”。
    """
    n = int(SAMPLE_RATE * duration_sec)
    pcm = bytearray()
    for i in range(n):
        v = 0.6 * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
        s = int(v * 32767)
        pcm += s.to_bytes(2, "little", signed=True)
    return bytes(pcm)


@app.route("/api/tts_test", methods=["GET"])
def api_tts_test():
    """
    返回一段 beep 的 PCM，ESP32 直接 I2S 播放。
    以后想换真正的 TTS，只要保持返回 16bit PCM 即可。
    """
    text = request.args.get("text", "I love Columbia, test test test")
    print(f"[TTS] request text='{text}' (当前用 beep 代替真实语音)")
    pcm = generate_beep(duration_sec=2.0, freq=660.0)
    return Response(pcm, mimetype="application/octet-stream")


# =======================
# 4. 启动
# =======================

if __name__ == "__main__":
    print("============================================================")
    print("🌱 智能盆栽 Web 监控系统 + ESP32 STT/TTS Server")
    print("============================================================")
    print("本机访问:   http://localhost:8000")
    print("局域网访问: http://<你的笔记本IP>:8000")
    print("STT 接口:   POST /api/stt")
    print("TTS 测试:   GET  /api/tts_test")
    print("============================================================")

    app.run(host="0.0.0.0", port=8000, debug=True)
