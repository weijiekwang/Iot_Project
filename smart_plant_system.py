import cv2
import mediapipe as mp
import numpy as np
from collections import deque
import time
import speech_recognition as sr
import threading

class SmartPlantSystem:
    def __init__(self):
        # 初始化动作识别
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # 历史记录
        self.nose_y_history = deque(maxlen=15)
        self.nose_x_history = deque(maxlen=15)
        self.wrist_history = deque(maxlen=10)
        self.clap_history = deque(maxlen=10)
        
        # 冷却时间
        self.last_gesture_time = 0
        self.gesture_cooldown = 2.0
        
        # 初始化语音识别
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = True
        self.latest_speech = ""
        self.conversation_mode = False  # 对话模式标志
        
        # 调整环境噪音
        print("正在校准麦克风...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("麦克风校准完成！")
        except Exception as e:
            print(f"麦克风初始化失败: {e}")
            print("将继续运行，但语音识别可能不可用")
    
    def calculate_distance(self, point1, point2):
        """计算两点之间的欧几里得距离"""
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def detect_wave(self, landmarks, image_width, image_height):
        """检测挥手打招呼"""
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        
        wrist_pos = None
        is_hand_raised = False
        
        if right_wrist.y < right_shoulder.y and right_wrist.y < nose.y + 0.1:
            wrist_pos = (right_wrist.x * image_width, right_wrist.y * image_height)
            is_hand_raised = True
        elif left_wrist.y < left_shoulder.y and left_wrist.y < nose.y + 0.1:
            wrist_pos = (left_wrist.x * image_width, left_wrist.y * image_height)
            is_hand_raised = True
        
        if is_hand_raised and wrist_pos:
            self.wrist_history.append(wrist_pos)
            
            if len(self.wrist_history) >= 8:
                positions = list(self.wrist_history)
                x_positions = [p[0] for p in positions]
                x_changes = [x_positions[i] - x_positions[i-1] for i in range(1, len(x_positions))]
                
                direction_changes = 0
                for i in range(1, len(x_changes)):
                    if (x_changes[i] > 5 and x_changes[i-1] < -5) or \
                       (x_changes[i] < -5 and x_changes[i-1] > 5):
                        direction_changes += 1
                
                if direction_changes >= 2:
                    return True
        else:
            self.wrist_history.clear()
        
        return False
    
    def detect_nod(self, landmarks, image_height):
        """检测点头"""
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        nose_y = nose.y * image_height
        
        self.nose_y_history.append(nose_y)
        
        if len(self.nose_y_history) >= 12:
            positions = list(self.nose_y_history)
            max_y = max(positions)
            min_y = min(positions)
            movement_range = max_y - min_y
            
            if movement_range < 8:
                return False
            
            peaks = 0
            valleys = 0
            
            for i in range(2, len(positions) - 2):
                if (positions[i] > positions[i-1] + 3 and 
                    positions[i] > positions[i-2] + 2 and
                    positions[i] > positions[i+1] + 3):
                    peaks += 1
                elif (positions[i] < positions[i-1] - 3 and 
                      positions[i] < positions[i-2] - 2 and
                      positions[i] < positions[i+1] - 3):
                    valleys += 1
            
            if peaks >= 1 and valleys >= 1:
                return True
        
        return False
    
    def detect_shake(self, landmarks, image_width):
        """检测摇头"""
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        nose_x = nose.x * image_width
        
        self.nose_x_history.append(nose_x)
        
        if len(self.nose_x_history) >= 10:
            positions = list(self.nose_x_history)
            max_x = max(positions)
            min_x = min(positions)
            movement_range = max_x - min_x
            
            if movement_range < 25:
                return False
            
            direction_changes = 0
            for i in range(1, len(positions) - 1):
                if (positions[i] > positions[i-1] + 5 and 
                    positions[i] > positions[i+1] + 5):
                    direction_changes += 1
                elif (positions[i] < positions[i-1] - 5 and 
                      positions[i] < positions[i+1] - 5):
                    direction_changes += 1
            
            if direction_changes >= 2:
                return True
        
        return False
    
    def detect_raise_hands(self, landmarks, image_height):
        """检测双手举高"""
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value]
        right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value]
        
        left_hand_raised = (
            left_wrist.y < nose.y and
            left_wrist.y < left_shoulder.y - 0.1 and
            left_elbow.y < left_shoulder.y
        )
        
        right_hand_raised = (
            right_wrist.y < nose.y and
            right_wrist.y < right_shoulder.y - 0.1 and
            right_elbow.y < right_shoulder.y
        )
        
        return left_hand_raised and right_hand_raised
    
    def detect_clap(self, landmarks, image_width, image_height):
        """检测鼓掌动作"""
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        
        left_wrist_pos = (left_wrist.x * image_width, left_wrist.y * image_height)
        right_wrist_pos = (right_wrist.x * image_width, right_wrist.y * image_height)
        
        hands_distance = self.calculate_distance(left_wrist_pos, right_wrist_pos)
        
        hands_in_position = (
            left_wrist.y > left_shoulder.y - 0.2 and
            left_wrist.y < left_shoulder.y + 0.3 and
            right_wrist.y > right_shoulder.y - 0.2 and
            right_wrist.y < right_shoulder.y + 0.3
        )
        
        if hands_in_position:
            self.clap_history.append(hands_distance)
            
            if len(self.clap_history) >= 8:
                distances = list(self.clap_history)
                min_distance = min(distances)
                max_distance = max(distances)
                
                if max_distance - min_distance > 80:
                    close_count = sum(1 for d in distances if d < min_distance + 40)
                    far_count = sum(1 for d in distances if d > max_distance - 40)
                    
                    if close_count >= 2 and far_count >= 2:
                        return True
        else:
            self.clap_history.clear()
        
        return False
    
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
    
    def process_conversation(self, text):
        """处理对话内容"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # 检查是否是开启对话指令
        if not self.conversation_mode:
            if "hello world" in text_lower or "helloworld" in text_lower:
                self.conversation_mode = True
                response = "Hello! I'm your smart plant. How can I help you today?"
                print(f"\n🤖 [对话开启] 回复: {response}")
                return response
            else:
                # 非对话模式下，只返回None
                return None
        
        # 对话模式下处理
        # 检查是否是关闭对话指令
        if "bye bye" in text_lower or "bye-bye" in text_lower or "goodbye" in text_lower or "good bye" in text_lower:
            response = "Have a good day! Goodbye!"
            print(f"\n🤖 [对话结束] 回复: {response}")
            self.conversation_mode = False
            return response
        
        # 生成对话响应
        response = self.generate_response(text_lower)
        print(f"\n🤖 [对话中] 回复: {response}")
        return response
    
    def process_frame(self, frame):
        """处理单帧图像"""
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = self.pose.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        gesture_detected = None
        current_time = time.time()
        
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS
            )
            
            landmarks = results.pose_landmarks.landmark
            h, w, _ = image.shape
            
            if current_time - self.last_gesture_time > self.gesture_cooldown:
                if self.detect_raise_hands(landmarks, h):
                    gesture_detected = "Wow"
                    self.last_gesture_time = current_time
                elif self.detect_clap(landmarks, w, h):
                    gesture_detected = "Good"
                    self.last_gesture_time = current_time
                    self.clap_history.clear()
                elif self.detect_wave(landmarks, w, h):
                    gesture_detected = "Hi"
                    self.last_gesture_time = current_time
                    self.wrist_history.clear()
                elif self.detect_nod(landmarks, h):
                    gesture_detected = "Yes"
                    self.last_gesture_time = current_time
                    self.nose_y_history.clear()
                elif self.detect_shake(landmarks, w):
                    gesture_detected = "No"
                    self.last_gesture_time = current_time
                    self.nose_x_history.clear()
        
        return image, gesture_detected
    
    def listen_speech(self):
        """语音识别线程"""
        while self.is_listening:
            try:
                with self.microphone as source:
                    # 设置较短的超时时间，避免阻塞
                    audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=8)
                
                # 识别语音
                text = self.recognizer.recognize_google(audio, language='en-US')
                self.latest_speech = text
                print(f"\n🎤 你说: {text}")
                
                # 处理对话
                response = self.process_conversation(text)
                
                # 如果有回复，更新显示（后续可以添加语音输出）
                if response:
                    self.latest_speech = f"You: {text} | Bot: {response[:30]}..."
                
            except sr.WaitTimeoutError:
                pass  # 超时，继续监听
            except sr.UnknownValueError:
                pass  # 无法识别，继续监听
            except sr.RequestError as e:
                print(f"语音识别服务错误: {e}")
                time.sleep(5)
            except Exception:
                pass  # 其他错误，继续监听
    
    def run(self):
        """运行主程序"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("错误：无法打开摄像头")
            return
        
        print("=" * 60)
        print("🌱 智能盆栽交互系统")
        print("=" * 60)
        print("📹 动作识别:")
        print("  - 挥手 → Hi")
        print("  - 双手举高 → Wow")
        print("  - 鼓掌 → Good")
        print("  - 点头 → Yes")
        print("  - 摇头 → No")
        print("\n🎤 语音识别: 已启动 (英语)")
        print("💬 对话功能:")
        print("  - 说 'hello world' 开启对话")
        print("  - 说 'bye bye' 或 'goodbye' 结束对话")
        print("\n按 'q' 键退出")
        print("=" * 60)
        
        # 启动语音识别线程
        speech_thread = threading.Thread(target=self.listen_speech, daemon=True)
        speech_thread.start()
        
        window_name = 'Smart Plant System'
        cv2.namedWindow(window_name)
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame = cv2.flip(frame, 1)
                processed_frame, gesture = self.process_frame(frame)
                
                if gesture:
                    print(f"\n👋 动作: {gesture}")
                    cv2.putText(
                        processed_frame,
                        f"Gesture: {gesture}",
                        (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.5,
                        (0, 255, 0),
                        3
                    )
                
                # 显示最新的语音识别结果
                if self.latest_speech:
                    cv2.putText(
                        processed_frame,
                        f"Speech: {self.latest_speech[:30]}",
                        (10, processed_frame.shape[0] - 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 0),
                        2
                    )
                
                cv2.putText(
                    processed_frame,
                    "Press 'q' to quit",
                    (10, processed_frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2
                )
                
                cv2.imshow(window_name, processed_frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\n用户按下 'q' 键，正在退出...")
                    break
                
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    print("\n窗口被关闭，正在退出...")
                    break
        
        except KeyboardInterrupt:
            print("\n\n检测到 Ctrl+C，正在退出...")
        
        finally:
            self.is_listening = False
            cap.release()
            cv2.destroyAllWindows()
            self.pose.close()
            print("程序已安全退出")

if __name__ == "__main__":
    system = SmartPlantSystem()
    system.run()
