import speech_recognition as sr
import threading
import time

class VoiceRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = True
        self.conversation_mode = False  # 对话模式标志
        
        # 调整环境噪音
        print("正在校准麦克风，请保持安静...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print("校准完成！")
    
    def listen_once(self):
        """监听一次语音输入"""
        try:
            with self.microphone as source:
                if self.conversation_mode:
                    print("\n🤖 [对话模式] 正在监听...")
                else:
                    print("\n🎤 正在监听... (说 'hello world' 开启对话)")
                
                # 设置超时和短语时间限制
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
            print("⏳ 正在识别...")
            # 使用Google语音识别API（免费）
            text = self.recognizer.recognize_google(audio, language='en-US')
            print(f"✅ 你说: {text}")
            return text.lower()  # 转为小写便于匹配
            
        except sr.WaitTimeoutError:
            if self.conversation_mode:
                print("⚠️  没有检测到语音（对话模式）")
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
    
    def process_conversation(self, text):
        """处理对话内容"""
        if not text:
            return
        
        # 检查是否是开启对话指令
        if not self.conversation_mode:
            if "hello world" in text or "helloworld" in text:
                self.conversation_mode = True
                response = "Hello! I'm your smart plant. How can I help you today?"
                print(f"🤖 回复: {response}")
                print("\n" + "=" * 60)
                print("✅ 对话模式已开启！")
                print("💡 说 'bye bye' 或 'goodbye' 结束对话")
                print("=" * 60)
                return
            else:
                # 非对话模式下，只显示识别结果
                return
        
        # 对话模式下处理
        # 检查是否是关闭对话指令
        if "bye bye" in text or "bye-bye" in text or "goodbye" in text or "good bye" in text:
            response = "Have a good day! Goodbye!"
            print(f"🤖 回复: {response}")
            self.conversation_mode = False
            print("\n" + "=" * 60)
            print("❌ 对话模式已关闭")
            print("💡 说 'hello world' 可以重新开启对话")
            print("=" * 60)
            return
        
        # 简单的对话响应（后续可以接入AI API）
        response = self.generate_response(text)
        print(f"🤖 回复: {response}")
    
    def generate_response(self, text):
        """生成回复（简单规则，后续可替换为AI API）"""
        text = text.lower()
        
        # 简单的规则响应
        if "how are you" in text or "how r u" in text:
            return "I'm doing great! Thanks for asking. How about you?"
        
        elif "what is your name" in text or "your name" in text:
            return "I'm your smart plant assistant. You can call me Planty!"
        
        elif "hello" in text or "hi" in text:
            return "Hello there! How can I assist you?"
        
        elif "help" in text:
            return "I can chat with you! Try asking me questions or just say 'bye bye' when you're done."
        
        elif "thank" in text:
            return "You're welcome! Happy to help!"
        
        elif "weather" in text:
            return "I'm a plant, so I love sunny weather! But I can't check the actual weather for you yet."
        
        elif "water" in text:
            return "Remember to water your plants regularly! But not too much - we don't like soggy roots!"
        
        elif "sing" in text or "song" in text:
            return "I'm a plant, not a singer! But I appreciate good music!"
        
        elif "joke" in text:
            return "Why did the plant go to therapy? Because it had too many deep roots!"
        
        else:
            # 默认回复（后续可接入AI API）
            return "I heard you! That's interesting. Tell me more!"
    
    def continuous_listen(self):
        """持续监听模式"""
        print("\n" + "=" * 60)
        print("🎙️  语音识别系统已启动")
        print("=" * 60)
        print("模式: 持续监听")
        print("语言: 英语 (English)")
        print("\n💡 使用说明:")
        print("  - 说 'hello world' 开启对话模式")
        print("  - 对话模式下，说 'bye bye' 或 'goodbye' 结束对话")
        print("  - 按 Ctrl+C 退出程序")
        print("=" * 60 + "\n")
        
        while self.is_listening:
            text = self.listen_once()
            if text:
                self.process_conversation(text)
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
