# main.py
import time
import usocket as socket
import ujson

from wifi_manager import connect_wifi
from mic_module import MicRecorder
from config import (
    MIC_SAMPLE_RATE,
    MIC_BITS,
    MIC_BUFFER_BYTES,
    SERVER_IP,
    SERVER_PORT,
    AUDIO_API_PATH,
    DEVICE_ID,
)

RECORD_SECONDS = 3   # 先 3 秒试一下，成功后可以再加长


def record_and_stream(mic, seconds):
    """
    边录音边通过 HTTP POST 推给服务器。
    不在 ESP32 上保留整段音频，只占用 1KB 左右的缓冲。
    """
    bytes_per_sample = MIC_BITS // 8  # 16bit -> 2 bytes
    total_bytes = MIC_SAMPLE_RATE * bytes_per_sample * seconds

    print("Will stream {} seconds, total bytes = {}".format(seconds, total_bytes))

    # 1. 建立 TCP 连接
    addr_info = socket.getaddrinfo(SERVER_IP, SERVER_PORT)[0][-1]
    s = socket.socket()
    s.connect(addr_info)

    path = AUDIO_API_PATH + "?device_id=" + DEVICE_ID

    # 2. 发送 HTTP 头
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

    # 3. 边录边发送音频
    bytes_sent = 0
    mv = memoryview(mic.buf)

    while bytes_sent < total_bytes:
        remaining = total_bytes - bytes_sent
        this_chunk = MIC_BUFFER_BYTES if remaining >= MIC_BUFFER_BYTES else remaining

        n = mic.i2s.readinto(mv[:this_chunk])
        if not n:
            # 读不到就等一下再读
            time.sleep_ms(2)
            continue

        s.write(mv[:n])
        bytes_sent += n

        if bytes_sent % (MIC_BUFFER_BYTES * 10) == 0:
            print("  streamed bytes: {}/{}".format(bytes_sent, total_bytes))

    print("Streaming done, total sent:", bytes_sent)

    # 4. 读取服务器响应
    response = b""
    while True:
        data = s.recv(512)
        if not data:
            break
        response += data

    s.close()

    # 5. 解析 HTTP 响应，提取 JSON body
    try:
        header, body = response.split(b"\r\n\r\n", 1)
    except ValueError:
        print("Failed to split HTTP response, raw:", response)
        return None

    # body 是 JSON，比如 {"text": "..."}
    try:
        obj = ujson.loads(body)
    except Exception as e:
        print("JSON parse error:", e)
        print("Body:", body)
        return None

    text = obj.get("text") or obj.get("transcript")
    print("Server transcript:", text)
    return text


def main():
    if not connect_wifi():
        print("WiFi connect failed, exit.")
        return

    mic = MicRecorder()

    try:
        time.sleep(1)
        text = record_and_stream(mic, RECORD_SECONDS)

        print("=== FINAL RESULT ===")
        print(text)

    except Exception as e:
        print("Unexpected error in main():", e)

    finally:
        mic.deinit()
        print("Mic deinit, done.")


if __name__ == "__main__":
    main()
