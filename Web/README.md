# 🌐 智能盆栽Web监控系统

## 📋 功能说明

提供Web界面，实时监控盆栽状态和控制对话功能。

### 主要功能
- 📊 **湿度监控**: 显示过去24小时的湿度变化折线图
- 💬 **对话控制**: 网页按钮控制对话开启/关闭
- 📝 **活动日志**: 实时显示动作识别和对话记录
- 🔄 **自动刷新**: 每5秒自动更新数据

## 🚀 快速开始

### 方式1: 本地访问（最简单）

```bash
pip install -r requirements.txt
python app.py
```

打开浏览器访问: **http://localhost:8080**

### 方式2: 公网访问（推荐）🌍

```bash
pip install -r requirements.txt
python app_public.py
```

程序会自动生成公网链接，任何人都可以访问！

**特点：**
- ✅ 无需配置路由器
- ✅ 自动HTTPS加密  
- ✅ 获得固定域名链接
- ✅ 可以在任何地方访问

详细说明请查看: [公网访问说明.md](公网访问说明.md)

## 📊 网页功能

### 湿度监控面板
- **折线图**: 显示过去24小时湿度趋势
- **当前湿度**: 最新一次测量值
- **平均湿度**: 24小时平均值
- **数据点数**: 记录的数据点总数

### 对话控制面板
- **状态显示**: 显示当前对话是否开启
- **开启对话**: 点击按钮开启对话模式
- **关闭对话**: 点击按钮关闭对话模式
- **刷新数据**: 手动刷新所有数据

### 活动日志
- **系统消息**: 蓝色，显示系统状态
- **用户消息**: 浅蓝色，显示用户说的话
- **植物回复**: 绿色，显示植物的回复
- **动作识别**: 粉色，显示识别到的动作

## 🔌 API接口

### 获取湿度数据
```
GET /api/humidity
返回: 过去24小时的湿度数据
```

### 获取对话状态
```
GET /api/conversation/status
返回: 当前对话状态
```

### 开启对话
```
POST /api/conversation/start
返回: 开启成功消息
```

### 关闭对话
```
POST /api/conversation/stop
返回: 关闭成功消息
```

### 获取对话日志
```
GET /api/conversation/log
返回: 最近50条对话记录
```

### 添加湿度数据（供传感器调用）
```
POST /api/humidity/add
Body: {"humidity": 75.5}
返回: 添加成功消息
```

### 记录动作
```
POST /api/gesture
Body: {"gesture": "Hi"}
返回: 记录成功消息
```

### 记录对话
```
POST /api/speech
Body: {"user": "hello", "bot": "hi there"}
返回: 记录成功消息
```

## 📁 文件结构

```
Web/
├── app.py                 # Flask主程序
├── requirements.txt       # 依赖列表
├── README.md             # 说明文档
├── templates/            # HTML模板
│   └── index.html        # 主页面
└── data/                 # 数据目录（自动创建）
    ├── humidity_data.json      # 湿度数据
    └── conversation_log.json   # 对话日志
```

## 🔧 数据格式

### 湿度数据格式
```json
[
  {
    "timestamp": "2024-12-05T10:00:00",
    "humidity": 75.5
  }
]
```

### 对话日志格式
```json
[
  {
    "timestamp": "2024-12-05T10:00:00",
    "type": "system",  // system, user, bot, gesture
    "message": "对话模式已开启"
  }
]
```

## 🌐 与其他模块集成

### 整合到动作识别
在 `gesture_recognition.py` 中添加：

```python
import requests

def send_gesture_to_web(gesture):
    """发送动作到Web服务器"""
    try:
        requests.post('http://localhost:5000/api/gesture', 
                     json={'gesture': gesture})
    except:
        pass

# 在检测到动作后调用
if gesture_detected:
    send_gesture_to_web(gesture_detected)
```

### 整合到语音识别
在 `voice_recognition.py` 中添加：

```python
import requests

def send_conversation_to_web(user_text, bot_text):
    """发送对话到Web服务器"""
    try:
        requests.post('http://localhost:5000/api/speech',
                     json={'user': user_text, 'bot': bot_text})
    except:
        pass

# 在对话时调用
send_conversation_to_web(user_text, response)
```

### 湿度传感器数据上传
```python
import requests
import time

def upload_humidity(humidity):
    """上传湿度数据到Web服务器"""
    try:
        response = requests.post('http://localhost:5000/api/humidity/add',
                                json={'humidity': humidity})
        print(f"湿度数据已上传: {humidity}%")
    except Exception as e:
        print(f"上传失败: {e}")

# 每小时上传一次
while True:
    humidity = read_sensor()  # 从传感器读取
    upload_humidity(humidity)
    time.sleep(3600)  # 等待1小时
```

## 💡 使用场景

### 场景1: 实时监控
- 打开网页
- 查看湿度趋势
- 观察植物状态

### 场景2: 远程对话控制
- 不在电脑旁边
- 通过网页开启/关闭对话
- 查看对话记录

### 场景3: 数据分析
- 查看24小时湿度变化
- 分析最佳浇水时间
- 观察植物生长环境

## 🔒 安全说明

**当前版本**: 开发测试版本
- 仅限本地网络访问
- 无身份验证
- 无数据加密

**生产环境建议**:
- 添加用户认证
- 使用HTTPS
- 限制访问IP
- 添加访问日志

## 🐛 常见问题

### Q1: 无法访问网页
**A:** 检查防火墙，确保5000端口开放

### Q2: 数据不更新
**A:** 
1. 检查Flask服务器是否运行
2. 查看浏览器控制台错误
3. 尝试手动刷新

### Q3: 图表不显示
**A:** 确保有网络连接（需要加载Chart.js库）

### Q4: 数据丢失
**A:** 数据存储在 `data/` 文件夹，确保文件未被删除

## 🚀 扩展功能

### 后续可添加
- 📱 响应式移动端适配
- 🔔 湿度告警通知
- 📸 摄像头画面实时查看
- 📈 更多数据可视化图表
- 🌡️ 温度、光照等传感器数据
- 📅 历史数据查询（超过24小时）
- 🔐 用户登录和权限管理
- 🌍 外网访问配置

## 📞 技术支持

遇到问题请查看:
- Flask文档: https://flask.palletsprojects.com/
- Chart.js文档: https://www.chartjs.org/

---

**祝使用愉快！🌱**
