# main.py
# 流程：
# 1. WiFi 连接
# 2. 持续监听模式：不断录音并发送到服务器
# 3. 说 "hello world" 开启对话，说 "bye bye" 关闭对话
# 4. 接收服务器的语音回复并通过扬声器播放

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

RECORD_SECONDS = 3   # 每次录音3秒


def record_and_stream(mic, seconds):
    """
    边录音边通过 HTTP POST 推给 /api/stt，
    返回完整的对话响应数据。
    """
    bytes_per_sample = MIC_BITS // 8  # 16bit -> 2 bytes
    total_bytes = MIC_SAMPLE_RATE * bytes_per_sample * seconds

    print("Recording {} seconds...".format(seconds))

    # 清空I2S缓冲区，确保麦克风状态正常
    try:
        dummy_buf = bytearray(512)
        for _ in range(5):
            mic.i2s.readinto(dummy_buf)
            time.sleep_ms(10)
    except:
        pass

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

    print("Audio sent, waiting for response...")

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
        print("Failed to split HTTP response")
        return None

    try:
        obj = ujson.loads(body)
    except Exception as e:
        print("JSON parse error:", e)
        return None

    # 返回完整的响应对象
    return obj


def stream_tts_from_server():
    """
    从服务器流式获取TTS音频并播放，避免大内存分配。
    一边接收一边播放，不在ESP32上存储整段音频。
    """
    speaker = SpeakerPlayer()

    try:
        # 建立TCP连接
        addr_info = socket.getaddrinfo(SERVER_IP, SERVER_PORT)[0][-1]
        s = socket.socket()
        s.connect(addr_info)

        # 发送HTTP GET请求
        path = "/api/tts"
        req = (
            "GET {} HTTP/1.1\r\n"
            "Host: {}:{}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).format(path, SERVER_IP, SERVER_PORT)

        s.write(req.encode("utf-8"))
        print("Requesting TTS audio...")

        # 读取HTTP响应头
        buf = b""
        while b"\r\n\r\n" not in buf:
            data = s.recv(256)
            if not data:
                break
            buf += data
            if len(buf) > 1024:
                break

        # 分离头和体
        if b"\r\n\r\n" in buf:
            header, body = buf.split(b"\r\n\r\n", 1)
        else:
            header = buf
            body = b""

        # body中已有第一块音频数据
        if body:
            speaker.play_chunk(body)

        # 流式接收并播放剩余音频
        total_bytes = len(body)
        while True:
            data = s.recv(512)
            if not data:
                break
            speaker.play_chunk(data)
            total_bytes += len(data)

        s.close()
        print("Played {} bytes".format(total_bytes))

    except Exception as e:
        print("TTS playback error:", e)

    finally:
        speaker.deinit()
        # 等待扬声器完全释放I2S总线
        time.sleep_ms(100)


def main():
    # 1. WiFi
    if not connect_wifi():
        print("WiFi connect failed, exit.")
        return

    print("=" * 50)
    print("Smart Plant - Continuous Listening Mode")
    print("Say 'Hello World' to start conversation")
    print("Say 'Bye Bye' to end conversation")
    print("=" * 50)

    # 2. 初始化麦克风
    mic = MicRecorder()
    conversation_active = False

    try:
        # 持续监听循环
        while True:
            print("\n[Listening...]")

            # 录音并发送到服务器
            result = record_and_stream(mic, RECORD_SECONDS)

            if result:
                user_text = result.get("text", "")
                response_text = result.get("response", "")
                action = result.get("action", "")
                has_audio = result.get("has_audio", False)
                conversation_active = result.get("conversation_active", False)

                print("\n" + "=" * 50)
                print("RESULT FROM SERVER:")
                print("  User text: '{}'".format(user_text))
                print("  Response: '{}'".format(response_text))
                print("  Action: '{}'".format(action))
                print("  Has audio: {}".format(has_audio))
                print("  Conversation active: {}".format(conversation_active))
                print("=" * 50)

                # 显示识别的文字
                if user_text:
                    print("\n[YOU]: {}".format(user_text))

                # 显示机器人的回复
                if response_text:
                    print("[BOT]: {}".format(response_text))

                    # 流式播放语音回复（避免大内存分配）
                    if has_audio:
                        print("[播放语音回复...]")
                        stream_tts_from_server()

                        # 重新初始化麦克风I2S（解决扬声器使用后的I2S冲突）
                        print("[重新初始化麦克风...]")
                        mic.reinit()
                        time.sleep_ms(50)
                else:
                    print("[BOT]: (no response)")

                # 处理对话状态变化
                if action == "start_conversation":
                    print("\n*** Conversation Started! ***\n")
                elif action == "end_conversation":
                    print("\n*** Conversation Ended ***\n")

            # 短暂延迟
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\nStopping...")

    except Exception as e:
        print("Error:", e)

    finally:
        mic.deinit()
        print("System shutdown complete.")


if __name__ == "__main__":
    main()
