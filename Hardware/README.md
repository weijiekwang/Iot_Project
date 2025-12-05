# 🌱 智能盆栽硬件系统

## 📋 系统架构

```
ESP32硬件端                服务器端                   Web监控端
├── 麦克风(SPH0645)  →    ├── server.py         →   ├── app.py
├── 扬声器(MAX98357A) ←   │   - 语音识别              │   - 湿度监控
├── OLED(SSD1306)     ←   │   - 对话处理              │   - 对话控制
└── 摄像头(ESP32-CAM) →   └── - 动作识别              └── - 活动日志
```

## 🔌 硬件连接

### ESP32引脚分配

#### 麦克风 (SPH0645 - I2S)
- BCLK → GPIO 14
- LRCL (WS) → GPIO 15
- DOUT → GPIO 32
- VDD → 3.3V
- GND → GND

#### 扬声器/功放 (MAX98357A - I2S)
- BCLK → GPIO 26
- LRCL (WS) → GPIO 25
- DIN → GPIO 22
- VIN → 5V
- GND → GND

#### OLED显示屏 (SSD1306 - I2C)
- SCL → GPIO 22
- SDA → GPIO 21
- VDD → 3.3V
- GND → GND

#### 摄像头 (ESP32-CAM)
- 使用ESP32-CAM模块（固定引脚）
- 或使用OV2640连接到ESP32

## 🚀 快速开始

### 1. 准备环境

**安装MicroPython到ESP32:**
```bash
# 下载MicroPython固件
# https://micropython.org/download/esp32/

# 烧录固件（替换PORT为你的串口）
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-*.bin
```

**安装依赖库:**
```bash
# 使用mpremote或ampy上传库文件
pip install mpremote

# 上传ssd1306库（OLED）
mpremote connect /dev/ttyUSB0 fs cp ssd1306.py :
```

### 2. 配置服务器

**修改 `config.py`:**
```python
# 改为你的电脑IP地址
SERVER_BASE_URL = "http://10.207.99.24:8080"

# 改为你的WiFi
WIFI_SSID = "Columbia University"
WIFI_PASSWORD = ""
```

### 3. 启动服务器

**在电脑上运行:**
```bash
# 创建环境
conda activate SmartPlanter

# 安装依赖
pip install Flask speech_recognition opencv-python mediapipe

# 启动服务器
python Hardware/server.py
```

服务器会监听：`http://0.0.0.0:8000`

### 4. 上传代码到ESP32

```bash
# 上传所有文件
mpremote connect /dev/ttyUSB0 fs cp config.py :
mpremote connect /dev/ttyUSB0 fs cp main.py :
mpremote connect /dev/ttyUSB0 fs cp wifi_manager.py :
mpremote connect /dev/ttyUSB0 fs cp mic_module.py :
mpremote connect /dev/ttyUSB0 fs cp speaker_module.py :
mpremote connect /dev/ttyUSB0 fs cp oled_module.py :
mpremote connect /dev/ttyUSB0 fs cp camera_module.py :

# 或者使用一键上传脚本
./upload_to_esp32.sh
```

### 5. 运行系统

**ESP32自动运行:**
```bash
# 重启ESP32
mpremote connect /dev/ttyUSB0 reset

# 或通过串口监视
mpremote connect /dev/ttyUSB0 run main.py
```

## 📊 工作流程

### 启动流程
1. ESP32连接WiFi（Columbia University）
2. 初始化硬件（麦克风、扬声器、OLED、摄像头）
3. 连接到服务器检查对话状态
4. 进入主循环

### 主循环流程
```
1. 检查对话状态（每2秒）
   └─> 向服务器查询是否有人开启了对话

2. 如果对话激活：
   ├─> 录音3秒
   ├─> 上传到服务器
   ├─> 服务器识别语音 → 处理对话 → 返回回复
   └─> ESP32显示/播放回复

3. 定期拍照并识别动作
   ├─> 捕获图片
   ├─> 上传到服务器
   └─> 服务器检测动作（挥手、举手等）

4. 在OLED上显示状态
```

