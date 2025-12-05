"""
智能盆栽Web监控系统 - 公网访问版本
使用 pyngrok 创建公网访问链接
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import json
import os
from threading import Lock

app = Flask(__name__)

# 数据文件路径
DATA_DIR = "data"
HUMIDITY_FILE = os.path.join(DATA_DIR, "humidity_data.json")
CONVERSATION_FILE = os.path.join(DATA_DIR, "conversation_log.json")

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

# 线程锁
data_lock = Lock()

# 对话状态
conversation_state = {
    "active": False,
    "started_at": None
}

def load_humidity_data():
    """加载湿度数据"""
    if os.path.exists(HUMIDITY_FILE):
        try:
            with open(HUMIDITY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_humidity_data(data):
    """保存湿度数据"""
    with data_lock:
        with open(HUMIDITY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def load_conversation_log():
    """加载对话记录"""
    if os.path.exists(CONVERSATION_FILE):
        try:
            with open(CONVERSATION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_conversation_log(log):
    """保存对话记录"""
    with data_lock:
        with open(CONVERSATION_FILE, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

def get_last_24h_humidity():
    """获取过去24小时的湿度数据"""
    all_data = load_humidity_data()
    now = datetime.now()
    past_24h = now - timedelta(hours=24)
    
    filtered_data = [
        entry for entry in all_data
        if datetime.fromisoformat(entry['timestamp']) >= past_24h
    ]
    
    return filtered_data

def generate_sample_data():
    """生成示例数据（用于测试）"""
    now = datetime.now()
    sample_data = []
    
    for i in range(24, 0, -1):
        timestamp = now - timedelta(hours=i)
        humidity = 65 + (i % 5) * 3 + ((-1) ** i) * 2
        sample_data.append({
            "timestamp": timestamp.isoformat(),
            "humidity": humidity
        })
    
    save_humidity_data(sample_data)
    return sample_data

# 初始化示例数据
if not os.path.exists(HUMIDITY_FILE):
    generate_sample_data()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/humidity')
def get_humidity():
    """获取湿度数据API"""
    data = get_last_24h_humidity()
    return jsonify({
        "success": True,
        "data": data,
        "count": len(data)
    })

@app.route('/api/conversation/status')
def get_conversation_status():
    """获取对话状态API"""
    return jsonify({
        "success": True,
        "active": conversation_state["active"],
        "started_at": conversation_state["started_at"]
    })

@app.route('/api/conversation/start', methods=['POST'])
def start_conversation():
    """开启对话API"""
    conversation_state["active"] = True
    conversation_state["started_at"] = datetime.now().isoformat()
    
    log = load_conversation_log()
    log.append({
        "timestamp": datetime.now().isoformat(),
        "type": "system",
        "message": "对话模式已开启"
    })
    save_conversation_log(log)
    
    return jsonify({
        "success": True,
        "message": "对话已开启",
        "active": True
    })

@app.route('/api/conversation/stop', methods=['POST'])
def stop_conversation():
    """关闭对话API"""
    conversation_state["active"] = False
    
    log = load_conversation_log()
    log.append({
        "timestamp": datetime.now().isoformat(),
        "type": "system",
        "message": "对话模式已关闭"
    })
    save_conversation_log(log)
    
    return jsonify({
        "success": True,
        "message": "对话已关闭",
        "active": False
    })

@app.route('/api/conversation/log')
def get_conversation_log():
    """获取对话记录API"""
    log = load_conversation_log()
    recent_log = log[-50:] if len(log) > 50 else log
    return jsonify({
        "success": True,
        "data": recent_log
    })

@app.route('/api/gesture', methods=['POST'])
def log_gesture():
    """记录动作识别结果"""
    data = request.json
    gesture = data.get('gesture', '')
    
    log = load_conversation_log()
    log.append({
        "timestamp": datetime.now().isoformat(),
        "type": "gesture",
        "gesture": gesture,
        "message": f"动作: {gesture}"
    })
    save_conversation_log(log)
    
    return jsonify({
        "success": True,
        "message": f"动作 {gesture} 已记录"
    })

@app.route('/api/speech', methods=['POST'])
def log_speech():
    """记录语音识别和回复"""
    data = request.json
    user_text = data.get('user', '')
    bot_text = data.get('bot', '')
    
    log = load_conversation_log()
    if user_text:
        log.append({
            "timestamp": datetime.now().isoformat(),
            "type": "user",
            "message": user_text
        })
    if bot_text:
        log.append({
            "timestamp": datetime.now().isoformat(),
            "type": "bot",
            "message": bot_text
        })
    save_conversation_log(log)
    
    return jsonify({
        "success": True,
        "message": "对话已记录"
    })

@app.route('/api/humidity/add', methods=['POST'])
def add_humidity():
    """添加湿度数据（供传感器调用）"""
    data = request.json
    humidity = data.get('humidity', 0)
    
    all_data = load_humidity_data()
    all_data.append({
        "timestamp": datetime.now().isoformat(),
        "humidity": humidity
    })
    save_humidity_data(all_data)
    
    return jsonify({
        "success": True,
        "message": "湿度数据已添加"
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🌱 智能盆栽Web监控系统 - 公网访问版")
    print("=" * 60)
    
    # 尝试导入 pyngrok
    try:
        from pyngrok import ngrok
        
        # 启动 ngrok 隧道
        public_url = ngrok.connect(8080)
        print(f"✅ 公网访问链接: {public_url}")
        print(f"📱 任何人都可以通过这个链接访问你的网站！")
        print(f"\n本地访问地址: http://localhost:8080")
        
    except ImportError:
        print("⚠️  未安装 pyngrok")
        print("   运行: pip install pyngrok")
        print("   即可获得公网访问功能")
        print(f"\n本地访问地址: http://localhost:8080")
    except Exception as e:
        print(f"⚠️  Ngrok 启动失败: {e}")
        print(f"本地访问地址: http://localhost:8080")
    
    print("\n💡 提示:")
    print("  - 公网链接有效期24小时（免费版）")
    print("  - 按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8080)
