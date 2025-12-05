# config.py

# ==== WiFi ====
WIFI_SSID = "你的WiFi名字"
WIFI_PASSWORD = "你的WiFi密码"

# ==== 服务器 ====
# 用你服务器终端里那行：Running on http://10.207.99.24:8000
SERVER_BASE_URL = "http://10.207.99.24:8000"
AUDIO_API_PATH = "/api/stt"

DEVICE_ID = "esp32-test-01"

# ==== I2S 麦克风（SPH0645） ====
MIC_BCLK_PIN = 14   # BCLK
MIC_LRCL_PIN = 15   # LRCL / WS
MIC_DOUT_PIN = 32   # DOUT

MIC_SAMPLE_RATE = 16000
MIC_BITS = 16
MIC_BUFFER_BYTES = 1024    # 一次读 1024 字节
