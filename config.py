# config.py

# ==== WiFi ====
WIFI_SSID = "Columbia University"      # Your current WiFi
WIFI_PASSWORD = ""                     # Leave empty if this WiFi doesn't need password

# ==== Server ====
SERVER_IP = "10.206.128.179"             # The IP shown in your server.py terminal. School IP: 10.207.99.24
SERVER_PORT = 8000
AUDIO_API_PATH = "/api/stt"
DEVICE_ID = "esp32-test-01"

# ==== I2S Microphone (SPH0645) ====
MIC_BCLK_PIN = 14   # BCLK
MIC_LRCL_PIN = 15   # LRCL / WS
MIC_DOUT_PIN = 32   # DOUT

MIC_SAMPLE_RATE = 16000
MIC_BITS = 16
MIC_BUFFER_BYTES = 1024    # Read 1KB each time

# ==== I2S Speaker (MAX98357A) ====
AMP_BCLK_PIN = 14   # Shared with mic BCLK
AMP_LRCL_PIN = 15   # Shared with mic LRCL
AMP_DIN_PIN  = 13   # Connect to MAX98357A DIN pin

AMP_SAMPLE_RATE = 16000
AMP_BITS = 16

# ==== ESP32 CAM ====
CAM_STREAM_URL = "http://10.206.163.226:81/stream"

# ==== POE API ====
POE_API_KEY = "V-WboX2arfVDphhx1WjY8pB4KyqQeygpyZ-O2oIQ-1E"
POE_BOT_NAME = "gpt-5-chat"  # Use GPT-5 (no thinking, pure text response)

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