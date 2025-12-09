# config.py

# ==== WiFi ====
WIFI_SSID = "Columbia University"      # 你现在用的 WiFi
WIFI_PASSWORD = ""                     # 如果这个 WiFi 不需要密码就留空

# ==== 服务器 ====
SERVER_IP = "10.206.128.179"             # 你 server.py 终端里显示的那个 IP 学校IP：10.207.99.24
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

# ==== ESP32 CAM ====
CAM_STREAM_URL = "http://10.206.163.226:81/stream"

# ==== POE API ====
POE_API_KEY = "V-WboX2arfVDphhx1WjY8pB4KyqQeygpyZ-O2oIQ-1E"
POE_BOT_NAME = "gpt-5-chat"  # 使用GPT-5（无thinking，纯文本回复）

# ==== Moisture Sensor ====
MOISTURE_SENSOR_PIN = 39  # AOUT connected to GPIO39 (ADC1)
MOISTURE_READ_INTERVAL = 5  # Read sensor every 5 seconds

# ==== OLED Display (SSD1306) ====
OLED_WIDTH = 192  # Horizontal rectangular OLED
OLED_HEIGHT = 64
OLED_SDA_PIN = 22  # I2C SDA
OLED_SCL_PIN = 20  # I2C SCL

# ==== NTP Time Sync ====
NTP_HOST = "pool.ntp.org"  # NTP server
NYC_UTC_OFFSET = -5  # New York timezone offset (EST: UTC-5, EDT: UTC-4)
# Note: For daylight saving time (March-November), change to -4