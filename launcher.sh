#!/bin/bash
# 内容生产者启动脚本

cd "$(dirname "$0")"

echo "启动内容生产者调度器..."
echo "日志文件: scheduler.log"
echo "按 Ctrl+C 停止"
echo ""

python3 scheduler.py
