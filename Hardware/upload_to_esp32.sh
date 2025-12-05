#!/bin/bash
# upload_to_esp32.sh - 一键上传所有文件到ESP32

PORT="/dev/ttyUSB0"  # 修改为你的串口

echo "=================================="
echo "上传文件到ESP32"
echo "=================================="

# 检查mpremote是否安装
if ! command -v mpremote &> /dev/null; then
    echo "错误: 未安装 mpremote"
    echo "请运行: pip install mpremote"
    exit 1
fi

# 上传所有文件
echo "上传 config.py..."
mpremote connect $PORT fs cp config.py :

echo "上传 main.py..."
mpremote connect $PORT fs cp main.py :

echo "上传 wifi_manager.py..."
mpremote connect $PORT fs cp wifi_manager.py :

echo "上传 mic_module.py..."
mpremote connect $PORT fs cp mic_module.py :

echo "上传 speaker_module.py..."
mpremote connect $PORT fs cp speaker_module.py :

echo "上传 oled_module.py..."
mpremote connect $PORT fs cp oled_module.py :

echo "上传 camera_module.py..."
mpremote connect $PORT fs cp camera_module.py :

echo "=================================="
echo "✅ 所有文件上传完成！"
echo "=================================="
echo ""
echo "接下来："
echo "1. 修改 config.py 中的服务器IP"
echo "2. 运行: mpremote connect $PORT run main.py"
echo ""
