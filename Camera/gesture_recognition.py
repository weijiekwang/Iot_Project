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
        
        # 用于跟踪头部位置历史（用于点头/摇头检测）
        self.nose_history = deque(maxlen=15)
        
        # 用于跟踪手部位置（用于挥手检测）
        self.wrist_history = deque(maxlen=10)
        
        # 用于跟踪跳跃
        self.hip_height_history = deque(maxlen=20)
        
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
        
        self.nose_history.append(('y', nose_y))
        
        if len(self.nose_history) >= 12:
            positions = [p[1] for p in self.nose_history]
            
            # 寻找上下运动模式
            peaks = 0
            valleys = 0
            
            for i in range(1, len(positions) - 1):
                # 检测波峰（向下然后向上）
                if positions[i] > positions[i-1] + 3 and positions[i] > positions[i+1] + 3:
                    peaks += 1
                # 检测波谷（向上然后向下）
                elif positions[i] < positions[i-1] - 3 and positions[i] < positions[i+1] - 3:
                    valleys += 1
            
            # 点头应该有明显的上下运动
            if peaks >= 1 and valleys >= 1:
                return True
        
        return False
    
    def detect_shake(self, landmarks, image_width):
        """检测摇头"""
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        nose_x = nose.x * image_width
        
        self.nose_history.append(('x', nose_x))
        
        if len(self.nose_history) >= 12:
            # 只考虑最近的位置（用于摇头检测）
            recent = [p for p in self.nose_history if p[0] == 'x']
            if len(recent) >= 8:
                positions = [p[1] for p in recent[-8:]]
                
                # 检测左右摆动
                direction_changes = 0
                for i in range(1, len(positions) - 1):
                    # 检测方向改变
                    if (positions[i] > positions[i-1] + 5 and positions[i] > positions[i+1] + 5) or \
                       (positions[i] < positions[i-1] - 5 and positions[i] < positions[i+1] - 5):
                        direction_changes += 1
                
                if direction_changes >= 2:
                    return True
        
        return False
    
    def detect_jump(self, landmarks, image_height):
        """检测跳跃"""
        # 使用臀部的平均高度来检测跳跃
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        
        avg_hip_y = ((left_hip.y + right_hip.y) / 2) * image_height
        
        self.hip_height_history.append(avg_hip_y)
        
        if len(self.hip_height_history) >= 15:
            positions = list(self.hip_height_history)
            
            # 找到最近的最低点和当前位置
            recent_min = min(positions[-10:])
            current = positions[-1]
            
            # 如果当前位置明显低于最近的最低点（说明身体向上移动了）
            # y坐标越小表示越高
            if recent_min - current > 30:
                return True
        
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
                if self.detect_jump(landmarks, h):
                    gesture_detected = "Jump"
                    self.last_gesture_time = current_time
                    self.hip_height_history.clear()
                elif self.detect_wave(landmarks, w, h):
                    gesture_detected = "Hi"
                    self.last_gesture_time = current_time
                    self.wrist_history.clear()
                elif self.detect_nod(landmarks, h):
                    gesture_detected = "Yes"
                    self.last_gesture_time = current_time
                    self.nose_history.clear()
                elif self.detect_shake(landmarks, w):
                    gesture_detected = "No"
                    self.last_gesture_time = current_time
                    self.nose_history.clear()
        
        return image, gesture_detected
    
    def run(self):
        """运行摄像头捕获和动作识别"""
        cap = cv2.VideoCapture(0)
        
        print("=" * 50)
        print("智能盆栽动作识别系统")
        print("=" * 50)
        print("支持的动作:")
        print("  - 挥手打招呼 → 输出: Hi")
        print("  - 跳跃 → 输出: Jump")
        print("  - 点头 → 输出: Yes")
        print("  - 摇头 → 输出: No")
        print("\n按 'q' 退出程序")
        print("=" * 50)
        
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
            cv2.imshow('Smart Plant - Gesture Recognition', processed_frame)
            
            # 按'q'退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        self.pose.close()

if __name__ == "__main__":
    recognizer = GestureRecognizer()
    recognizer.run()
