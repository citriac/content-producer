#!/usr/bin/env python3
"""
定时任务调度器
简化版调度器，无需额外依赖
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
GENERATOR = PROJECT_ROOT / "generator.py"
LOG_FILE = PROJECT_ROOT / "scheduler.log"

def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(log_entry, end='')

    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)

def run_generator():
    """运行内容生成器"""
    try:
        result = subprocess.run(
            [sys.executable, str(GENERATOR)],
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )

        log(f"生成器执行完成，返回码: {result.returncode}")
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                log(f"  {line}")
        if result.stderr:
            for line in result.stderr.strip().split('\n'):
                log(f"  ERROR: {line}")

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log("生成器执行超时")
        return False
    except Exception as e:
        log(f"生成器执行异常: {e}")
        return False

def main():
    """主循环"""
    log("=== 调度器启动 ===")

    # 立即执行一次
    log("首次执行内容生成...")
    run_generator()

    # 定时执行（每天凌晨2点）
    while True:
        now = datetime.now()
        next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)

        # 如果已经过了今天的执行时间，计算明天的
        if now >= next_run:
            from datetime import timedelta
            next_run = next_run + timedelta(days=1)

        wait_seconds = (next_run - now).total_seconds()
        wait_hours = wait_seconds / 3600

        log(f"下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}, 等待 {wait_hours:.1f} 小时")

        # 等待到执行时间
        time.sleep(wait_seconds)

        log("定时执行内容生成...")
        run_generator()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("调度器被中断，退出")
        sys.exit(0)
    except Exception as e:
        log(f"调度器异常: {e}")
        sys.exit(1)
