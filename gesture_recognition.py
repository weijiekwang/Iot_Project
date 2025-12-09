# -*- coding: utf-8 -*-
import cv2
import mediapipe as mp
import numpy as np
from collections import deque
import time

class GestureRecognizer:
    def __init__(self):
        # 初始化 MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils

        # 用于跟踪头部位置历史（点头检测）
        self.nose_y_history = deque(maxlen=15)

        # 用于跟踪头部位置历史（摇头检测）
        self.nose_x_history = deque(maxlen=15)

        # 用于跟踪手部位置（用于挥手检测）
        self.wrist_history = deque(maxlen=10)

        # 用于跟踪鼓掌动作
        self.clap_history = deque(maxlen=10)

        # 冷却时间，避免重复识别
        self.last_gesture_time = 0
        self.gesture_cooldown = 2.0  # 2秒冷却时间
        
    def calculate_distance(self, point1, point2):
        """计算两点之间的欧几里得距离"""
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def detect_wave(self, landmarks, image_width, image_height):
        """检测挥手打招呼"""
        # 获取右手腕和左手腕的位置
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        
        # 记录手腕位置
        wrist_pos = None
        is_hand_raised = False
        
        # 检查右手是否举起（高于肩膀且靠近头部）
        if right_wrist.y < right_shoulder.y and right_wrist.y < nose.y + 0.1:
            wrist_pos = (right_wrist.x * image_width, right_wrist.y * image_height)
            is_hand_raised = True
        # 检查左手是否举起
        elif left_wrist.y < left_shoulder.y and left_wrist.y < nose.y + 0.1:
            wrist_pos = (left_wrist.x * image_width, left_wrist.y * image_height)
            is_hand_raised = True
        
        if is_hand_raised and wrist_pos:
            self.wrist_history.append(wrist_pos)
            
            # 如果有足够的历史数据，检测左右摆动
            if len(self.wrist_history) >= 8:
                positions = list(self.wrist_history)
                # 计算水平位置的变化
                x_positions = [p[0] for p in positions]
                x_changes = [x_positions[i] - x_positions[i-1] for i in range(1, len(x_positions))]
                
                # 检测是否有明显的左右摆动（变化方向改变）
                direction_changes = 0
                for i in range(1, len(x_changes)):
                    if (x_changes[i] > 5 and x_changes[i-1] < -5) or \
                       (x_changes[i] < -5 and x_changes[i-1] > 5):
                        direction_changes += 1
                
                # 如果有至少2次方向改变，认为是挥手
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
            
            # 计算运动范围
            max_y = max(positions)
            min_y = min(positions)
            movement_range = max_y - min_y
            
            # 降低运动范围要求（从12降到8像素）
            if movement_range < 8:
                return False
            
            # 寻找上下运动模式（降低阈值）
            peaks = 0
            valleys = 0
            
            for i in range(2, len(positions) - 2):
                # 检测波峰（向下移动）- 降低阈值
                if (positions[i] > positions[i-1] + 3 and 
                    positions[i] > positions[i-2] + 2 and
                    positions[i] > positions[i+1] + 3):
                    peaks += 1
                # 检测波谷（向上移动）
                elif (positions[i] < positions[i-1] - 3 and 
                      positions[i] < positions[i-2] - 2 and
                      positions[i] < positions[i+1] - 3):
                    valleys += 1
            
            # 点头应该有至少1个明显的波峰和波谷
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
            
            # 计算运动范围
            max_x = max(positions)
            min_x = min(positions)
            movement_range = max_x - min_x
            
            # 提高运动范围要求（从15提高到25像素）
            if movement_range < 25:
                return False
            
            # 检测左右摆动
            direction_changes = 0
            for i in range(1, len(positions) - 1):
                # 检测方向改变（波峰或波谷）- 提高阈值
                if (positions[i] > positions[i-1] + 5 and 
                    positions[i] > positions[i+1] + 5):
                    direction_changes += 1
                elif (positions[i] < positions[i-1] - 5 and 
                      positions[i] < positions[i+1] - 5):
                    direction_changes >= 1
            
            # 要求至少2次方向改变
            if direction_changes >= 2:
                return True
        
        return False
    
    def detect_raise_hands(self, landmarks, image_height):
        """检测双手举高"""
        # 获取关键点
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value]
        right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value]
        
        # 检查双手是否都举高（高于头部）
        left_hand_raised = (
            left_wrist.y < nose.y and  # 手腕高于鼻子
            left_wrist.y < left_shoulder.y - 0.1 and  # 手腕明显高于肩膀
            left_elbow.y < left_shoulder.y  # 手肘也要抬起
        )
        
        right_hand_raised = (
            right_wrist.y < nose.y and
            right_wrist.y < right_shoulder.y - 0.1 and
            right_elbow.y < right_shoulder.y
        )
        
        # 双手都举起来
        return left_hand_raised and right_hand_raised
    
    def detect_clap(self, landmarks, image_width, image_height):
        """检测鼓掌动作"""
        # 获取双手手腕位置
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        
        # 转换为像素坐标
        left_wrist_pos = (left_wrist.x * image_width, left_wrist.y * image_height)
        right_wrist_pos = (right_wrist.x * image_width, right_wrist.y * image_height)
        
        # 计算双手之间的距离
        hands_distance = self.calculate_distance(left_wrist_pos, right_wrist_pos)
        
        # 双手都应该在胸前位置（高于腰部，低于肩膀上方）
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
                
                # 检测双手距离的快速变化（靠近和分开）
                min_distance = min(distances)
                max_distance = max(distances)
                
                # 如果距离变化范围大（说明在拍手）
                if max_distance - min_distance > 80:
                    # 检测至少一次靠近-分开的模式
                    close_count = 0
                    far_count = 0
                    
                    for d in distances:
                        if d < min_distance + 40:
                            close_count += 1
                        if d > max_distance - 40:
                            far_count += 1
                    
                    # 如果有明显的靠近和分开
                    if close_count >= 2 and far_count >= 2:
                        return True
        else:
            self.clap_history.clear()
        
        return False
    
    def process_frame(self, frame):
        """处理单帧图像"""
        # 转换为RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        
        # 进行姿态检测
        results = self.pose.process(image)
        
        # 转回BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        gesture_detected = None
        current_time = time.time()
        
        # 如果检测到姿态
        if results.pose_landmarks:
            # 绘制姿态标记
            self.mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS
            )
            
            landmarks = results.pose_landmarks.landmark
            h, w, _ = image.shape
            
            # 检查冷却时间
            if current_time - self.last_gesture_time > self.gesture_cooldown:
                # 按优先级检测动作
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
                # elif self.detect_nod(landmarks, h):
                #     gesture_detected = "Yes"
                #     self.last_gesture_time = current_time
                #     self.nose_y_history.clear()
                # elif self.detect_shake(landmarks, w):
                #     gesture_detected = "No"
                #     self.last_gesture_time = current_time
                #     self.nose_x_history.clear()
        
        return image, gesture_detected
    
    def run(self):
        """运行摄像头捕获和动作识别"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("错误：无法打开摄像头")
            return
        
        print("=" * 50)
        print("智能盆栽交互系统")
        print("=" * 50)
        print("支持的动作:")
        print("  - 挥手打招呼 → 输出: Hi")
        print("  - 双手举高 → 输出: Wow")
        print("  - 鼓掌 → 输出: Good")
        print("\n按 'q' 键或关闭窗口退出程序")
        print("=" * 50)
        
        window_name = 'Smart Plant - Gesture Recognition'
        cv2.namedWindow(window_name)
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print("无法获取摄像头画面")
                    break
                
                # 镜像翻转，使显示更自然
                frame = cv2.flip(frame, 1)
                
                # 处理帧
                processed_frame, gesture = self.process_frame(frame)
                
                # 如果检测到动作，显示并输出
                if gesture:
                    print(f"\n检测到动作: {gesture}")
                    cv2.putText(
                        processed_frame,
                        f"Detected: {gesture}",
                        (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.5,
                        (0, 255, 0),
                        3
                    )
                
                # 显示提示信息
                cv2.putText(
                    processed_frame,
                    "Press 'q' to quit",
                    (10, processed_frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2
                )
                
                # 显示画面
                cv2.imshow(window_name, processed_frame)
                
                # 按'q'退出或检查窗口是否被关闭
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\n用户按下 'q' 键，正在退出...")
                    break
                
                # 检查窗口是否被关闭
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    print("\n窗口被关闭，正在退出...")
                    break
        
        except KeyboardInterrupt:
            print("\n\n检测到 Ctrl+C，正在退出...")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.pose.close()
            print("程序已安全退出")


if __name__ == "__main__":
    # 设置控制台编码为UTF-8
    import sys
    if sys.platform == 'win32':
        try:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        except:
            pass

    recognizer = GestureRecognizer()
    recognizer.run()
