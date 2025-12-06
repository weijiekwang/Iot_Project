# server.py
# 功能：
#  1) /api/stt  ：接收 ESP32 发送的原始 PCM，做语音识别，返回 {"text": "..."}
#  2) /api/tts_test ：生成 "I love Columbia, test test test" 的 16kHz 16bit mono PCM，原样返回

from flask import Flask, request, jsonify, Response
import io
import wave
import speech_recognition as sr

import pyttsx3
import audioop
import tempfile
import os

app = Flask(__name__)

# ====== 语音识别部分 ======
recognizer = sr.Recognizer()

@app.route("/", methods=["GET"])
def index():
    return "ESP32 STT/TTS server is running."


@app.route("/api/stt", methods=["POST"])
def stt_endpoint():
    """
    接收 ESP32 发送的原始 PCM（16kHz,16bit,mono），
    转成 WAV 后，用 SpeechRecognition 调用 Google STT。
    """
    raw = request.data
    if not raw:
        return jsonify({"error": "no audio data"}), 400

    print(f"[INFO] Received audio bytes: {len(raw)}")

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
        print("[WARN] Speech was not understood.")
        text = ""
    except sr.RequestError as e:
        print(f"[ERROR] STT API request failed: {e}")
        return jsonify({"error": "stt_request_failed"}), 500
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return jsonify({"error": "internal_error"}), 500

    return jsonify({
        "text": text,
        "raw_bytes": len(raw)
    })


# ====== TTS 部分：在服务器上把一句话变成 16kHz 16bit mono PCM ======

REPLY_TEXT = "I love Columbia, test test test"

def generate_tts_pcm(text: str) -> bytes:
    """
    用 pyttsx3 生成 text 的 WAV，再转成 16kHz 16bit mono PCM。
    返回：纯 PCM bytes（不含 WAV 头）。
    """
    # 1. 用 pyttsx3 输出到临时 WAV 文件
    engine = pyttsx3.init()
    tmp_name = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_name = tmp.name

        engine.save_to_file(text, tmp_name)
        engine.runAndWait()

        # 2. 读 WAV 内容
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

        # 5. 转采样率到 16000
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


# 在服务器启动时预生成一次 TTS PCM，后续直接复用
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
    # 监听所有网卡，端口 8000
    app.run(host="0.0.0.0", port=8000, debug=True)
