#!/usr/bin/env python3
"""
内容生产监控器
基于 system-automation 技能，监控系统资源并优化性能
"""

import os
import sys
import time
import json
import signal
import psutil
from datetime import datetime
from pathlib import Path
import threading
import queue

class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self, config_path=None):
        self.config_path = config_path or Path('~/.workbuddy/monitor_config.json').expanduser()
        self.load_config()
        
        # 监控状态
        self.running = False
        self.monitor_thread = None
        self.data_queue = queue.Queue()
        
        # 历史数据
        self.history = {
            'cpu': [],
            'memory': [],
            'disk': [],
            'network': []
        }
        
        # 告警状态
        self.alarms = {
            'high_memory': False,
            'high_cpu': False,
            'low_disk': False,
            'high_swap': False
        }
    
    def load_config(self):
        """加载配置"""
        default_config = {
            'monitor_interval': 5,  # 监控间隔（秒）
            'history_size': 100,     # 历史数据点数量
            'thresholds': {
                'memory_percent': 85,      # 内存使用率阈值
                'cpu_percent': 80,         # CPU使用率阈值
                'disk_percent': 90,        # 磁盘使用率阈值
                'swap_percent': 50,        # 交换空间使用率阈值
                'memory_available_mb': 100  # 可用内存阈值（MB）
            },
            'actions': {
                'clear_cache_on_high_memory': True,
                'restart_on_critical': False,
                'notify_on_alert': True
            },
            'log_file': 'monitor.log',
            'data_file': 'monitor_data.json'
        }
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = {**default_config, **json.load(f)}
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def collect_metrics(self):
        """收集系统指标"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'freq': psutil.cpu_freq().current if hasattr(psutil.cpu_freq(), 'current') else None,
                'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
            },
            'memory': {
                'total_mb': psutil.virtual_memory().total // (1024 * 1024),
                'available_mb': psutil.virtual_memory().available // (1024 * 1024),
                'percent': psutil.virtual_memory().percent,
                'used_mb': psutil.virtual_memory().used // (1024 * 1024),
                'free_mb': psutil.virtual_memory().free // (1024 * 1024)
            },
            'swap': {
                'total_mb': psutil.swap_memory().total // (1024 * 1024),
                'used_mb': psutil.swap_memory().used // (1024 * 1024),
                'percent': psutil.swap_memory().percent,
                'free_mb': psutil.swap_memory().free // (1024 * 1024)
            },
            'disk': {
                'total_gb': psutil.disk_usage('/').total // (1024 * 1024 * 1024),
                'used_gb': psutil.disk_usage('/').used // (1024 * 1024 * 1024),
                'free_gb': psutil.disk_usage('/').free // (1024 * 1024 * 1024),
                'percent': psutil.disk_usage('/').percent
            },
            'network': {
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv,
                'packets_sent': psutil.net_io_counters().packets_sent,
                'packets_recv': psutil.net_io_counters().packets_recv
            },
            'processes': {
                'total': len(psutil.pids()),
                'python': len([p for p in psutil.process_iter(['name']) if 'python' in p.info['name'].lower()]),
                'memory_hogs': self.get_memory_hogs(5)
            }
        }
        
        return metrics
    
    def get_memory_hogs(self, limit=5):
        """获取内存占用最高的进程"""
        hogs = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
            try:
                info = proc.info
                if info['memory_percent'] is not None:
                    hogs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 按内存使用率排序
        hogs.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
        return hogs[:limit]
    
    def check_thresholds(self, metrics):
        """检查阈值并触发告警"""
        thresholds = self.config['thresholds']
        new_alarms = {}
        
        # 检查内存
        if metrics['memory']['percent'] > thresholds['memory_percent']:
            new_alarms['high_memory'] = True
            if not self.alarms['high_memory']:
                self.trigger_alert('HIGH_MEMORY', metrics['memory'])
        else:
            new_alarms['high_memory'] = False
        
        # 检查可用内存
        if metrics['memory']['available_mb'] < thresholds['memory_available_mb']:
            new_alarms['low_available_memory'] = True
            if not self.alarms.get('low_available_memory', False):
                self.trigger_alert('LOW_AVAILABLE_MEMORY', metrics['memory'])
        else:
            new_alarms['low_available_memory'] = False
        
        # 检查 CPU
        if metrics['cpu']['percent'] > thresholds['cpu_percent']:
            new_alarms['high_cpu'] = True
            if not self.alarms['high_cpu']:
                self.trigger_alert('HIGH_CPU', metrics['cpu'])
        else:
            new_alarms['high_cpu'] = False
        
        # 检查磁盘
        if metrics['disk']['percent'] > thresholds['disk_percent']:
            new_alarms['low_disk'] = True
            if not self.alarms['low_disk']:
                self.trigger_alert('LOW_DISK_SPACE', metrics['disk'])
        else:
            new_alarms['low_disk'] = False
        
        # 检查交换空间
        if metrics['swap']['percent'] > thresholds['swap_percent']:
            new_alarms['high_swap'] = True
            if not self.alarms['high_swap']:
                self.trigger_alert('HIGH_SWAP_USAGE', metrics['swap'])
        else:
            new_alarms['high_swap'] = False
        
        # 更新告警状态
        self.alarms.update(new_alarms)
        
        return new_alarms
    
    def trigger_alert(self, alert_type, data):
        """触发告警"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"[{timestamp}] ALERT: {alert_type} - {json.dumps(data, indent=2)}"
        
        print(f"⚠️  {message}")
        
        # 记录到日志
        self.log_message('ALERT', message)
        
        # 执行相应动作
        self.execute_actions(alert_type)
    
    def execute_actions(self, alert_type):
        """执行相应的动作"""
        actions = self.config['actions']
        
        if alert_type == 'HIGH_MEMORY' and actions.get('clear_cache_on_high_memory', False):
            self.clear_memory_cache()
        
        if alert_type in ['HIGH_CPU', 'HIGH_MEMORY'] and actions.get('restart_on_critical', False):
            # 在真实环境中可能需要重启特定服务
            print("⚠️  Critical condition detected. Consider restarting heavy processes.")
    
    def clear_memory_cache(self):
        """清理内存缓存"""
        print("🔄 Clearing memory cache...")
        
        try:
            # 清理 Python 内存
            import gc
            collected = gc.collect()
            print(f"  GC collected {collected} objects")
            
            # 尝试清理系统缓存（需要权限）
            if sys.platform == 'linux':
                # Linux: 清除页面缓存
                os.system('sync; echo 1 > /proc/sys/vm/drop_caches 2>/dev/null || true')
            elif sys.platform == 'darwin':
                # macOS: 使用 purge 命令
                os.system('purge 2>/dev/null || true')
            
            print("  Memory cache cleared")
            
        except Exception as e:
            print(f"  Failed to clear cache: {e}")
    
    def log_message(self, level, message):
        """记录日志消息"""
        log_file = self.config.get('log_file', 'monitor.log')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            with open(log_file, 'a') as f:
                f.write(f"[{timestamp}] [{level}] {message}\n")
        except Exception as e:
            print(f"Failed to write log: {e}")
    
    def save_history(self, metrics):
        """保存历史数据"""
        # 添加到历史
        for key in ['cpu', 'memory', 'disk', 'network']:
            if key in metrics:
                self.history[key].append(metrics[key])
                
                # 限制历史数据大小
                history_size = self.config.get('history_size', 100)
                if len(self.history[key]) > history_size:
                    self.history[key] = self.history[key][-history_size:]
        
        # 定期保存到文件
        data_file = self.config.get('data_file', 'monitor_data.json')
        try:
            with open(data_file, 'w') as f:
                json.dump({
                    'history': self.history,
                    'last_update': datetime.now().isoformat(),
                    'alarms': self.alarms
                }, f, indent=2)
        except Exception as e:
            print(f"Failed to save data: {e}")
    
    def monitor_loop(self):
        """监控主循环"""
        print(f"📊 Starting resource monitor (interval: {self.config['monitor_interval']}s)")
        
        while self.running:
            try:
                # 收集指标
                metrics = self.collect_metrics()
                
                # 检查阈值
                alarms = self.check_thresholds(metrics)
                
                # 保存历史
                self.save_history(metrics)
                
                # 输出状态
                self.print_status(metrics, alarms)
                
                # 等待下一个间隔
                time.sleep(self.config['monitor_interval'])
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(1)
    
    def print_status(self, metrics, alarms):
        """输出状态信息"""
        # 构建状态行
        status_parts = []
        
        # CPU
        cpu_percent = metrics['cpu']['percent']
        cpu_status = f"CPU:{cpu_percent:.1f}%"
        if alarms.get('high_cpu', False):
            cpu_status = f"⚠️{cpu_status}"
        status_parts.append(cpu_status)
        
        # 内存
        mem_percent = metrics['memory']['percent']
        mem_avail = metrics['memory']['available_mb']
        mem_status = f"MEM:{mem_percent:.1f}%({mem_avail}MB)"
        if alarms.get('high_memory', False) or alarms.get('low_available_memory', False):
            mem_status = f"⚠️{mem_status}"
        status_parts.append(mem_status)
        
        # 磁盘
        disk_percent = metrics['disk']['percent']
        disk_status = f"DISK:{disk_percent:.1f}%"
        if alarms.get('low_disk', False):
            disk_status = f"⚠️{disk_status}"
        status_parts.append(disk_status)
        
        # 进程数
        proc_total = metrics['processes']['total']
        proc_python = metrics['processes']['python']
        status_parts.append(f"PROC:{proc_total}(py:{proc_python})")
        
        # 输出状态行
        print(f"\r📊 {' | '.join(status_parts)}", end='', flush=True)
    
    def start(self):
        """启动监控器"""
        if self.running:
            print("Monitor already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        print(f"✅ Resource monitor started (PID: {os.getpid()})")
        print(f"   Config: {self.config_path}")
        print(f"   Log: {self.config.get('log_file', 'monitor.log')}")
        print(f"   Press Ctrl+C to stop")
    
    def stop(self):
        """停止监控器"""
        self.running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        print("\n🛑 Resource monitor stopped")
        
        # 输出最终报告
        self.generate_report()
    
    def generate_report(self, hours=24):
        """生成报告"""
        print("\n" + "="*60)
        print("RESOURCE MONITOR REPORT")
        print("="*60)
        
        # 加载最新数据
        data_file = self.config.get('data_file', 'monitor_data.json')
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            history = data.get('history', {})
            
            # 分析内存使用
            if history.get('memory'):
                mem_data = history['memory']
                avg_memory = sum(m['percent'] for m in mem_data) / len(mem_data)
                max_memory = max(m['percent'] for m in mem_data)
                
                print(f"\n📈 Memory Usage:")
                print(f"   Average: {avg_memory:.1f}%")
                print(f"   Maximum: {max_memory:.1f}%")
                print(f"   Samples: {len(mem_data)}")
            
            # 分析 CPU 使用
            if history.get('cpu'):
                cpu_data = history['cpu']
                avg_cpu = sum(c['percent'] for c in cpu_data) / len(cpu_data)
                max_cpu = max(c['percent'] for c in cpu_data)
                
                print(f"\n⚡ CPU Usage:")
                print(f"   Average: {avg_cpu:.1f}%")
                print(f"   Maximum: {max_cpu:.1f}%")
            
            # 告警统计
            alarms = data.get('alarms', {})
            active_alarms = [k for k, v in alarms.items() if v]
            
            if active_alarms:
                print(f"\n⚠️  Active Alarms:")
                for alarm in active_alarms:
                    print(f"   - {alarm}")
            else:
                print(f"\n✅ No active alarms")
                
        except Exception as e:
            print(f"\n❌ Failed to generate report: {e}")
        
        print("="*60)

def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\nReceived signal {signum}, shutting down...")
    if 'monitor' in globals():
        monitor.stop()
    sys.exit(0)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Resource Monitor for Content Producer')
    parser.add_argument('--config', help='Config file path')
    parser.add_argument('--interval', type=int, help='Monitor interval in seconds')
    parser.add_argument('--report', action='store_true', help='Generate report and exit')
    parser.add_argument('--status', action='store_true', help='Show current status and exit')
    
    args = parser.parse_args()
    
    # 创建监控器
    monitor = ResourceMonitor(args.config)
    
    # 覆盖配置
    if args.interval:
        monitor.config['monitor_interval'] = args.interval
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if args.report:
        # 生成报告
        monitor.generate_report()
        return
    
    if args.status:
        # 显示当前状态
        metrics = monitor.collect_metrics()
        alarms = monitor.check_thresholds(metrics)
        
        print("Current System Status:")
        print(f"  CPU: {metrics['cpu']['percent']:.1f}%")
        print(f"  Memory: {metrics['memory']['percent']:.1f}% (Available: {metrics['memory']['available_mb']}MB)")
        print(f"  Disk: {metrics['disk']['percent']:.1f}%")
        print(f"  Swap: {metrics['swap']['percent']:.1f}%")
        
        if any(alarms.values()):
            print("\n⚠️  Active Alarms:")
            for alarm, active in alarms.items():
                if active:
                    print(f"  - {alarm}")
        
        # 显示内存占用最高的进程
        print("\nTop Memory Hogs:")
        for i, hog in enumerate(metrics['processes']['memory_hogs'], 1):
            print(f"  {i}. PID {hog['pid']}: {hog['name']} - {hog.get('memory_percent', 0):.1f}%")
        
        return
    
    # 启动监控
    monitor.start()
    
    try:
        # 保持主线程运行
        while monitor.running:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop()

if __name__ == '__main__':
    main()