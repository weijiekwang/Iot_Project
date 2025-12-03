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
└── Voice/                     # 语音识别模块（可独立使用）
    ├── voice_recognition.py
    ├── requirements.txt
    └── README.md
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建环境（推荐）
conda create -n LOTplanter python=3.11 -y
conda activate LOTplanter

# 安装动作识别依赖
pip install -r Gesture/requirements.txt

# 安装语音识别依赖
pip install -r Voice/requirements.txt
```

### 2. 运行程序

```bash
# 运行完整系统（动作 + 语音）
python smart_plant_system.py

# 或只测试动作识别
python Gesture/gesture_recognition.py

# 或只测试语音识别
python Voice/voice_recognition.py
```

## 📖 详细文档

- **动作识别说明**: [Gesture/README.md](Gesture/README.md)
- **动作识别技巧**: [Gesture/TIPS.md](Gesture/TIPS.md)
- **语音识别说明**: [Voice/README.md](Voice/README.md)

## 🎯 支持的功能

### 动作识别（5个动作）
- 挥手 → Hi
- 双手举高 → Wow
- 鼓掌 → Good
- 点头 → Yes
- 摇头 → No

### 语音识别
- 实时英语语音识别
- 预留AI对话接口

## ⚠️ 注意事项

1. **PyAudio安装**：语音识别需要PyAudio，可能需要额外配置
   - Windows: 可能需要下载whl文件
   - macOS: `brew install portaudio`
   - Linux: `sudo apt-get install portaudio19-dev`

2. **网络连接**：语音识别使用Google API，需要网络

3. **摄像头/麦克风权限**：首次运行需要授权

## 💡 开发建议

- **独立开发**：可以分别在Gesture和Voice文件夹中修改和测试
- **整合测试**：使用smart_plant_system.py测试完整功能
- **模块化**：两个模块互不影响，可以独立开发
