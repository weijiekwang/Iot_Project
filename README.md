# Smart Plant IoT System

A comprehensive IoT system featuring gesture recognition, voice interaction, moisture monitoring, and real-time web dashboard for smart plant care.

## Table of Contents
- [System Overview](#system-overview)
- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Project Structure](#project-structure)
- [Step-by-Step Setup Guide](#step-by-step-setup-guide)
  - [1. Environment Setup](#1-environment-setup)
  - [2. Server Setup](#2-server-setup)
  - [3. ESP32 Hardware Setup](#3-esp32-hardware-setup)
  - [4. Web Dashboard Setup](#4-web-dashboard-setup)
- [Usage Guide](#usage-guide)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)

## System Overview

This IoT system integrates multiple technologies to create an intelligent plant monitoring and interaction system:

- **Gesture Recognition**: Recognizes hand gestures (Hi, Wow, Good) using ESP32-CAM and MediaPipe
- **Voice Interaction**: Speech-to-text and text-to-speech conversation system
- **Moisture Monitoring**: Real-time soil moisture sensor data collection
- **Web Dashboard**: Real-time monitoring interface with charts and controls
- **Hardware Integration**: ESP32 microcontroller with camera, microphone, speaker, and OLED display

## Features

### Gesture Recognition
- Hi (Wave hand)
- Wow (Raise both hands)
- Good (Thumbs up/Applause)
- Yes (Nod head)
- No (Shake head)

### Voice Interaction
- Conversation mode activation: Say "Hello World" or "Hello"
- Natural language conversation using POE API (GPT-5)
- End conversation: Say "Bye Bye" or "Goodbye"
- Hardcoded responses for schedule queries
- Real-time speech-to-text and text-to-speech

### Moisture Monitoring
- Real-time soil moisture percentage
- Voltage readings from analog sensor
- Status classification (Dry/Medium/Wet)
- Historical data tracking

### Web Dashboard
- Real-time moisture monitoring
- Gesture recognition status display
- Conversation mode control (voice or web buttons)
- Humidity trend visualization
- Auto-refresh every 2-5 seconds

## Hardware Requirements

### ESP32-CAM Module
- Model: AI-Thinker ESP32-CAM
- Purpose: Video streaming for gesture recognition
- Connection: WiFi

### ESP32 Huzzah (Main Controller)
- Model: Adafruit ESP32 Huzzah or compatible
- Purpose: Voice interaction, sensor reading, display control

### Audio Components
- **Microphone**: I2S MEMS SPH0645
  - BCLK → GPIO 14
  - LRCL (WS) → GPIO 15
  - DOUT → GPIO 32
  - VDD → 3.3V, GND → GND

- **Speaker/Amplifier**: MAX98357A I2S
  - BCLK → GPIO 14
  - LRCL (WS) → GPIO 15
  - DIN → GPIO 13
  - VIN → 5V, GND → GND

### Display
- **OLED**: SSD1306 (192x64 pixels, I2C)
  - SDA → GPIO 22
  - SCL → GPIO 20
  - VDD → 3.3V, GND → GND

### Sensor
- **Moisture Sensor**: Analog capacitive soil moisture sensor
  - AOUT → GPIO 39 (ADC1)
  - VCC → 3.3V, GND → GND

## Software Requirements

### Python Environment
- Python 3.8 or higher (3.11 recommended)
- Conda (recommended for environment management)

### Key Python Libraries
- Flask 2.3.0 (Web server)
- OpenCV >= 4.8.0 (Computer vision)
- MediaPipe >= 0.10.5 (Gesture recognition)
- SpeechRecognition 3.10.0 (Speech-to-text)
- pyttsx3 (Text-to-speech)
- fastapi-poe (POE API client for conversation)
- NumPy >= 1.24.0

### ESP32 Firmware
- MicroPython firmware for ESP32
- Arduino IDE (for ESP32-CAM)

### API Keys
- POE API Key (for conversation with GPT-5)

## Project Structure

```
Iot_Project/
├── server.py                      # Main Flask server (STT/TTS/Gesture/Web)
├── config.py                      # Configuration file (WiFi, IPs, API keys)
├── gesture_recognition.py         # Gesture detection module
├── requirements.txt               # Python dependencies
│
├── Gesture/                       # Gesture recognition module
│   ├── gesture_recognition.py
│   ├── requirements.txt
│   └── README.md
│
├── Voice/                         # Voice recognition module
│   ├── voice_recognition.py
│   ├── requirements.txt
│   └── README.md
│
├── Web/                           # Web dashboard
│   ├── app.py
│   ├── requirements.txt
│   └── README.md
│
├── Hardware/                      # ESP32 hardware code
│   ├── main.py                    # ESP32 main program (MicroPython)
│   ├── config.py                  # Hardware configuration
│   ├── mic_module.py              # Microphone I2S module
│   ├── speaker_module.py          # Speaker I2S module
│   ├── oled_module.py             # OLED display module
│   ├── wifi_manager.py            # WiFi connection manager
│   ├── requirements.txt           # Server-side dependencies
│   └── README.md
│
└── Arduino/                       # Arduino code for ESP32-CAM
    └── CameraWebServer/
        └── CameraWebServer.ino    # ESP32-CAM video streaming
```

## Step-by-Step Setup Guide

### 1. Environment Setup

#### Create Conda Environment (Recommended)

```bash
# Create environment
conda create -n SmartPlanter python=3.11 -y

# Activate environment
conda activate SmartPlanter
```

#### Install Python Dependencies

```bash
# Navigate to project root
cd Iot_Project

# Install all dependencies
pip install -r requirements.txt
```

**Note**: If you encounter issues with specific libraries, install them individually:

```bash
pip install Flask==2.3.0
pip install opencv-python>=4.8.0
pip install mediapipe>=0.10.5
pip install SpeechRecognition==3.10.0
pip install pyttsx3
pip install fastapi-poe
pip install numpy>=1.24.0
```

### 2. Server Setup

#### Step 2.1: Configure Settings

Edit `config.py` in the project root:

```python
# WiFi Configuration
WIFI_SSID = "Your_WiFi_SSID"           # Your WiFi network name
WIFI_PASSWORD = "Your_WiFi_Password"   # Your WiFi password

# Server Configuration
SERVER_IP = "192.168.1.100"            # Your computer's local IP address
SERVER_PORT = 8000

# ESP32-CAM Configuration
CAM_STREAM_URL = "http://192.168.1.101:81/stream"  # ESP32-CAM stream URL

# POE API Configuration
POE_API_KEY = "your_poe_api_key"       # Get from https://poe.com/api_key
POE_BOT_NAME = "gpt-5-chat"            # Use GPT-5 for conversation

# Moisture Sensor Configuration
MOISTURE_SENSOR_PIN = 39               # GPIO pin for moisture sensor
MOISTURE_READ_INTERVAL = 5             # Read interval in seconds
```

#### Step 2.2: Find Your Computer's Local IP

**Windows:**
```cmd
ipconfig
# Look for "IPv4 Address" under your active network adapter
```

**macOS/Linux:**
```bash
ifconfig
# Look for "inet" address under your active network interface (usually en0 or wlan0)
```

**Example**: If your IP is `10.206.128.179`, set `SERVER_IP = "10.206.128.179"`

#### Step 2.3: Start the Main Server

```bash
# Activate environment if not already active
conda activate SmartPlanter

# Run the server
python server.py
```

You should see:
```
============================================================
Smart Plant Web Monitoring System + ESP32 STT/TTS Server
============================================================
Local access:   http://localhost:8000
LAN access:     http://10.206.128.179:8000
STT endpoint:   POST /api/stt
TTS test:       GET  /api/tts_test
============================================================
```

**Keep this terminal window open** - the server needs to run continuously.

### 3. ESP32 Hardware Setup

#### Step 3.1: ESP32-CAM Setup (Gesture Recognition)

**Upload Arduino Code:**

1. Open Arduino IDE
2. Install ESP32 board support:
   - Go to File > Preferences
   - Add to "Additional Board Manager URLs":
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to Tools > Board > Boards Manager
   - Search for "esp32" and install "esp32 by Espressif Systems"

3. Open `Arduino/CameraWebServer/CameraWebServer.ino`

4. Configure WiFi:
   ```cpp
   const char *ssid = "Your_WiFi_SSID";
   const char *password = "Your_WiFi_Password";
   ```

5. Select board: Tools > Board > ESP32 Arduino > AI Thinker ESP32-CAM

6. Upload the sketch (you may need to press the RESET button)

7. Open Serial Monitor (115200 baud) to see the camera stream URL:
   ```
   Camera Ready! Use 'http://192.168.1.101' to connect
   Stream: http://192.168.1.101:81/stream
   ```

8. Update `config.py` with the stream URL:
   ```python
   CAM_STREAM_URL = "http://192.168.1.101:81/stream"
   ```

#### Step 3.2: ESP32 Huzzah Setup (Voice & Sensors)

**Install MicroPython:**

1. Download MicroPython firmware for ESP32:
   - Visit: https://micropython.org/download/esp32/
   - Download the latest stable `.bin` file

2. Install esptool:
   ```bash
   pip install esptool
   ```

3. Erase flash and upload firmware:
   ```bash
   # Find your serial port (COM3, /dev/ttyUSB0, etc.)
   # Windows: Check Device Manager
   # macOS/Linux: ls /dev/tty*

   # Erase flash
   esptool.py --chip esp32 --port COM3 erase_flash

   # Upload MicroPython
   esptool.py --chip esp32 --port COM3 write_flash -z 0x1000 esp32-*.bin
   ```

**Upload Project Code:**

1. Install mpremote:
   ```bash
   pip install mpremote
   ```

2. Upload files to ESP32:
   ```bash
   # Navigate to Hardware directory
   cd Hardware

   # Upload configuration
   mpremote connect COM3 fs cp config.py :

   # Upload modules
   mpremote connect COM3 fs cp wifi_manager.py :
   mpremote connect COM3 fs cp mic_module.py :
   mpremote connect COM3 fs cp speaker_module.py :
   mpremote connect COM3 fs cp oled_module.py :
   mpremote connect COM3 fs cp moisture_sensor_module.py :

   # Upload main program
   mpremote connect COM3 fs cp main.py :

   # Upload SSD1306 library (for OLED)
   mpremote connect COM3 fs cp ../ssd1306.py :
   ```

   **Or use the upload script:**
   ```bash
   chmod +x upload_to_esp32.sh
   ./upload_to_esp32.sh
   ```

3. Configure ESP32 settings in `Hardware/config.py`:
   ```python
   # WiFi
   WIFI_SSID = "Your_WiFi_SSID"
   WIFI_PASSWORD = "Your_WiFi_Password"

   # Server
   SERVER_IP = "10.206.128.179"  # Your computer's IP
   SERVER_PORT = 8000
   ```

4. Reset ESP32 to run the program:
   ```bash
   mpremote connect COM3 reset
   ```

#### Step 3.3: Hardware Wiring

**Microphone (SPH0645):**
- BCLK → GPIO 14
- LRCL (WS) → GPIO 15
- DOUT → GPIO 32
- 3V → 3.3V
- GND → GND

**Speaker/Amplifier (MAX98357A):**
- BCLK → GPIO 14 (shared with mic)
- LRCL (WS) → GPIO 15 (shared with mic)
- DIN → GPIO 13
- VIN → 5V
- GND → GND

**OLED Display (SSD1306):**
- SDA → GPIO 22
- SCL → GPIO 20
- VCC → 3.3V
- GND → GND

**Moisture Sensor:**
- AOUT → GPIO 39 (ADC1 channel)
- VCC → 3.3V
- GND → GND

### 4. Web Dashboard Setup

The web dashboard is integrated into the main `server.py`, so if the server is running, the dashboard is already accessible.

**Access the Dashboard:**

1. Open a web browser
2. Navigate to: `http://localhost:8000` or `http://YOUR_COMPUTER_IP:8000`

**Dashboard Features:**
- Real-time moisture monitoring with trend chart
- Gesture recognition status display
- Conversation mode control (Start/Stop buttons)
- Live updates every 2 seconds

## Usage Guide

### Starting the System

1. **Start the Server** (on your computer):
   ```bash
   conda activate SmartPlanter
   python server.py
   ```

2. **Power on ESP32-CAM** - It will automatically connect to WiFi and start streaming

3. **Power on ESP32 Huzzah** - It will:
   - Connect to WiFi
   - Initialize hardware (mic, speaker, OLED, sensors)
   - Start listening for voice commands

4. **Open Web Dashboard**: Navigate to `http://localhost:8000` in your browser

### Voice Interaction

**Activate Conversation Mode:**
- Say: **"Hello World"** or **"Hello"**
- System responds: "Hello! How can I help you today?"
- OLED displays: "Conversation Started!"

**During Conversation:**
- Speak naturally in English
- System recognizes speech and responds using GPT-5
- Responses are displayed on OLED and spoken through speaker

**Hardcoded Commands:**
- "What's my schedule today?" → System tells you your schedule

**Deactivate Conversation Mode:**
- Say: **"Bye Bye"** or **"Goodbye"**
- System responds: "Have a good day! Goodbye!"
- OLED displays: "Conversation Ended"

### Gesture Recognition

**Supported Gestures:**
- **Hi**: Wave your hand in front of ESP32-CAM
- **Wow**: Raise both hands above your head
- **Good**: Thumbs up or applause

**Behavior:**
- When a gesture is detected, the system generates TTS audio
- ESP32 Huzzah fetches and plays the gesture audio
- Gesture is displayed on the web dashboard
- Preview window shows the camera feed with detected landmarks

### Moisture Monitoring

**Automatic Monitoring:**
- ESP32 reads moisture sensor every 5 seconds
- Data is sent to server via POST `/api/moisture`
- Web dashboard displays real-time moisture percentage
- Status shown as: Dry / Medium / Wet

**Manual Refresh:**
- Click "Refresh Humidity" button on web dashboard
- View historical trend chart (past 24 hours)

### Web Dashboard Controls

**Conversation Control:**
- **Start Conversation** button: Activates conversation mode
- **Stop Conversation** button: Deactivates conversation mode
- Status updates automatically every 2 seconds

**Moisture Monitoring:**
- Current moisture percentage
- Voltage reading
- Status classification
- Trend chart with 24-hour history

**Gesture Display:**
- Shows most recent gesture detected
- Timestamp of detection
- Updates every 500ms

## API Reference

### Speech-to-Text (STT)

**Endpoint**: `POST /api/stt`

**Request**:
- Content-Type: `application/octet-stream`
- Body: Raw PCM audio (16kHz, 16-bit, mono)

**Response**:
```json
{
  "text": "recognized text",
  "response": "bot response",
  "action": "start_conversation|continue|end_conversation",
  "conversation_active": true,
  "has_audio": true
}
```

### Text-to-Speech (TTS)

**Endpoint**: `GET /api/tts`

**Response**:
- Content-Type: `application/octet-stream`
- Body: PCM audio (16kHz, 16-bit, mono)

**Test Endpoint**: `GET /api/tts_test`

### Gesture Recognition Status

**Endpoint**: `GET /api/gesture_status`

**Response**:
```json
{
  "gesture": "Hi|Wow|Good|null",
  "timestamp": 1234567890.123
}
```

### Gesture TTS Audio

**Endpoint**: `GET /api/gesture_tts`

**Response**:
- Content-Type: `application/octet-stream`
- Body: PCM audio for gesture (e.g., "Hi", "Wow", "Good")

### Moisture Data Upload

**Endpoint**: `POST /api/moisture`

**Request**:
```json
{
  "raw": 2048,
  "voltage": 1.65,
  "moisture_percent": 50.0,
  "status": "Medium"
}
```

**Response**:
```json
{
  "success": true
}
```

### Moisture Status

**Endpoint**: `GET /api/moisture_status`

**Response**:
```json
{
  "raw": 2048,
  "voltage": 1.65,
  "moisture_percent": 50.0,
  "status": "Medium",
  "timestamp": 1234567890.123,
  "is_stale": false
}
```

### Conversation Control

**Get Status**: `GET /api/conversation/status`
```json
{
  "active": true
}
```

**Start Conversation**: `POST /api/conversation/start`
```json
{
  "success": true,
  "active": true
}
```

**Stop Conversation**: `POST /api/conversation/stop`
```json
{
  "success": true,
  "active": false
}
```

## Troubleshooting

### Server Issues

**Problem**: Cannot access web dashboard

**Solution**:
1. Check if server is running: `python server.py`
2. Verify firewall allows port 8000
3. Try both `localhost:8000` and `YOUR_IP:8000`

**Problem**: Gesture recognition not working

**Solution**:
1. Verify ESP32-CAM stream URL in `config.py`
2. Test stream URL in browser: `http://CAM_IP:81/stream`
3. Check if MediaPipe is installed: `pip install mediapipe`
4. Ensure adequate lighting for camera

### ESP32 Issues

**Problem**: ESP32 won't connect to WiFi

**Solution**:
1. Verify SSID and password in `config.py`
2. Check WiFi signal strength
3. Ensure WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
4. Reset ESP32 and retry

**Problem**: Microphone not recording

**Solution**:
1. Check I2S pin connections (BCLK, LRCL, DOUT)
2. Verify 3.3V power supply
3. Check serial monitor for error messages
4. Test with simple recording script

**Problem**: Speaker not playing audio

**Solution**:
1. Check I2S pin connections (BCLK, LRCL, DIN)
2. Verify 5V power supply for MAX98357A
3. Ensure BCLK and LRCL are shared with microphone
4. Test with simple tone playback

**Problem**: OLED display blank

**Solution**:
1. Check I2C connections (SDA, SCL)
2. Verify I2C address (usually 0x3C)
3. Check if ssd1306.py is uploaded to ESP32
4. Test I2C scanner script

### Voice Recognition Issues

**Problem**: Speech not recognized

**Solution**:
1. Ensure quiet environment
2. Speak clearly and at moderate pace
3. Check internet connection (Google API requires network)
4. Adjust microphone distance (20-50cm optimal)
5. Check audio quality in server logs

**Problem**: POE API errors

**Solution**:
1. Verify POE_API_KEY in `config.py`
2. Check POE account credits
3. Ensure network connectivity
4. Check server logs for error details

### Hardware Connection Issues

**Problem**: Moisture sensor readings unstable

**Solution**:
1. Verify sensor connection to GPIO 39
2. Check 3.3V power supply
3. Ensure sensor probe is inserted in soil
4. Calibrate sensor readings in code

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         User                                │
│              (Voice, Gestures, Web Browser)                 │
└────────────┬──────────────────────┬────────────┬───────────┘
             │                      │            │
             │ Voice                │ Gestures   │ Web Access
             │                      │            │
┌────────────▼──────────┐  ┌────────▼─────────┐  │
│   ESP32 Huzzah        │  │  ESP32-CAM       │  │
│  ┌─────────────────┐  │  │ ┌──────────────┐ │  │
│  │ Microphone      │  │  │ │ Camera       │ │  │
│  │ (SPH0645)       │  │  │ │ (OV2640)     │ │  │
│  └─────────────────┘  │  │ └──────────────┘ │  │
│  ┌─────────────────┐  │  │                  │  │
│  │ Speaker         │  │  │ Video Stream     │  │
│  │ (MAX98357A)     │  │  │ :81/stream       │  │
│  └─────────────────┘  │  └──────────────────┘  │
│  ┌─────────────────┐  │           │            │
│  │ OLED Display    │  │           │            │
│  │ (SSD1306)       │  │           │            │
│  └─────────────────┘  │           │            │
│  ┌─────────────────┐  │           │            │
│  │ Moisture Sensor │  │           │            │
│  │ (GPIO 39)       │  │           │            │
│  └─────────────────┘  │           │            │
└───────────┬───────────┘           │            │
            │ WiFi                  │ WiFi       │ HTTP
            │                       │            │
┌───────────▼───────────────────────▼────────────▼───────────┐
│                  Flask Server (server.py)                  │
│                    Running on Computer                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Web Dashboard (/)                                   │  │
│  │  - Moisture monitoring chart                        │  │
│  │  - Gesture status display                           │  │
│  │  - Conversation controls                            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  STT/TTS API (/api/stt, /api/tts)                   │  │
│  │  - Google Speech Recognition                        │  │
│  │  - pyttsx3 Text-to-Speech                          │  │
│  │  - POE API (GPT-5) Conversation                    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Gesture Recognition (Background Thread)            │  │
│  │  - OpenCV video capture from ESP32-CAM             │  │
│  │  - MediaPipe hand/pose detection                   │  │
│  │  - Gesture classification (Hi, Wow, Good)          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Moisture Data Storage                               │  │
│  │  - In-memory latest data                            │  │
│  │  - Thread-safe access with locks                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

**Voice Interaction Flow:**
```
ESP32 Mic → PCM Audio → WiFi → Server /api/stt
                                  ↓
                            Google STT API
                                  ↓
                            Text Recognition
                                  ↓
                        Conversation Manager
                                  ↓
                        POE API (GPT-5) / Hardcoded
                                  ↓
                            Response Text
                                  ↓
                            pyttsx3 TTS
                                  ↓
Server /api/tts → PCM Audio → WiFi → ESP32 Speaker
```

**Gesture Recognition Flow:**
```
ESP32-CAM → Video Stream → Server Background Thread
                                  ↓
                            OpenCV Capture
                                  ↓
                          MediaPipe Detection
                                  ↓
                        Gesture Classification
                                  ↓
                        Store in Global Variable
                                  ↓
                            Generate TTS
                                  ↓
ESP32 Polls /api/gesture_tts → Play Audio
```

**Moisture Monitoring Flow:**
```
ESP32 ADC → Read Sensor → Calculate Percentage
                                  ↓
                        POST /api/moisture
                                  ↓
                      Server Updates Data
                                  ↓
                      Web Dashboard Polls
                                  ↓
                     Display Chart & Stats
```

### Technology Stack

**Backend:**
- Flask 2.3.0 - Web server framework
- SpeechRecognition 3.10.0 - Google STT integration
- pyttsx3 - Local TTS engine
- fastapi-poe - POE API client for GPT-5
- OpenCV 4.8.0+ - Computer vision
- MediaPipe 0.10.5+ - Hand/pose detection

**Frontend:**
- HTML5/CSS3/JavaScript
- Native fetch API for AJAX requests
- Real-time updates with setInterval

**Embedded:**
- MicroPython - ESP32 Huzzah firmware
- Arduino C++ - ESP32-CAM firmware
- I2S protocol - Audio communication
- I2C protocol - OLED display
- ADC - Analog sensor reading

**APIs:**
- Google Speech Recognition API (Free tier)
- POE API (GPT-5 chat model)

### Security Notes

**Current Status**: Development/Testing Version
- No authentication required
- No HTTPS encryption
- Local network only access
- Credentials in plain text config files

**Production Recommendations**:
1. Add user authentication (OAuth2, JWT)
2. Enable HTTPS with SSL certificates
3. Use environment variables for sensitive data
4. Implement rate limiting on API endpoints
5. Add input validation and sanitization
6. Set up firewall rules to restrict access
7. Use secure WebSocket for real-time updates
8. Implement logging and monitoring

---

## Additional Resources

- **Gesture Recognition Details**: [Gesture/README.md](Gesture/README.md)
- **Voice Recognition Details**: [Voice/README.md](Voice/README.md)
- **Web Dashboard Details**: [Web/README.md](Web/README.md)
- **Hardware Setup Guide**: [Hardware/README.md](Hardware/README.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributors

Smart Plant IoT System - Columbia University 2025 Fall Project

---

For questions or issues, please refer to the individual module README files or check the troubleshooting section above.
