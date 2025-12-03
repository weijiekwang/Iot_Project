import speech_recognition as sr
import threading
import time

class VoiceRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = True
        
        # 调整环境噪音
        print("正在校准麦克风，请保持安静...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print("校准完成！")
    
    def listen_once(self):
        """监听一次语音输入"""
        try:
            with self.microphone as source:
                print("\n🎤 正在监听... (请说英语)")
                # 设置超时和短语时间限制
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
            print("⏳ 正在识别...")
            # 使用Google语音识别API（免费）
            text = self.recognizer.recognize_google(audio, language='en-US')
            print(f"✅ 你说: {text}")
            return text
            
        except sr.WaitTimeoutError:
            print("⚠️  没有检测到语音")
            return None
        except sr.UnknownValueError:
            print("❌ 无法识别语音，请说清楚一点")
            return None
        except sr.RequestError as e:
            print(f"❌ 识别服务出错: {e}")
            return None
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            return None
    
    def continuous_listen(self):
        """持续监听模式"""
        print("\n" + "=" * 50)
        print("🎙️  语音识别系统已启动")
        print("=" * 50)
        print("模式: 持续监听")
        print("语言: 英语 (English)")
        print("按 Ctrl+C 退出")
        print("=" * 50 + "\n")
        
        while self.is_listening:
            text = self.listen_once()
            if text:
                # 这里可以添加对话逻辑
                # 后续可以调用AI API处理对话
                pass
            time.sleep(0.5)  # 短暂延迟避免过于频繁
    
    def stop(self):
        """停止监听"""
        self.is_listening = False

def main():
    """主函数"""
    try:
        recognizer = VoiceRecognizer()
        recognizer.continuous_listen()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")

if __name__ == "__main__":
    main()
