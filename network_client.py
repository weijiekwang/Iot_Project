# network_client.py
import ujson
import ubinascii
import urequests as requests

from config import SERVER_BASE_URL, AUDIO_API_PATH, DEVICE_ID

def send_audio_and_get_result(pcm_bytes):
    """
    向服务器发送一段 PCM 音频，返回解析后的 dict：
    {
      "gesture": str or None,
      "oled_text": str or None,
      "reply_text": str or None,
      "reply_audio_pcm": bytes or b""
    }
    """
    url = SERVER_BASE_URL + AUDIO_API_PATH + "?device_id=" + DEVICE_ID
    headers = {"Content-Type": "application/octet-stream"}

    try:
        resp = requests.post(url, data=pcm_bytes, headers=headers)
        if resp.status_code != 200:
            print("Server error:", resp.status_code)
            resp.close()
            return None

        data = resp.json()
        resp.close()

        result = {
            "gesture": data.get("gesture"),
            "oled_text": data.get("oled_text"),
            "reply_text": data.get("reply_text"),
            "reply_audio_pcm": b""
        }

        b64_audio = data.get("reply_audio_b64")
        if b64_audio:
            try:
                result["reply_audio_pcm"] = ubinascii.a2b_base64(b64_audio)
            except Exception as e:
                print("Base64 decode error:", e)

        return result

    except Exception as e:
        print("HTTP error:", e)
        return None
