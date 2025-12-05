# 智能盆栽语音识别功能

## 📋 功能说明

系统现在支持**英语语音识别**和**对话功能**。

### 当前功能
- ✅ 实时英语语音识别
- ✅ 对话模式（可开启/关闭）
- ✅ 简单对话响应
- ✅ 识别结果实时显示

### 对话指令
- 🟢 **开启对话**: 说 "hello world"
- 🔴 **关闭对话**: 说 "bye bye" 或 "goodbye"

### 未来功能（预留接口）
- 🔄 接入AI对话API（如ChatGPT、Claude等）
- 🔄 语音回复功能（TTS）
- 🔄 中英文混合识别

## 🎯 三个程序说明

### 1. gesture_recognition.py - 纯动作识别
**功能：** 只有动作识别，不含语音
**适合：** 测试动作识别功能
**运行：**
```bash
python gesture_recognition.py
```

### 2. voice_recognition.py - 纯语音识别
**功能：** 只有语音识别，不含动作
**适合：** 测试语音识别功能
**运行：**
```bash
python voice_recognition.py
```

### 3. smart_plant_system.py - 完整系统 ⭐
**功能：** 动作识别 + 语音识别同时运行
**适合：** 完整的交互体验
**运行：**
```bash
python smart_plant_system.py
```

## 📦 安装步骤

### 1. 创建conda环境（推荐）
```bash
conda create -n SmartPlanter python=3.11 -y
conda activate SmartPlanter
```

### 2. 安装依赖包

#### 方法一：使用requirements.txt
```bash
pip install -r requirements.txt
```

#### 方法二：手动安装
```bash
pip install opencv-python mediapipe numpy SpeechRecognition pyaudio
```

### 3. PyAudio安装注意事项

PyAudio是语音识别必需的库，但在某些系统上安装可能遇到问题：

**Windows:**
如果 `pip install pyaudio` 失败，请使用预编译的whl文件：
```bash
# 下载对应Python版本的whl文件
# Python 3.11, 64位: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
pip install PyAudio-0.2.13-cp311-cp311-win_amd64.whl
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

### 4. 测试麦克风

确保你的麦克风正常工作：
```bash
# 运行语音识别测试
python voice_recognition.py
```

## 🎤 使用说明

### 语音识别使用

1. **启动程序**
```bash
python voice_recognition.py
```

2. **等待校准**
   - 程序启动时会自动校准麦克风
   - 校准期间请保持安静

3. **开启对话模式**
   - 对着麦克风说 **"hello world"**
   - 系统回复: "Hello! I'm your smart plant. How can I help you today?"
   - 对话模式开启！

4. **开始对话**
   - 对话模式下，你说的话会得到回复
   - 识别结果会显示在终端/控制台
   - 系统会给出文字回复

5. **结束对话**
   - 说 **"bye bye"** 或 **"goodbye"**
   - 系统回复: "Have a good day! Goodbye!"
   - 对话模式关闭

6. **支持的语言**
   - 目前只支持英语 (English)
   - 后续可以扩展其他语言

### 对话功能演示

```
🎤 你说: hello world
🤖 回复: Hello! I'm your smart plant. How can I help you today?
✅ 对话模式已开启！

🎤 你说: how are you
🤖 回复: I'm doing great! Thanks for asking. How about you?

🎤 你说: tell me a joke
🤖 回复: Why did the plant go to therapy? Because it had too many deep roots!

