# 对话系统测试指南

## 问题诊断

如果对话系统只能识别第一个输入或者无法响应预设对话，请按以下步骤排查：

## 1. 启动服务器并观察日志

运行服务器：
```bash
python server.py
```

你应该看到详细的日志输出，包括：
- `[STT] Received audio bytes: xxx` - 接收到的音频数据
- `[STT] User said: xxx` - 识别到的文本
- `[对话] 处理文本: 'xxx' | 对话模式: True/False` - 对话处理状态
- `[BOT] Response: xxx` - 生成的回复

## 2. 测试流程

### 第一次测试（开启对话）
1. ESP32录音3秒
2. 说 **"Hello"**（单独说这个词）或 **"Hello World"**
3. 服务器日志应该显示：
   ```
   [STT] User said: hello
   [对话] 处理文本: 'hello' | 对话模式: False
   [对话] 对话模式已激活
   [BOT] Response: Hello! I'm your smart plant. How can I help you today?
   ```

**注意**:
- 开启对话需要单独说 "Hello" 或说 "Hello World"
- 如果说 "Hello there" 或其他包含hello的句子，不会触发开启对话
- 这样设计是为了避免误触发

### 第二次测试（对话中）
1. ESP32继续录音
2. 说 **"How are you"** 或其他预设问题
3. 服务器日志应该显示：
   ```
   [STT] User said: how are you
   [对话] 处理文本: 'how are you' | 对话模式: True
   [对话] 对话模式已激活，处理用户输入
   [对话] 生成回复: 'I'm doing great! Thanks for asking. How about you?'
   [BOT] Response: I'm doing great! Thanks for asking. How about you?
   ```

### 第三次测试（关闭对话）
1. 说 **"Bye bye"**
2. 服务器日志应该显示：
   ```
   [STT] User said: bye bye
   [对话] 处理文本: 'bye bye' | 对话模式: True
   [对话] 对话模式已关闭
   [BOT] Response: Have a good day! Goodbye!
   ```

## 3. 常见问题排查

### 问题1: 对话模式没有激活
**症状**: 服务器日志显示 `[对话] 非对话模式，忽略输入`

**原因**:
- Google STT 没有正确识别 "hello" 或 "hello world"
- 可能识别成了其他相似的词

**解决方法**:
- 说话时靠近麦克风
- 说话清晰，速度适中
- 检查服务器日志中的 `[STT] User said: xxx`，看实际识别成了什么

### 问题2: 对话模式激活后没有回复
**症状**:
- 第一次说 "hello" 有回复
- 第二次说 "how are you" 没有回复

**调试方法**:
1. 查看服务器日志中的识别文本
2. 检查是否显示 `[对话] 对话模式已激活，处理用户输入`
3. 查看 `[对话] 生成回复: xxx` 是否出现

**可能原因**:
- Google STT 识别失败（返回空字符串）
- 网络问题导致识别超时
- 麦克风录音质量不佳

### 问题3: 只能识别预设短语的部分
**症状**: 说 "how are you" 但只识别到 "how"

**解决方法**:
- 增加录音时长（修改 `RECORD_SECONDS`）
- 说话时保持连贯
- 检查麦克风配置

## 4. 预设对话列表

当对话模式激活后，系统可以识别以下问题：

| 说什么 | 回复 |
|--------|------|
| how are you | I'm doing great! Thanks for asking. How about you? |
| what is your name | I'm your smart plant assistant. You can call me Planty! |
| hello / hi | Hello there! How can I assist you? |
| help | I can chat with you! Try asking me questions or just say bye bye when you're done. |
| thank you | You're welcome! Happy to help! |
| weather | I'm a plant, so I love sunny weather! But I can't check the actual weather for you yet. |
| water | Remember to water your plants regularly! But not too much - we don't like soggy roots! |
| sing a song | I'm a plant, not a singer! But I appreciate good music! |
| tell me a joke | Why did the plant go to therapy? Because it had too many deep roots! |
| 其他任何话 | I heard you! That's interesting. Tell me more! |

## 5. ESP32端日志

ESP32应该显示：
```
[Listening...]
Recording 3 seconds...
Audio sent, waiting for response...

==================================================
RESULT FROM SERVER:
  User text: 'hello'
  Response: 'Hello! I'm your smart plant. How can I help you today?'
  Action: 'start_conversation'
  Has audio: True
  Conversation active: True
==================================================

[YOU]: hello
[BOT]: Hello! I'm your smart plant. How can I help you today?
[播放语音回复...]
Requesting TTS audio...
Played 23456 bytes

*** Conversation Started! ***
```

## 6. 调试技巧

### 增加录音时长
如果经常识别不全，可以在 `main.py` 中修改：
```python
RECORD_SECONDS = 5   # 从3秒改为5秒
```

### 测试语音识别
可以单独测试STT是否工作，使用curl：
```bash
curl -X POST http://localhost:8000/api/stt \
  -H "Content-Type: application/octet-stream" \
  --data-binary @test_audio.pcm
```

### 查看对话状态
对话管理器的状态存储在服务器内存中，重启服务器会重置状态。

## 7. 优化建议

1. **改善识别准确率**:
   - 在安静环境中测试
   - 使用质量好的麦克风
   - 说话清晰、速度适中

2. **降低延迟**:
   - 确保WiFi信号良好
   - 减少录音时长（但可能影响识别率）

3. **增强对话能力**:
   - 在 `generate_response()` 中添加更多规则
   - 未来可以接入AI API（如OpenAI GPT）
