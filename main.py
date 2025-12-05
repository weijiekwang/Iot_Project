# main.py
import time
import urequests as requests

from wifi_manager import connect_wifi
from mic_module import MicRecorder
from config import (
    MIC_SAMPLE_RATE,
    MIC_BITS,
    MIC_BUFFER_BYTES,
    SERVER_BASE_URL,
    AUDIO_API_PATH,
    DEVICE_ID,
)

RECORD_SECONDS = 5   # 先录 5 秒测试

def record_audio(mic, seconds):
    bytes_per_sample = MIC_BITS // 8  # 16bit -> 2 bytes
    total_bytes = MIC_SAMPLE_RATE * bytes_per_sample * seconds

    num_chunks = total_bytes // MIC_BUFFER_BYTES
    if total_bytes % MIC_BUFFER_BYTES != 0:
        num_chunks += 1

    print("Start recording {} seconds...".format(seconds))
    print("Target bytes:", total_bytes,
          "buffer size:", MIC_BUFFER_BYTES,
          "chunks:", num_chunks)

    chunks = []
    for i in range(num_chunks):
        data = mic.read_chunk()
        if data:
            chunks.append(data)
        if i % 10 == 0:
            print("  recorded chunk {}/{}".format(i + 1, num_chunks))
        time.sleep_ms(5)

    pcm = b"".join(chunks)
    print("Recording done, got bytes:", len(pcm))
    return pcm


def send_to_server(pcm_bytes):
    if not pcm_bytes:
        print("No audio data to send")
        return None

    url = SERVER_BASE_URL + AUDIO_API_PATH + "?device_id=" + DEVICE_ID
    headers = {"Content-Type": "application/octet-stream"}

    print("Uploading {} bytes to {}".format(len(pcm_bytes), url))

    try:
        resp = requests.post(url, data=pcm_bytes, headers=headers)
        print("HTTP status:", resp.status_code)

        if resp.status_code != 200:
            try:
                print("Response text:", resp.text)
            except Exception:
                pass
            resp.close()
            return None

        try:
            data = resp.json()
        except Exception:
            try:
                print("Raw response:", resp.text)
            except Exception:
                pass
            resp.close()
            return None

        resp.close()

        text = data.get("text") or data.get("transcript")
        if text is None:
            print("No 'text' or 'transcript' in JSON:", data)
            return None

        print("Server transcript:", text)
        return text

    except Exception as e:
        print("Error sending to server:", e)
        return None


def main():
    if not connect_wifi():
        print("WiFi connect failed, exit.")
        return

    mic = MicRecorder()

    try:
        time.sleep(1)

        pcm = record_audio(mic, RECORD_SECONDS)

        text = send_to_server(pcm)

        print("=== FINAL RESULT ===")
        print(text)

    except Exception as e:
        print("Unexpected error in main():", e)

    finally:
        mic.deinit()
        print("Mic deinit, done.")


if __name__ == "__main__":
    main()