🎤 你说: bye bye
🤖 回复: Have a good day! Goodbye!
❌ 对话模式已关闭
```

### 简单对话主题

当前系统支持以下简单对话（预设规则）：

- 问候语: "hello", "hi"
- 状态询问: "how are you"
- 自我介绍: "what is your name"
- 求助: "help"
- 感谢: "thank you"
- 天气: "weather"
- 植物相关: "water"
- 娱乐: "joke", "sing"
- 其他话题: 会给出默认回复

**注意**: 这些是简单的规则回复。后续可以接入AI API获得更智能的对话。

### 识别效果优化

**环境要求：**
- 安静的环境（减少背景噪音）
- 清晰的发音
- 麦克风与嘴巴距离适中（20-50cm）

**说话技巧：**
- 说话速度适中，不要太快
- 吐字清晰
- 避免长时间停顿

## 🔧 常见问题

### Q1: PyAudio安装失败
**A:** 
- Windows: 下载预编译的whl文件安装
- macOS: 先安装portaudio: `brew install portaudio`
- Linux: 先安装依赖: `sudo apt-get install portaudio19-dev`

### Q2: 麦克风无法使用
**A:**
1. 检查麦克风是否正常连接
2. 检查系统麦克风权限设置
3. 确保没有其他程序占用麦克风
4. 尝试重启程序

### Q3: 识别不准确
**A:**
1. 确保环境安静
2. 说话清晰，速度适中
3. 调整麦克风与嘴巴的距离
4. 检查麦克风质量

### Q4: 程序运行慢/卡顿
**A:**
- 语音识别使用在线Google API，需要网络连接
- 如果网络慢，识别会有延迟
- 可以考虑使用离线语音识别引擎

### Q5: 无法连接Google语音识别服务
**A:**
- 检查网络连接
- 确保可以访问Google服务
- 如果在中国大陆，可能需要特殊网络配置

## 🚀 后续扩展功能

### 1. 接入AI对话API

在 `smart_plant_system.py` 的 `listen_speech` 函数中，找到这段代码：

```python
text = self.recognizer.recognize_google(audio, language='en-US')
self.latest_speech = text
print(f"\n🎤 你说: {text}")

# 这里后续可以接入AI对话API
# response = call_ai_api(text)
# print(f"🤖 回复: {response}")
```

替换为你的AI API调用：

**使用OpenAI ChatGPT:**
```python
import openai

openai.api_key = "your-api-key"

def call_ai_api(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

# 在识别后调用
text = self.recognizer.recognize_google(audio, language='en-US')
response = call_ai_api(text)
print(f"🤖 AI回复: {response}")
```

**使用Claude API:**
```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")

def call_ai_api(text):
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": text}
        ]
    )
    return message.content[0].text

# 在识别后调用
text = self.recognizer.recognize_google(audio, language='en-US')
response = call_ai_api(text)
print(f"🤖 AI回复: {response}")
```

### 2. 添加语音合成（Text-to-Speech）

安装pyttsx3:
```bash
pip install pyttsx3
```

添加语音回复：
```python
import pyttsx3

# 初始化TTS引擎
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # 语速

# 使用
def speak(text):
    engine.say(text)
    engine.runAndWait()

# 回复时使用
response = call_ai_api(text)
print(f"🤖 AI回复: {response}")
speak(response)
```

### 3. 切换语音识别语言

修改语言参数：
```python
# 英语
text = self.recognizer.recognize_google(audio, language='en-US')

# 中文
text = self.recognizer.recognize_google(audio, language='zh-CN')

# 日语
text = self.recognizer.recognize_google(audio, language='ja-JP')

# 西班牙语
text = self.recognizer.recognize_google(audio, language='es-ES')
```

## 📊 系统架构

```
智能盆栽系统
├── 视觉输入
│   ├── 摄像头捕获
│   ├── MediaPipe姿态检测
│   └── 动作识别
│       ├── 挥手 → Hi
│       ├── 双手举高 → Wow
│       ├── 鼓掌 → Good
│       ├── 点头 → Yes
│       └── 摇头 → No
│
└── 语音输入
    ├── 麦克风捕获
    ├── 语音识别 (Google API)
    └── 对话处理
        ├── 文本显示
        └── [预留] AI对话API
            └── [预留] 语音合成
```

## 💡 使用建议

1. **首次使用**：先分别测试动作识别和语音识别
2. **环境准备**：安静的环境，良好的光线
3. **逐步调试**：先确保单个功能正常，再运行完整系统
4. **性能优化**：如果电脑配置较低，可以降低摄像头分辨率

## 🔗 相关资源

- SpeechRecognition文档: https://pypi.org/project/SpeechRecognition/
- MediaPipe文档: https://google.github.io/mediapipe/
- OpenAI API: https://platform.openai.com/docs/api-reference
- Anthropic Claude API: https://docs.anthropic.com/
