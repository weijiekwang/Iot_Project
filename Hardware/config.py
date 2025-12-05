# config.py - 智能盆栽ESP32完整配置

# ==== WiFi ====
WIFI_SSID = "Columbia University"
WIFI_PASSWORD = ""

# ==== 服务器配置 ====
# 改为你的电脑IP地址（运行Web服务器的地址）
SERVER_BASE_URL = "http://10.207.99.24:8080"  # 改为8080端口

# API路径
AUDIO_API_PATH = "/api/speech"      # 语音识别和对话
GESTURE_API_PATH = "/api/gesture"   # 动作识别上报
STATUS_API_PATH = "/api/conversation/status"  # 对话状态

DEVICE_ID = "smart-plant-01"

# ==== I2S 麦克风（SPH0645） ====
MIC_BCLK_PIN = 14   # BCLK
MIC_LRCL_PIN = 15   # LRCL / WS
MIC_DOUT_PIN = 32   # DOUT

MIC_SAMPLE_RATE = 16000
MIC_BITS = 16
MIC_BUFFER_BYTES = 1024

# ==== I2S 扬声器/功放（MAX98357A） ====
AMP_BCLK_PIN = 26   # BCLK
AMP_LRCL_PIN = 25   # LRCL / WS
AMP_DIN_PIN = 22    # DIN

AMP_SAMPLE_RATE = 16000
AMP_BITS = 16

# ==== OLED 显示屏（SSD1306） ====
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_SCL_PIN = 22   # I2C SCL
OLED_SDA_PIN = 21   # I2C SDA

# ==== 摄像头（ESP32-CAM）====
# ESP32-CAM 使用固定引脚，无需配置
CAMERA_ENABLED = True
CAMERA_FRAME_SIZE = 7  # QVGA (320x240)
CAMERA_QUALITY = 10    # JPEG质量 (0-63，越小质量越高)

# ==== 录音参数 ====
RECORD_SECONDS = 3     # 每次录音3秒
GESTURE_CHECK_INTERVAL = 2  # 每2秒检查一次对话状态
