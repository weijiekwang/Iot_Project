# 智能盆栽交互系统

## 📁 文件结构

```
Iot_Project/
├── smart_plant_system.py      # 完整系统（动作识别 + 语音识别）
│
├── Gesture/                   # 动作识别模块（可独立使用）
│   ├── gesture_recognition.py
│   ├── requirements.txt
│   ├── README.md
│   └── TIPS.md
│
├── Voice/                     # 语音识别模块（可独立使用）
│   ├── voice_recognition.py
│   ├── requirements.txt
│   ├── README.md
│   └── 对话功能说明.md
│
└── Web/                       # Web监控系统（可独立使用）
    ├── app.py                 # Flask服务器
    ├── requirements.txt
    ├── README.md
    └── templates/
        └── index.html         # 网页界面
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建环境（推荐）
conda create -n SmartPlanter python=3.11 -y
conda activate SmartPlanter

# 安装动作识别依赖
pip install -r Gesture/requirements.txt

# 安装语音识别依赖
pip install -r Voice/requirements.txt

# 安装Web监控依赖
pip install -r Web/requirements.txt
```

### 2. 运行程序

```bash
# 运行完整系统（动作 + 语音）
python smart_plant_system.py

# 或只测试动作识别
python Gesture/gesture_recognition.py

# 或只测试语音识别
python Voice/voice_recognition.py

# 或启动Web监控系统（本地）
python Web/app.py
# 然后访问 http://localhost:8080

# 或启动Web监控系统（公网）
python Web/app_public.py
# 自动生成公网链接，任何人都可访问！
```

## 📖 详细文档

- **动作识别说明**: [Gesture/README.md](Gesture/README.md)
- **动作识别技巧**: [Gesture/TIPS.md](Gesture/TIPS.md)
- **语音识别说明**: [Voice/README.md](Voice/README.md)
- **对话功能说明**: [Voice/对话功能说明.md](Voice/对话功能说明.md)
- **Web监控说明**: [Web/README.md](Web/README.md)

## 🎯 支持的功能

### 动作识别（5个动作）
- 挥手 → Hi
- 双手举高 → Wow
- 鼓掌 → Good
- 点头 → Yes
- 摇头 → No

### 语音识别与对话
- 实时英语语音识别
- 对话模式控制
  - 说 "hello world" 开启对话
  - 说 "bye bye" 关闭对话
- 简单对话响应
- 预留AI对话接口

### Web监控系统 🌐
- 📊 湿度监控折线图（过去24小时）
- 💬 网页按钮控制对话开启/关闭
- 📝 实时活动日志（动作+对话）
- 🔄 自动刷新（每5秒）
- 🌡️ 湿度统计（当前/平均/数据点）

## ⚠️ 注意事项

1. **PyAudio安装**：语音识别需要PyAudio，可能需要额外配置
   - Windows: 可能需要下载whl文件
   - macOS: `brew install portaudio`
   - Linux: `sudo apt-get install portaudio19-dev`

2. **网络连接**：语音识别使用Google API，需要网络

3. **摄像头/麦克风权限**：首次运行需要授权

## 💡 开发建议

- **独立开发**：可以分别在Gesture、Voice和Web文件夹中修改和测试
- **整合测试**：使用smart_plant_system.py测试动作和语音功能
- **Web监控**：使用Web/app.py启动监控界面
- **模块化**：三个模块互不影响，可以独立开发

## 🔗 模块协作

各模块可以通过API相互通信：

```python
# 动作识别 → Web
import requests
requests.post('http://localhost:5000/api/gesture', 
              json={'gesture': 'Hi'})

# 语音对话 → Web  
requests.post('http://localhost:5000/api/speech',
              json={'user': 'hello', 'bot': 'hi there'})

# 湿度传感器 → Web
requests.post('http://localhost:5000/api/humidity/add',
              json={'humidity': 75.5})
```
