# config.py - Smart Plant ESP32 Complete Configuration

# ==== WiFi ====
WIFI_SSID = "Columbia University"
WIFI_PASSWORD = ""

# ==== Server Configuration ====
# Change to your computer's IP address (where the Web server is running)
SERVER_BASE_URL = "http://10.207.99.24:8080"  # Change to port 8080

# API Paths
AUDIO_API_PATH = "/api/speech"      # Speech recognition and conversation
GESTURE_API_PATH = "/api/gesture"   # Gesture recognition reporting
STATUS_API_PATH = "/api/conversation/status"  # Conversation status

DEVICE_ID = "smart-plant-01"

# ==== I2S Microphone (SPH0645) ====
MIC_BCLK_PIN = 14   # BCLK
MIC_LRCL_PIN = 15   # LRCL / WS
MIC_DOUT_PIN = 32   # DOUT

MIC_SAMPLE_RATE = 16000
MIC_BITS = 16
MIC_BUFFER_BYTES = 1024

# ==== I2S Speaker/Amplifier (MAX98357A) ====
AMP_BCLK_PIN = 26   # BCLK
AMP_LRCL_PIN = 25   # LRCL / WS
AMP_DIN_PIN = 22    # DIN

AMP_SAMPLE_RATE = 16000
AMP_BITS = 16

# ==== OLED Display (SSD1306) ====
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_SCL_PIN = 22   # I2C SCL
OLED_SDA_PIN = 21   # I2C SDA

# ==== Camera (ESP32-CAM) ====
# ESP32-CAM uses fixed pins, no configuration needed
CAMERA_ENABLED = True
CAMERA_FRAME_SIZE = 7  # QVGA (320x240)
CAMERA_QUALITY = 10    # JPEG quality (0-63, lower is higher quality)

# ==== Recording Parameters ====
RECORD_SECONDS = 3     # Record 3 seconds each time
GESTURE_CHECK_INTERVAL = 2  # Check conversation status every 2 seconds
