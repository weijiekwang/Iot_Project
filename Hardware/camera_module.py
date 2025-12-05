# camera_module.py
import camera
from config import CAMERA_FRAME_SIZE, CAMERA_QUALITY

class CameraModule:
    def __init__(self):
        try:
            # 初始化摄像头（ESP32-CAM）
            camera.init(0, format=camera.JPEG)
            camera.framesize(CAMERA_FRAME_SIZE)  # QVGA
            camera.quality(CAMERA_QUALITY)
            print("Camera initialized")
        except Exception as e:
            print("Camera init error:", e)
            raise
    
    def capture_jpeg(self):
        """捕获一张JPEG图片"""
        try:
            buf = camera.capture()
            if buf:
                return bytes(buf)
            return None
        except Exception as e:
            print("Capture error:", e)
            return None
    
    def deinit(self):
        """关闭摄像头"""
        try:
            camera.deinit()
        except:
            pass
