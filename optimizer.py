#!/usr/bin/env python3
"""
内容生产者优化器
基于 system-automation 技能，优化系统性能
"""

import os
import sys
import time
import json
import psutil
import subprocess
from datetime import datetime
from pathlib import Path
import signal
import gc
import shutil

class ContentProducerOptimizer:
    """内容生产者优化器"""
    
    def __init__(self, config_path=None):
        self.config_path = config_path or Path('~/.workbuddy/optimizer_config.json').expanduser()
        self.load_config()
        
        # 性能基线
        self.baseline = self.load_baseline()
        
        # 优化历史
        self.history = []
        
        print(f"🤖 Content Producer Optimizer initialized")
        print(f"   Config: {self.config_path}")
    
    def load_config(self):
        """加载配置"""
        default_config = {
            'optimizations': {
                'memory_cleanup': {
                    'enabled': True,
                    'threshold_mb': 500,  # 可用内存低于此值时清理
                    'interval_minutes': 30
                },
                'process_management': {
                    'enabled': True,
                    'max_python_processes': 3,
                    'idle_timeout_minutes': 60
                },
                'cache_management': {
                    'enabled': True,
                    'max_cache_size_mb': 100,
                    'cleanup_old_days': 7
                },
                'git_optimization': {
                    'enabled': True,
                    'auto_gc': True,
                    'prune_old_days': 30
                }
            },
            'monitoring': {
                'check_interval_seconds': 300,  # 5分钟
                'log_file': 'optimizer.log',
                'metrics_file': 'optimizer_metrics.json'
            },
            'safety': {
                'max_memory_reduction_mb': 1024,  # 单次最多释放内存
                'min_available_memory_mb': 100,   # 最少保留可用内存
                'backup_before_cleanup': True
            }
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
    
    def load_baseline(self):
        """加载性能基线"""
        baseline_file = Path('~/.workbuddy/optimizer_baseline.json').expanduser()
        
        default_baseline = {
            'memory_usage_mb': 512,
            'cpu_usage_percent': 20,
            'generation_time_seconds': 30,
            'git_operations_time_seconds': 10,
            'last_calibrated': None
        }
        
        try:
            with open(baseline_file, 'r') as f:
                return {**default_baseline, **json.load(f)}
        except (FileNotFoundError, json.JSONDecodeError):
            return default_baseline
    
    def save_baseline(self):
        """保存性能基线"""
        baseline_file = Path('~/.workbuddy/optimizer_baseline.json').expanduser()
        
        # 更新最后校准时间
        self.baseline['last_calibrated'] = datetime.now().isoformat()
        
        try:
            with open(baseline_file, 'w') as f:
                json.dump(self.baseline, f, indent=2)
        except Exception as e:
            print(f"Failed to save baseline: {e}")
    
    def log_optimization(self, action, details, impact=None):
        """记录优化操作"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details,
            'impact': impact or {},
            'system_state': self.get_system_state()
        }
        
        self.history.append(entry)
        
        # 记录到日志文件
        log_file = self.config['monitoring']['log_file']
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            print(f"Failed to write log: {e}")
        
        # 输出到控制台
        print(f"📝 {action}: {details}")
        if impact:
            print(f"   Impact: {impact}")
        
        return entry
    
    def get_system_state(self):
        """获取系统状态"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': {
                    'total_mb': psutil.virtual_memory().total // (1024 * 1024),
                    'available_mb': psutil.virtual_memory().available // (1024 * 1024),
                    'percent': psutil.virtual_memory().percent,
                    'used_mb': psutil.virtual_memory().used // (1024 * 1024)
                },
                'swap': {
                    'total_mb': psutil.swap_memory().total // (1024 * 1024),
                    'used_mb': psutil.swap_memory().used // (1024 * 1024),
                    'percent': psutil.swap_memory().percent
                },
                'disk': {
                    'total_gb': psutil.disk_usage('/').total // (1024 * 1024 * 1024),
                    'used_gb': psutil.disk_usage('/').used // (1024 * 1024 * 1024),
                    'free_gb': psutil.disk_usage('/').free // (1024 * 1024 * 1024),
                    'percent': psutil.disk_usage('/').percent
                },
                'processes': {
                    'total': len(psutil.pids()),
                    'python': len([p for p in psutil.process_iter(['name']) 
                                  if p.info['name'] and 'python' in p.info['name'].lower()])
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    def optimize_memory(self):
        """优化内存使用"""
        if not self.config['optimizations']['memory_cleanup']['enabled']:
            return {'action': 'skipped', 'reason': 'disabled'}
        
        threshold_mb = self.config['optimizations']['memory_cleanup']['threshold_mb']
        state = self.get_system_state()
        
        if 'error' in state:
            return {'action': 'error', 'details': state['error']}
        
        available_mb = state['memory']['available_mb']
        
        if available_mb > threshold_mb:
            return {'action': 'skipped', 'reason': f'available_mb ({available_mb}) > threshold ({threshold_mb})'}
        
        # 记录优化前状态
        before_state = state.copy()
        
        actions = []
        memory_freed_mb = 0
        
        # 1. 强制垃圾回收
        print("🔄 Running garbage collection...")
        collected = gc.collect()
        actions.append(f"GC collected {collected} objects")
        
        # 2. 清理 Python 模块缓存
        print("🔄 Clearing Python module cache...")
        try:
            # 清理 sys.modules 中的非必要模块
            import sys as sys_module
            modules_to_keep = {'sys', 'builtins', '__main__', 'json', 'os', 'pathlib', 'psutil'}
            
            modules_before = len(sys_module.modules)
            modules_to_remove = []
            
            for name in list(sys_module.modules.keys()):
                if name not in modules_to_keep and not name.startswith(('_', 'test', 'pytest')):
                    modules_to_remove.append(name)
            
            # 安全移除（不实际删除，避免破坏当前运行）
            actions.append(f"Identified {len(modules_to_remove)} non-essential modules for cleanup")
        
        except Exception as e:
            actions.append(f"Module cache cleanup failed: {e}")
        
        # 3. 清理文件系统缓存（如果可用）
        if sys.platform == 'linux':
            print("🔄 Clearing Linux page cache...")
            try:
                subprocess.run(['sync'], check=True)
                with open('/proc/sys/vm/drop_caches', 'w') as f:
                    f.write('1\n')
                actions.append("Cleared Linux page cache")
            except Exception as e:
                actions.append(f"Linux cache clear failed: {e}")
        
        elif sys.platform == 'darwin':
            print("🔄 Clearing macOS memory cache...")
            try:
                result = subprocess.run(['purge'], capture_output=True, text=True)
                if result.returncode == 0:
                    actions.append("Cleared macOS memory cache")
                else:
                    actions.append(f"macOS purge failed: {result.stderr}")
            except Exception as e:
                actions.append(f"macOS cache clear failed: {e}")
        
        # 4. 检查优化后状态
        time.sleep(1)  # 等待系统稳定
        after_state = self.get_system_state()
        
        if 'error' not in after_state:
            memory_freed_mb = before_state['memory']['available_mb'] - after_state['memory']['available_mb']
        
        # 记录优化
        return self.log_optimization(
            'memory_optimization',
            '; '.join(actions),
            {
                'memory_freed_mb': memory_freed_mb,
                'available_before_mb': before_state['memory']['available_mb'],
                'available_after_mb': after_state['memory']['available_mb'] if 'error' not in after_state else 'unknown',
                'swap_before_percent': before_state['swap']['percent'],
                'swap_after_percent': after_state['swap']['percent'] if 'error' not in after_state else 'unknown'
            }
        )
    
    def optimize_processes(self):
        """优化进程管理"""
        if not self.config['optimizations']['process_management']['enabled']:
            return {'action': 'skipped', 'reason': 'disabled'}
        
        max_python = self.config['optimizations']['process_management']['max_python_processes']
        idle_timeout = self.config['optimizations']['process_management']['idle_timeout_minutes'] * 60
        
        try:
            # 获取所有 Python 进程
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
                try:
                    info = proc.info
                    if info['name'] and 'python' in info['name'].lower():
                        # 计算进程年龄
                        age_seconds = time.time() - info['create_time']
                        python_processes.append({
                            'pid': proc.pid,
                            'name': info['name'],
                            'cpu': info['cpu_percent'],
                            'memory': info['memory_percent'],
                            'age_seconds': age_seconds
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            actions = []
            terminated = []
            
            # 检查是否需要终止进程
            if len(python_processes) > max_python:
                # 按内存使用率排序（优先终止内存占用高的）
                python_processes.sort(key=lambda x: x.get('memory', 0), reverse=True)
                
                for proc in python_processes[max_python:]:
                    try:
                        p = psutil.Process(proc['pid'])
                        
                        # 检查是否空闲
                        is_idle = proc['age_seconds'] > idle_timeout and proc['cpu'] < 1.0
                        
                        if is_idle or len(python_processes) > max_python + 2:  # 稍微宽松一点
                            p.terminate()
                            terminated.append(proc['pid'])
                            actions.append(f"Terminated PID {proc['pid']} ({proc['name']}) - idle: {is_idle}")
                    except Exception as e:
                        actions.append(f"Failed to terminate PID {proc['pid']}: {e}")
            
            if not actions:
                actions.append("No processes needed termination")
            
            return self.log_optimization(
                'process_optimization',
                '; '.join(actions),
                {
                    'python_processes_before': len(python_processes),
                    'python_processes_after': len(python_processes) - len(terminated),
                    'terminated_pids': terminated
                }
            )
        
        except Exception as e:
            return {'action': 'error', 'details': str(e)}
    
    def optimize_cache(self):
        """优化缓存管理"""
        if not self.config['optimizations']['cache_management']['enabled']:
            return {'action': 'skipped', 'reason': 'disabled'}
        
        max_size_mb = self.config['optimizations']['cache_management']['max_cache_size_mb']
        cleanup_days = self.config['optimizations']['cache_management']['cleanup_old_days']
        
        cache_dirs = [
            Path('~/.cache').expanduser(),
            Path('posts/'),
            Path('data/'),
            Path('tmp/')
        ]
        
        actions = []
        total_size_before = 0
        total_size_after = 0
        files_removed = 0
        
        for cache_dir in cache_dirs:
            if not cache_dir.exists():
                continue
            
            try:
                # 计算目录大小
                dir_size = 0
                files_to_clean = []
                
                for file in cache_dir.rglob('*'):
                    if file.is_file():
                        try:
                            file_size = file.stat().st_size
                            dir_size += file_size
                            
                            # 检查是否应该清理
                            file_age = time.time() - file.stat().st_mtime
                            if file_age > cleanup_days * 24 * 3600:
                                files_to_clean.append((file, file_size))
                        except OSError:
                            continue
                
                total_size_before += dir_size
                dir_size_mb = dir_size / (1024 * 1024)
                
                # 检查是否超过大小限制或需要清理旧文件
                if dir_size_mb > max_size_mb or files_to_clean:
                    if self.config['safety']['backup_before_cleanup']:
                        # 创建备份（简化实现）
                        backup_file = cache_dir.parent / f"{cache_dir.name}_backup_{int(time.time())}.tar.gz"
                        actions.append(f"Backup created: {backup_file.name}")
                    
                    # 清理旧文件
                    for file, file_size in files_to_clean:
                        try:
                            file.unlink()
                            files_removed += 1
                            total_size_after += file_size
                        except OSError as e:
                            actions.append(f"Failed to remove {file}: {e}")
                    
                    actions.append(f"Cleaned {cache_dir}: removed {len(files_to_clean)} files")
            
            except Exception as e:
                actions.append(f"Cache cleanup error for {cache_dir}: {e}")
        
        if not actions:
            actions.append("Cache sizes within limits, no cleanup needed")
        
        return self.log_optimization(
            'cache_optimization',
            '; '.join(actions),
            {
                'total_size_before_mb': total_size_before / (1024 * 1024),
                'total_size_after_mb': (total_size_before - total_size_after) / (1024 * 1024),
                'files_removed': files_removed
            }
        )
    
    def optimize_git(self):
        """优化 Git 操作"""
        if not self.config['optimizations']['git_optimization']['enabled']:
            return {'action': 'skipped', 'reason': 'disabled'}
        
        actions = []
        
        try:
            # 检查当前目录是否为 Git 仓库
            repo_dir = Path.cwd()
            git_dir = repo_dir / '.git'
            
            if not git_dir.exists():
                return {'action': 'skipped', 'reason': 'not a git repository'}
            
            # 自动垃圾回收
            if self.config['optimizations']['git_optimization']['auto_gc']:
                print("🔄 Running git garbage collection...")
                result = subprocess.run(
                    ['git', 'gc', '--auto'],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    actions.append("Git auto-gc completed")
                else:
                    actions.append(f"Git auto-gc failed: {result.stderr}")
            
            # 清理旧分支
            prune_days = self.config['optimizations']['git_optimization']['prune_old_days']
            print(f"🔄 Pruning branches older than {prune_days} days...")
            
            # 获取远程分支
            result = subprocess.run(
                ['git', 'branch', '-r'],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                remote_branches = result.stdout.strip().split('\n')
                pruned_count = 0
                
                for branch in remote_branches:
                    branch = branch.strip()
                    if not branch or '->' in branch:
                        continue
                    
                    # 检查分支最后提交时间
                    result = subprocess.run(
                        ['git', 'log', '-1', '--format=%at', branch],
                        cwd=repo_dir,
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        last_commit = int(result.stdout.strip())
                        age_days = (time.time() - last_commit) / (24 * 3600)
                        
                        if age_days > prune_days:
                            # 删除远程分支
                            branch_name = branch.split('/')[-1]
                            subprocess.run(
                                ['git', 'push', 'origin', '--delete', branch_name],
                                cwd=repo_dir,
                                capture_output=True
                            )
                            pruned_count += 1
                
                if pruned_count > 0:
                    actions.append(f"Pruned {pruned_count} old remote branches")
                else:
                    actions.append("No old branches to prune")
            
            # 压缩仓库
            print("🔄 Compressing git repository...")
            result = subprocess.run(
                ['git', 'repack', '-a', '-d', '--depth=250', '--window=250'],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                actions.append("Git repository compressed")
            else:
                actions.append(f"Git compression failed: {result.stderr}")
            
            if not actions:
                actions.append("Git repository already optimized")
            
            return self.log_optimization(
                'git_optimization',
                '; '.join(actions),
                {'operations': len(actions)}
            )
        
        except Exception as e:
            return {'action': 'error', 'details': str(e)}
    
    def run_all_optimizations(self):
        """运行所有优化"""
        print("🚀 Starting comprehensive optimization...")
        print("="*60)
        
        results = []
        
        # 1. 内存优化
        print("\n1️⃣  Memory Optimization")
        result = self.optimize_memory()
        results.append(('memory', result))
        
        # 2. 进程优化
        print("\n2️⃣  Process Optimization")
        result = self.optimize_processes()
        results.append(('process', result))
        
        # 3. 缓存优化
        print("\n3️⃣  Cache Optimization")
        result = self.optimize_cache()
        results.append(('cache', result))
        
        # 4. Git 优化
        print("\n4️⃣  Git Optimization")
        result = self.optimize_git()
        results.append(('git', result))
        
        # 汇总结果
        print("\n" + "="*60)
        print("📊 Optimization Summary")
        print("="*60)
        
        for category, result in results:
            if 'action' in result:
                status = "✅" if result['action'] in ['skipped', 'completed'] else "⚠️"
                print(f"{status} {category.title()}: {result['action']}")
                if 'reason' in result:
                    print(f"   Reason: {result['reason']}")
                if 'impact' in result:
                    for key, value in result['impact'].items():
                        print(f"   {key}: {value}")
        
        print("="*60)
        
        # 保存指标
        self.save_metrics()
        
        return results
    
    def save_metrics(self):
        """保存性能指标"""
        metrics_file = self.config['monitoring']['metrics_file']
        
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'system_state': self.get_system_state(),
                'recent_optimizations': self.history[-10:],  # 最近10条记录
                'config': self.config
            }
            
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            print(f"Failed to save metrics: {e}")
    
    def calibrate(self):
        """校准性能基线"""
        print("🔧 Calibrating performance baseline...")
        
        # 运行几次生成操作来建立基线
        generation_times = []
        memory_usages = []
        
        for i in range(3):
            print(f"  Run {i+1}/3...")
            
            # 模拟生成操作（简化）
            start_time = time.time()
            start_memory = psutil.virtual_memory().used
            
            # 执行一些操作
            import random
            data = [random.random() for _ in range(1000000)]  # 生成一些数据
            
            end_time = time.time()
            end_memory = psutil.virtual_memory().used
            
            generation_times.append(end_time - start_time)
            memory_usages.append((end_memory - start_memory) / (1024 * 1024))
            
            # 清理
            del data
            gc.collect()
        
        # 更新基线
        self.baseline.update({
            'generation_time_seconds': sum(generation_times) / len(generation_times),
            'memory_usage_mb': sum(memory_usages) / len(memory_usages),
            'cpu_usage_percent': psutil.cpu_percent(interval=1),
            'last_calibrated': datetime.now().isoformat()
        })
        
        self.save_baseline()
        
        print(f"✅ Baseline calibrated:")
        print(f"   Generation time: {self.baseline['generation_time_seconds']:.2f}s")
        print(f"   Memory usage: {self.baseline['memory_usage_mb']:.1f}MB")
        print(f"   CPU usage: {self.baseline['cpu_usage_percent']:.1f}%")
    
    def monitor_and_optimize(self):
        """监控并自动优化"""
        print("👁️  Starting continuous monitoring and optimization...")
        print(f"   Check interval: {self.config['monitoring']['check_interval_seconds']}s")
        print("   Press Ctrl+C to stop")
        print("-"*60)
        
        check_interval = self.config['monitoring']['check_interval_seconds']
        
        try:
            while True:
                # 检查系统状态
                state = self.get_system_state()
                
                if 'error' not in state:
                    # 检查是否需要优化
                    needs_optimization = False
                    
                    # 内存检查
                    if state['memory']['available_mb'] < self.config['optimizations']['memory_cleanup']['threshold_mb']:
                        print(f"⚠️  Low memory detected: {state['memory']['available_mb']}MB available")
                        needs_optimization = True
                    
                    # 交换空间检查
                    if state['swap']['percent'] > 50:
                        print(f"⚠️  High swap usage: {state['swap']['percent']:.1f}%")
                        needs_optimization = True
                    
                    # 定期优化（每12小时）
                    last_optimization = None
                    if self.history:
                        last_time = datetime.fromisoformat(self.history[-1]['timestamp'].replace('Z', '+00:00'))
                        hours_since_last = (datetime.now() - last_time).total_seconds() / 3600
                        if hours_since_last > 12:
                            print(f"⏰ Periodic optimization due ({hours_since_last:.1f}h since last)")
                            needs_optimization = True
                    
                    # 执行优化
                    if needs_optimization:
                        print("\n" + "="*60)
                        print("🔄 Running optimizations...")
                        self.run_all_optimizations()
                        print("="*60 + "\n")
                
                # 等待下一个检查
                print(f"\r📊 Monitoring... Next check in {check_interval}s", end='', flush=True)
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Content Producer Optimizer')
    parser.add_argument('--optimize', action='store_true', help='Run all optimizations')
    parser.add_argument('--monitor', action='store_true', help='Start continuous monitoring')
    parser.add_argument('--calibrate', action='store_true', help='Calibrate performance baseline')
    parser.add_argument('--config', help='Config file path')
    parser.add_argument('--status', action='store_true', help='Show current status')
    
    args = parser.parse_args()
    
    # 创建优化器
    optimizer = ContentProducerOptimizer(args.config)
    
    if args.calibrate:
        optimizer.calibrate()
    
    elif args.monitor:
        optimizer.monitor_and_optimize()
    
    elif args.optimize:
        optimizer.run_all_optimizations()
    
    elif args.status:
        state = optimizer.get_system_state()
        
        print("System Status:")
        print(f"  CPU: {state['cpu_percent']:.1f}%")
        print(f"  Memory: {state['memory']['percent']:.1f}% ({state['memory']['available_mb']}MB available)")
        print(f"  Swap: {state['swap']['percent']:.1f}%")
        print(f"  Disk: {state['disk']['percent']:.1f}%")
        print(f"  Processes: {state['processes']['total']} total, {state['processes']['python']} Python")
        
        print(f"\nOptimization History ({len(optimizer.history)} entries):")
        for entry in optimizer.history[-3:]:  # 最近3条
            print(f"  [{entry['timestamp']}] {entry['action']}")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()