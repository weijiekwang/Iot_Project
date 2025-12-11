#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to translate Chinese comments to English in Python files
"""

import os
import re

# Translation dictionary for common Chinese phrases
TRANSLATIONS = {
    # Common phrases
    "计算两点之间的欧几里得距离": "Calculate Euclidean distance between two points",
    "检测挥手动作": "Detect wave gesture",
    "检测双手举高": "Detect hands raised",
    "检测鼓掌": "Detect clap",
    "检测点头": "Detect nod",
    "检测摇头": "Detect shake head",
    "返回": "Return",
    "参数": "Parameters",
    "返回值": "Returns",

    # Actions and operations
    "处理视频帧": "Process video frame",
    "主循环": "Main loop",
    "初始化": "Initialize",
    "开启": "Start",
    "关闭": "Close",
    "停止": "Stop",
    "启动": "Launch",
    "运行": "Run",
    "执行": "Execute",

    # Hardware related
    "麦克风": "Microphone",
    "扬声器": "Speaker",
    "摄像头": "Camera",
    "显示": "Display",
    "显示屏": "Display screen",
    "传感器": "Sensor",

    # Status and control
    "状态": "Status",
    "模式": "Mode",
    "检查": "Check",
    "更新": "Update",
    "设置": "Set",
    "获取": "Get",
    "读取": "Read",
    "写入": "Write",
    "发送": "Send",
    "接收": "Receive",

    # Data and processing
    "数据": "Data",
    "音频": "Audio",
    "图像": "Image",
    "文本": "Text",
    "处理": "Process",
    "识别": "Recognition",
    "转换": "Convert",

    # Time and counting
    "秒": "second(s)",
    "分钟": "minute(s)",
    "小时": "hour(s)",
    "次": "time(s)",
    "每": "Every",

    # Network and connection
    "连接": "Connect",
    "服务器": "Server",
    "客户端": "Client",
    "网络": "Network",

    # Misc
    "如果": "If",
    "否则": "Otherwise",
    "或者": "Or",
    "并且": "And",
    "当": "When",
    "用于": "Used for",
    "避免": "Avoid",
    "重复": "Duplicate/Repeat",
    "错误": "Error",
    "成功": "Success",
    "失败": "Failure",
}

def has_chinese(text):
    """Check if text contains Chinese characters"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def translate_line(line):
    """Translate Chinese in a line to English"""
    # Only process comment lines
    if not '#' in line:
        return line

    # Don't translate if no Chinese characters
    if not has_chinese(line):
        return line

    # Extract comment part
    parts = line.split('#', 1)
    if len(parts) != 2:
        return line

    before_comment = parts[0]
    comment = parts[1]

    # Try simple replacements from dictionary
    translated_comment = comment
    for chinese, english in TRANSLATIONS.items():
        if chinese in translated_comment:
            translated_comment = translated_comment.replace(chinese, english)

    # If still has Chinese after simple replacement, return original
    # (Manual review needed for complex phrases)
    return before_comment + '#' + translated_comment

def process_file(filepath):
    """Process a single Python file"""
    print(f"Processing: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        translated_lines = [translate_line(line) for line in lines]

        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(translated_lines)

        print(f"  ✓ Completed")
    except Exception as e:
        print(f"  ✗ Error: {e}")

def main():
    """Main function"""
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Find all Python files with Chinese comments
    python_files = []
    for root, dirs, files in os.walk(base_dir):
        # Skip .git and other hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            if file.endswith('.py') and file != 'translate_comments.py':
                filepath = os.path.join(root, file)
                python_files.append(filepath)

    print(f"Found {len(python_files)} Python files to check\n")

    # Process each file
    for filepath in python_files:
        process_file(filepath)

    print("\nTranslation complete!")
    print("Note: Complex phrases may need manual review")

if __name__ == '__main__':
    main()