### 对话控制方式

#### 方式1: 语音控制
- 说 "hello world" → 开启对话
- 说 "bye bye" → 关闭对话

#### 方式2: 网页控制
- 访问 http://localhost:8080
- 点击"开启对话"按钮
- 点击"关闭对话"按钮

## 🔧 API接口

### 服务器API

**1. 语音识别和对话**
```
POST /api/speech
Content-Type: application/octet-stream
Body: PCM音频数据（16kHz, 16-bit, mono）

Response:
{
  "user": "识别到的文字",
  "bot": "机器人回复",
  "action": "start_conversation/continue/end_conversation"
}
```

**2. 动作识别**
```
POST /api/gesture
Content-Type: image/jpeg
Body: JPEG图片

Response:
{
  "gesture": "Hi/Wow/Good/Yes/No" or null
}
```

**3. 对话状态查询**
```
GET /api/conversation/status

Response:
{
  "active": true/false
}
```

## 📝 OLED显示状态

| 状态 | 第一行 | 第二行 | 第三行 |
|------|--------|--------|--------|
| 启动中 | Smart Plant | Initializing... | |
| 待机 | Smart Plant | Standby | Say Hello! |
| 监听中 | Listening... | | |
| 处理中 | Processing... | | |
| 显示回复 | Bot回复文字（自动分行） | | |
| 动作识别 | Gesture: | Hi/Wow/etc | |

## 🐛 调试技巧

### 查看串口输出
```bash
mpremote connect /dev/ttyUSB0
```

### 常见问题

**Q1: WiFi连接失败**
- 检查SSID和密码
- 检查信号强度
- 尝试重启ESP32

**Q2: 服务器连接失败**
- 确认电脑和ESP32在同一WiFi
- 检查防火墙设置
- 确认服务器IP地址正确

**Q3: 麦克风无声音**
- 检查I2S引脚连接
- 检查麦克风供电（3.3V）
- 调整录音时长

**Q4: 摄像头无法初始化**
- 确认使用ESP32-CAM模块
- 或检查OV2640连接
- 设置 `CAMERA_ENABLED = False` 禁用

**Q5: OLED无显示**
- 检查I2C连接
- 确认地址（通常是0x3C）
- 检查ssd1306库是否上传

## 🔌 与Web系统集成

服务器会自动将数据同步到Web监控系统：

```python
# 对话记录 → Web
requests.post("http://localhost:8080/api/speech",
             json={"user": text, "bot": response})

# 动作识别 → Web
requests.post("http://localhost:8080/api/gesture",
             json={"gesture": gesture})

# 对话状态 → Web
requests.post("http://localhost:8080/api/conversation/start")
requests.post("http://localhost:8080/api/conversation/stop")
```

这样在Web页面上就能实时看到：
- 对话记录
- 动作识别结果
- 对话状态

## 📈 性能优化

### 降低功耗
```python
# 增加检查间隔
GESTURE_CHECK_INTERVAL = 5  # 从2秒改为5秒

# 缩短录音时长
RECORD_SECONDS = 2  # 从3秒改为2秒
```

### 提高识别准确度
```python
# 增加录音时长
RECORD_SECONDS = 5

# 提高图片质量
CAMERA_QUALITY = 5  # 值越小质量越高
```

## 🔮 后续扩展

- [ ] 添加TTS语音合成（让植物说话）
- [ ] 添加湿度传感器数据采集
- [ ] 添加LED灯光控制
- [ ] 支持更多动作识别
- [ ] 优化对话响应速度
- [ ] 添加本地缓存（离线模式）
- [ ] 支持多设备（多个盆栽）

## 📞 技术支持

遇到问题请查看：
- MicroPython文档: https://docs.micropython.org/
- ESP32文档: https://docs.espressif.com/
- MediaPipe文档: https://google.github.io/mediapipe/

---

**硬件集成完成！🎉**
