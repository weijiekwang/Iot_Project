# config.py

# ==== WiFi ====
WIFI_SSID = "Columbia University"      # 你现在用的 WiFi
WIFI_PASSWORD = ""                     # 如果这个 WiFi 不需要密码就留空

# ==== 服务器 ====
SERVER_IP = "10.207.99.24"             # 你 server.py 终端里显示的那个 IP
SERVER_PORT = 8000
AUDIO_API_PATH = "/api/stt"
DEVICE_ID = "esp32-test-01"

# ==== I2S 麦克风（SPH0645） ====
MIC_BCLK_PIN = 14   # BCLK
MIC_LRCL_PIN = 15   # LRCL / WS
MIC_DOUT_PIN = 32   # DOUT

MIC_SAMPLE_RATE = 16000
MIC_BITS = 16
MIC_BUFFER_BYTES = 1024    # 每次读 1KB

# ==== I2S 扬声器（MAX98357A） ====
AMP_BCLK_PIN = 14   # 跟麦克 BCLK 共用
AMP_LRCL_PIN = 15   # 跟麦克 LRCL 共用
AMP_DIN_PIN  = 13   # 接 MAX98357A 的 DIN 引脚

AMP_SAMPLE_RATE = 16000
AMP_BITS = 16