# main.py - 智能盆栽ESP32主程序
import time
import urequests as requests
import ujson

from wifi_manager import connect_wifi
from mic_module import MicRecorder
from speaker_module import SpeakerPlayer
from oled_module import OledDisplay
from camera_module import CameraModule
from config import (
    MIC_SAMPLE_RATE,
    MIC_BITS,
    MIC_BUFFER_BYTES,
    SERVER_BASE_URL,
    AUDIO_API_PATH,
    GESTURE_API_PATH,
    STATUS_API_PATH,
    DEVICE_ID,
    RECORD_SECONDS,
    GESTURE_CHECK_INTERVAL,
    CAMERA_ENABLED,
)

class SmartPlant:
    def __init__(self):
        self.oled = OledDisplay()
        self.oled.show_text("Smart Plant", "Initializing...")
        
        self.mic = MicRecorder()
        self.speaker = SpeakerPlayer()
        
        if CAMERA_ENABLED:
            try:
                self.camera = CameraModule()
            except Exception as e:
                print("Camera init failed:", e)
                self.camera = None
        else:
            self.camera = None
        
        self.conversation_active = False
        self.last_gesture_check = 0
        
        print("Smart Plant initialized!")
    
    def check_conversation_status(self):
        """检查服务器上的对话状态"""
        try:
            url = SERVER_BASE_URL + STATUS_API_PATH
            resp = requests.get(url, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                self.conversation_active = data.get("active", False)
                resp.close()
                return self.conversation_active
            
            resp.close()
            return False
            
        except Exception as e:
            print("Check status error:", e)
            return False
    
    def record_audio(self, seconds):
        """录制音频"""
        bytes_per_sample = MIC_BITS // 8
        total_bytes = MIC_SAMPLE_RATE * bytes_per_sample * seconds
        num_chunks = (total_bytes + MIC_BUFFER_BYTES - 1) // MIC_BUFFER_BYTES
        
        print("Recording {} seconds...".format(seconds))
        
        chunks = []
        for i in range(num_chunks):
            data = self.mic.read_chunk()
            if data:
                chunks.append(data)
            time.sleep_ms(5)
        
        pcm = b"".join(chunks)
        print("Recorded {} bytes".format(len(pcm)))
        return pcm
    
    def send_audio_to_server(self, pcm_bytes):
        """发送音频到服务器，获取识别和回复"""
        if not pcm_bytes:
            return None

        url = SERVER_BASE_URL + AUDIO_API_PATH
        headers = {"Content-Type": "application/octet-stream"}

        print("Uploading audio...")

        try:
            resp = requests.post(url, data=pcm_bytes, headers=headers)

            if resp.status_code != 200:
                print("Server error:", resp.status_code)
                resp.close()
                return None

            data = resp.json()
            resp.close()

            return {
                "text": data.get("text", ""),
                "response": data.get("response", ""),
                "action": data.get("action", ""),
                "conversation_active": data.get("conversation_active", False),
                "has_audio": data.get("has_audio", False),
                "audio_base64": data.get("audio_base64", "")
            }

        except Exception as e:
            print("Upload error:", e)
            return None
    
    def capture_and_send_gesture(self):
        """捕获图像并发送到服务器识别动作"""
        if not self.camera:
            return None
        
        try:
            # 捕获图像
            img_bytes = self.camera.capture_jpeg()
            if not img_bytes:
                return None
            
            # 发送到服务器
            url = SERVER_BASE_URL + GESTURE_API_PATH
            headers = {"Content-Type": "image/jpeg"}
            
            resp = requests.post(url, data=img_bytes, headers=headers)
            
            if resp.status_code == 200:
                data = resp.json()
                gesture = data.get("gesture")
                resp.close()
                return gesture
            
            resp.close()
            return None
            
        except Exception as e:
            print("Gesture capture error:", e)
            return None
    
    def play_response(self, text, audio_base64=None):
        """播放语音回复"""
        if text:
            print("Bot:", text)
            # 截断显示在OLED上（最多3行，每行16个字符）
            lines = self.split_text_to_lines(text, 16)
            self.oled.show_text(
                lines[0] if len(lines) > 0 else "",
                lines[1] if len(lines) > 1 else "",
                lines[2] if len(lines) > 2 else ""
            )

        # 如果有音频数据，播放出来
        if audio_base64:
            try:
                import ubinascii
                # 解码base64音频数据
                audio_pcm = ubinascii.a2b_base64(audio_base64)
                print("Playing audio, {} bytes".format(len(audio_pcm)))
                # 播放音频
                self.speaker.play_pcm(audio_pcm)
            except Exception as e:
                print("Audio play error:", e)
    
    def split_text_to_lines(self, text, max_len):
        """将文本分割成多行"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_len:
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def run(self):
        """主循环 - 持续监听模式"""
        self.oled.show_text("Smart Plant", "Ready!", "")
        time.sleep(1)

        print("=" * 50)
        print("Smart Plant System Running")
        print("Continuous Listening Mode")
        print("Say 'Hello World' to start conversation")
        print("=" * 50)

        try:
            while True:
                # 持续录音并发送到服务器
                self.oled.show_text("Listening...", "", "")

                # 录音
                pcm = self.record_audio(RECORD_SECONDS)

                self.oled.show_text("Processing...", "", "")

                # 发送到服务器
                result = self.send_audio_to_server(pcm)

                if result:
                    user_text = result.get("text", "")
                    response_text = result.get("response", "")
                    action = result.get("action", "")
                    has_audio = result.get("has_audio", False)
                    audio_base64 = result.get("audio_base64", "")
                    self.conversation_active = result.get("conversation_active", False)

                    if user_text:
                        print("You:", user_text)

                    if response_text:
                        # 播放响应（文字和语音）
                        self.play_response(response_text, audio_base64 if has_audio else None)
                        time.sleep(2)

                    # 根据动作更新状态
                    if action == "start_conversation":
                        self.oled.show_text("Conversation", "Started!", "")
                        time.sleep(1)
                    elif action == "end_conversation":
                        self.oled.show_text("Conversation", "Ended", "")
                        time.sleep(1)

                # 定期检查动作识别（如果有摄像头）
                current_time = time.time()
                if self.camera and current_time - self.last_gesture_check > GESTURE_CHECK_INTERVAL:
                    self.last_gesture_check = current_time
                    gesture = self.capture_and_send_gesture()
                    if gesture:
                        print("Gesture detected:", gesture)
                        self.oled.show_text("Gesture:", gesture, "")
                        time.sleep(1)

                # 短暂延迟，避免过于频繁
                time.sleep(0.3)

        except KeyboardInterrupt:
            print("\nStopping...")

        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        print("Cleaning up...")
        self.mic.deinit()
        self.speaker.deinit()
        if self.camera:
            self.camera.deinit()
        self.oled.show_text("Goodbye!", "", "")
        print("Done!")

def main():
    # 连接WiFi
    if not connect_wifi():
        print("WiFi failed, cannot continue")
        return
    
    # 创建并运行智能盆栽系统
    plant = SmartPlant()
    plant.run()

if __name__ == "__main__":
    main()
