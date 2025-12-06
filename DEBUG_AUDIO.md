# 音频识别问题调试指南

## 问题现象

ESP32日志显示：
```
User text: ''
Response: ''
Conversation active: True
```

这说明：
1. ✅ ESP32成功连接到服务器
2. ✅ 对话模式已激活（第一次说"hello"成功了）
3. ❌ 后续的语音识别失败（Google STT返回空字符串）

## 可能原因

### 1. 麦克风问题
- 麦克风没有正确连接
- 麦克风音量太小
- 麦克风录到的是静音

### 2. 环境噪音问题
- 环境太吵，导致识别失败
- 背景噪音干扰语音识别

### 3. 说话方式问题
- 说话声音太小
- 说话速度太快或太慢
- 没有在录音时段说话

### 4. 网络问题
- Google STT API访问失败
- 网络延迟导致超时

## 调试步骤

### 步骤1: 检查服务器日志

重新运行server.py，你应该看到更详细的日志：

```bash
python server.py
```

当ESP32发送音频时，查看服务器输出：

```
[STT] Received audio bytes: 96000
[STT] Audio stats - Max amplitude: 1234, Avg amplitude: 345.67
[STT] Audio duration: 96000 bytes
[STT] User said: hello
```

**重要诊断信息**：

1. **Max amplitude（最大振幅）**:
   - < 100: 音频太小或是静音 ⚠️
   - 100-1000: 可能太小
   - 1000-5000: 正常范围 ✅
   - > 10000: 音量较大，但可能过载

2. **Avg amplitude（平均振幅）**:
   - < 50: 几乎静音 ⚠️
   - 50-500: 正常范围 ✅
   - > 1000: 音量很大

### 步骤2: 测试麦克风

**在ESP32上测试**：

检查 `mic_module.py` 中的麦克风配置：
- I2S引脚是否正确
- 采样率是否为16000Hz
- 位深度是否为16bit

**简单测试**：
1. 重启ESP32
2. 第一次录音时大声说"Hello"
3. 观察服务器日志中的振幅值
4. 如果振幅很小（<100），说明麦克风有问题

### 步骤3: 检查录音时机

确保你在**正确的时间**说话：

```
ESP32输出：
[Listening...]          ← 开始监听
Recording 3 seconds...  ← 现在开始说话！（3秒内）
Audio sent...          ← 录音结束，太晚了
```

**正确做法**：
- 看到 "Recording 3 seconds..." 时立即开始说话
- 在3秒内说完整句话
- 说话要清晰、音量适中

### 步骤4: 增加录音时长

如果3秒太短，修改 `main.py`:

```python
RECORD_SECONDS = 5   # 改为5秒
```

### 步骤5: 测试网络连接

测试Google STT API是否可访问：

```python
# 在PC上运行这个测试
import speech_recognition as sr

recognizer = sr.Recognizer()
with sr.Microphone() as source:
    print("请说话...")
    audio = recognizer.listen(source)

try:
    text = recognizer.recognize_google(audio, language="en-US")
    print(f"识别结果: {text}")
except Exception as e:
    print(f"错误: {e}")
```

## 常见解决方案

### 解决方案1: 调整麦克风增益

在 `mic_module.py` 中可能需要调整麦克风增益设置。

### 解决方案2: 改善说话方式

- ✅ 靠近麦克风10-20cm
- ✅ 音量适中，清晰说话
- ✅ 在"Recording..."提示后立即开始
- ✅ 说完整的句子，不要停顿

### 解决方案3: 减少环境噪音

- 在安静的环境测试
- 关闭风扇、空调等噪音源
- 避免回声（不要在空旷的房间）

### 解决方案4: 保存音频文件用于调试

在 `server.py` 中添加保存音频的代码：

```python
# 在 stt_endpoint 函数中添加
with open("debug_audio.wav", "wb") as f:
    wav_buf.seek(0)
    f.write(wav_buf.read())
    wav_buf.seek(0)
print("[DEBUG] Audio saved to debug_audio.wav")
```

然后用音频播放器打开 `debug_audio.wav` 检查：
- 是否能听到声音
- 声音是否清晰
- 是否有杂音

## 快速诊断清单

运行下一次测试时，检查以下内容：

- [ ] 服务器显示 "Max amplitude" > 1000
- [ ] 服务器显示 "Avg amplitude" > 100
- [ ] 音频长度约为 96000 bytes (3秒 × 16000Hz × 2bytes)
- [ ] 没有 "WARNING: Audio appears to be silent"
- [ ] 没有 "Speech was not understood"
- [ ] ESP32输出显示 "User text" 不为空

## 预期的正常日志

**服务器端**：
```
[STT] Received audio bytes: 96000
[STT] Audio stats - Max amplitude: 3456, Avg amplitude: 567.89
[STT] Audio duration: 96000 bytes
[STT] User said: how are you
[对话] 处理文本: 'how are you' | 对话模式: True
[对话] 对话模式已激活，处理用户输入
[对话] 生成回复: 'I'm doing great! Thanks for asking. How about you?'
[BOT] Response: I'm doing great! Thanks for asking. How about you?
```

**ESP32端**：
```
[Listening...]
Recording 3 seconds...
Audio sent, waiting for response...

==================================================
RESULT FROM SERVER:
  User text: 'how are you'
  Response: 'I'm doing great! Thanks for asking. How about you?'
  Action: 'continue'
  Has audio: True
  Conversation active: True
==================================================

[YOU]: how are you
[BOT]: I'm doing great! Thanks for asking. How about you?
[播放语音回复...]
```

## 已发现的问题

### I2S总线冲突问题

**根本原因**：
- 麦克风和扬声器共用相同的I2S时钟引脚（BCLK=14, LRCL=15）
- 麦克风使用I2S(0)，扬声器使用I2S(1)
- 第一次录音后，扬声器播放音频，I2S总线状态改变
- 后续录音时，麦克风读取到全是0（Max amplitude: 0）

**已实施的修复**：
1. 在每次录音前清空I2S缓冲区（main.py:38-45）
2. 扬声器deinit后增加100ms延迟，确保I2S总线完全释放（main.py:173-174）

**测试方法**：
1. 重新上传修改后的main.py到ESP32
2. 重启ESP32
3. 观察服务器日志中的振幅值
4. 第二次、第三次录音应该也有正常的振幅值（>1000）

## 下一步

1. 重新运行 `python server.py`
2. 在ESP32上传并运行修改后的main.py
3. 观察服务器日志中的振幅值
4. 检查第二次、第三次录音是否正常
5. 如果仍然失败，可能需要考虑硬件改动（使用不同的I2S引脚）
