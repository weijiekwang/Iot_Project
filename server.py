# server.py
# 简单语音识别服务器：
# 接收 ESP32 发送的原始 PCM 音频（16kHz, 16-bit, mono）
# -> 转成 WAV
# -> 用 speech_recognition 做 STT
# -> 返回 {"text": "..."} 给 ESP32

from flask import Flask, request, jsonify
import io
import wave
import speech_recognition as sr

app = Flask(__name__)

# 全局复用一个 recognizer，避免每次创建
recognizer = sr.Recognizer()


@app.route("/", methods=["GET"])
def index():
    return "ESP32 STT server is running."


@app.route("/api/stt", methods=["POST"])
def stt_endpoint():
    # 1. 拿到原始音频数据（ESP32 发送的 body）
    raw = request.data
    if not raw:
        return jsonify({"error": "no audio data"}), 400

    print(f"[INFO] Received audio bytes: {len(raw)}")

    # 2. 把原始 PCM 包装成内存里的 WAV 文件
    #   - 单声道（1 channel）
    #   - 16-bit（2 bytes per sample）
    #   - 16 kHz 采样率（和 ESP32 端一致）
    wav_buf = io.BytesIO()
    with wave.open(wav_buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)        # 16-bit = 2 bytes
        wf.setframerate(16000)    # 和 config.py 里 MIC_SAMPLE_RATE 一致
        wf.writeframes(raw)

    wav_buf.seek(0)

    # 3. 用 speech_recognition 进行语音识别
    text = ""
    try:
        with sr.AudioFile(wav_buf) as source:
            audio = recognizer.record(source)

        # 你可以改 language，比如 "zh-CN" 识别中文
        text = recognizer.recognize_google(audio, language="en-US")
        print(f"[STT] {text}")

    except sr.UnknownValueError:
        print("[WARN] Speech was not understood.")
        text = ""
    except sr.RequestError as e:
        print(f"[ERROR] STT API request failed: {e}")
        return jsonify({"error": "stt_request_failed"}), 500
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return jsonify({"error": "internal_error"}), 500

    # 4. 返回 JSON 给 ESP32
    return jsonify({
        "text": text,
        "raw_bytes": len(raw)
    })


if __name__ == "__main__":
    # 监听所有网卡，端口 8000（和 ESP32 config 对应）
    app.run(host="0.0.0.0", port=8000, debug=True)
