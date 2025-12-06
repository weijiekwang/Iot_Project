# main.py
# 流程：
# 1. WiFi 连接
# 2. I2S 麦克录音 + 流式 POST 到 /api/stt，拿回文字
# 3. 释放麦克 I2S
# 4. 初始化 Speaker I2S
# 5. GET /api/tts_test，流式播放服务器返回的 PCM

import time
import usocket as socket
import ujson

from wifi_manager import connect_wifi
from mic_module import MicRecorder
from speaker_module import SpeakerPlayer
from config import (
    MIC_SAMPLE_RATE,
    MIC_BITS,
    MIC_BUFFER_BYTES,
    SERVER_IP,
    SERVER_PORT,
    AUDIO_API_PATH,
    DEVICE_ID,
)

RECORD_SECONDS = 3   # 录 3 秒够测试了


def record_and_stream(mic, seconds):
    """
    边录音边通过 HTTP POST 推给 /api/stt，
    最后解析 JSON，返回 text。
    """
    bytes_per_sample = MIC_BITS // 8  # 16bit -> 2 bytes
    total_bytes = MIC_SAMPLE_RATE * bytes_per_sample * seconds

    print("Will stream {} seconds, total bytes = {}".format(seconds, total_bytes))

    # 1. 建 TCP
    addr_info = socket.getaddrinfo(SERVER_IP, SERVER_PORT)[0][-1]
    s = socket.socket()
    s.connect(addr_info)

    path = AUDIO_API_PATH + "?device_id=" + DEVICE_ID

    headers = (
        "POST {} HTTP/1.1\r\n"
        "Host: {}:{}\r\n"
        "Content-Type: application/octet-stream\r\n"
        "Content-Length: {}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).format(path, SERVER_IP, SERVER_PORT, total_bytes)

    s.write(headers.encode("utf-8"))
    print("HTTP headers sent.")

    # 2. 边录边发
    bytes_sent = 0
    mv = memoryview(mic.buf)

    while bytes_sent < total_bytes:
        remaining = total_bytes - bytes_sent
        this_chunk = MIC_BUFFER_BYTES if remaining >= MIC_BUFFER_BYTES else remaining

        n = mic.i2s.readinto(mv[:this_chunk])
        if not n:
            time.sleep_ms(2)
            continue

        s.write(mv[:n])
        bytes_sent += n

        if bytes_sent % (MIC_BUFFER_BYTES * 10) == 0:
            print("  streamed bytes: {}/{}".format(bytes_sent, total_bytes))

    print("Streaming done, total sent:", bytes_sent)

    # 3. 读取 HTTP 响应
    response = b""
    while True:
        data = s.recv(512)
        if not data:
            break
        response += data

    s.close()

    # 4. 解析 JSON
    try:
        header, body = response.split(b"\r\n\r\n", 1)
    except ValueError:
        print("Failed to split HTTP response, raw:", response)
        return None

    try:
        obj = ujson.loads(body)
    except Exception as e:
        print("JSON parse error:", e)
        print("Body:", body)
        return None

    text = obj.get("text") or obj.get("transcript")
    print("Server transcript:", text)
    return text


def play_tts_from_server():
    """
    通过 HTTP GET /api/tts_test 从服务器拉取 TTS PCM，
    一边收一边通过 I2S 播放，不在 ESP32 上存整段。
    """
    speaker = SpeakerPlayer()

    try:
        addr_info = socket.getaddrinfo(SERVER_IP, SERVER_PORT)[0][-1]
        s = socket.socket()
        s.connect(addr_info)

        path = "/api/tts_test"
        req = (
            "GET {} HTTP/1.1\r\n"
            "Host: {}:{}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).format(path, SERVER_IP, SERVER_PORT)

        s.write(req.encode("utf-8"))
        print("TTS HTTP GET sent.")

        # 读取 HTTP header
        buf = b""
        while b"\r\n\r\n" not in buf:
            data = s.recv(256)
            if not data:
                break
            buf += data
            if len(buf) > 1024:
                break  # header 不会太长

        if b"\r\n\r\n" in buf:
            header, body = buf.split(b"\r\n\r\n", 1)
        else:
            header = buf
            body = b""

        print("TTS response header:")
        try:
            print(header.decode())   # MicroPython 默认就按 strict 解码，header 是 ASCII，不会出问题
        except Exception as e:
            print("header decode error:", e)
            print(header)

        # body 里已经有第一块音频数据了
        if body:
            speaker.play_chunk(body)

        # 持续接收剩余音频
        while True:
            data = s.recv(512)
            if not data:
                break
            speaker.play_chunk(data)

        s.close()
        print("TTS playback finished.")

    except Exception as e:
        print("Error playing TTS:", e)

    finally:
        speaker.deinit()


def main():
    # 1. WiFi
    if not connect_wifi():
        print("WiFi connect failed, exit.")
        return

    # 2. 麦克录音 + STT
    mic = MicRecorder()
    text = None

    try:
        time.sleep(1)
        text = record_and_stream(mic, RECORD_SECONDS)

        print("=== FINAL RESULT (STT) ===")
        print(text)

    except Exception as e:
        print("Unexpected error in STT part:", e)

    finally:
        mic.deinit()
        print("Mic deinit, done.")

    # 3. 播放固定 TTS
    print("Now play TTS: 'I love Columbia, test test test'")
    play_tts_from_server()


if __name__ == "__main__":
    main()
