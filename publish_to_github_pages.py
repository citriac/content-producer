#!/usr/bin/env python3
"""
GitHub Pages 发布脚本
自动将生成的日报推送到 citriac.github.io 仓库
"""

import json
import subprocess
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import shutil

PROJECT_ROOT = Path(__file__).parent
CONTENT_DIR = PROJECT_ROOT / "docs"
GITHUB_PAGES_DIR = Path("/Users/malt/WorkBuddy/Claw/github-pages")
DATA_DIR = PROJECT_ROOT / "data"
POSTS_DIR = PROJECT_ROOT / "posts"

def run_command(cmd, cwd=None, check=True):
    """运行命令并返回结果"""
    print(f"  $ {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"  ❌ 命令失败: {e}")
        if e.stderr:
            print(f"  stderr: {e.stderr.strip()}")
        if check:
            raise
        return None

def check_git_status():
    """检查Git状态"""
    print("🔍 检查Git状态...")
    
    # 检查是否在git仓库中
    if not (GITHUB_PAGES_DIR / ".git").exists():
        print("  ❌ GitHub Pages目录不是git仓库")
        return False
    
    # 检查是否有未提交的更改
    try:
        status = run_command("git status --porcelain", cwd=GITHUB_PAGES_DIR)
        if status:
            print(f"  ⚠️  有未提交的更改:\n{status}")
            return True
        else:
            print("  ✓ 工作目录干净")
            return True
    except Exception as e:
        print(f"  ❌ 检查Git状态失败: {e}")
        return False

def update_website_data():
    """更新网站数据"""
    print("📊 更新网站数据...")
    
    # 构建站点数据
    print("  运行站点构建脚本...")
    try:
        run_command(f"python3 {PROJECT_ROOT / 'build_site.py'}")
    except Exception as e:
        print(f"  ❌ 构建站点失败: {e}")
        return False
    
    # 复制最新的日报数据
    print("  复制数据文件...")
    
    # 确保目录存在
    (GITHUB_PAGES_DIR / "data").mkdir(exist_ok=True)
    
    # 复制最新的数据文件
    data_files = list((CONTENT_DIR / "data").glob("*.json"))
    if not data_files:
        print("  ⚠️  没有找到数据文件")
        return False
    
    for data_file in data_files:
        target_file = GITHUB_PAGES_DIR / "data" / data_file.name
        shutil.copy2(data_file, target_file)
        print(f"  ✓ 复制 {data_file.name}")
    
    # 更新daily.html
    daily_source = CONTENT_DIR / "index.html"
    daily_target = GITHUB_PAGES_DIR / "daily.html"
    
    if daily_source.exists():
        # 读取内容并添加返回首页链接
        with open(daily_source, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 在header中添加返回首页链接
        header_pattern = '<nav class="header-links">'
        new_header = '''<nav class="header-links">
    <a href="index.html">🏠 首页</a>
    <a href="https://github.com/citriac/content-producer" target="_blank">GitHub</a>
    <a href="https://clavis-hn-api.citriac.deno.net" target="_blank">API</a>
    <a href="https://github.com/sponsors/citriac" target="_blank">❤ 支持</a>
  </nav>'''
        
        if header_pattern in content:
            # 替换整个nav部分
            start = content.find(header_pattern)
            end = content.find('</nav>', start) + 6
            old_nav = content[start:end]
            content = content.replace(old_nav, new_header)
        
        with open(daily_target, "w", encoding="utf-8") as f:
            f.write(content)
        print("  ✓ 更新 daily.html")
    
    return True

def update_index_page():
    """更新主页的最近更新日期"""
    print("🏠 更新主页...")
    
    index_file = GITHUB_PAGES_DIR / "index.html"
    if not index_file.exists():
        print("  ⚠️  主页不存在")
        return False
    
    with open(index_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 更新最后更新日期
    today = datetime.now().strftime("%Y-%m-%d")
    old_date = "最后更新：2026-03-22"
    new_date = f"最后更新：{today}"
    
    if old_date in content:
        content = content.replace(old_date, new_date)
    
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"  ✓ 更新最后更新日期为 {today}")
    return True

def commit_and_push():
    """提交并推送更改"""
    print("🚀 提交并推送更改...")
    
    try:
        # 添加所有更改
        run_command("git add .", cwd=GITHUB_PAGES_DIR)
        
        # 提交
        today = datetime.now().strftime("%Y-%m-%d")
        commit_message = f"Auto-update: Daily tech trends for {today}"
        
        run_command(f'git commit -m "{commit_message}"', cwd=GITHUB_PAGES_DIR)
        
        # 检查远程仓库（兼容 SSH 和 HTTPS 两种格式）
        remotes = run_command("git remote -v", cwd=GITHUB_PAGES_DIR)
        if not remotes or "citriac.github.io" not in remotes:
            print("  ⚠️  未配置远程仓库，跳过推送")
            print("  请手动运行: git remote add origin git@github.com:citriac/citriac.github.io.git")
            print("  然后运行: git push -u origin main")
            return False
        
        # 推送
        print("  推送到GitHub...")
        run_command("git push origin main", cwd=GITHUB_PAGES_DIR)
        
        print(f"  ✅ 成功推送到GitHub Pages")
        print(f"  🌐 访问: https://citriac.github.io")
        return True
        
    except Exception as e:
        print(f"  ❌ 提交/推送失败: {e}")
        return False

def main():
    """主函数"""
    print(f"🚀 GitHub Pages 自动发布脚本")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # 检查前提条件
    if not GITHUB_PAGES_DIR.exists():
        print(f"❌ GitHub Pages目录不存在: {GITHUB_PAGES_DIR}")
        print(f"请先运行: git clone https://github.com/citriac/citriac.github.io.git {GITHUB_PAGES_DIR}")
        return 1
    
    # 检查是否有今天的日报数据
    today = datetime.now().strftime("%Y-%m-%d")
    today_post = POSTS_DIR / f"{today}.md"
    
    if not today_post.exists():
        print(f"⚠️  今天的日报尚未生成: {today}")
        print("请先运行内容生成器")
        return 0  # 非错误，只是跳过
    
    # 执行发布流程
    steps = [
        ("检查Git状态", check_git_status),
        ("更新网站数据", update_website_data),
        ("更新主页", update_index_page),
        ("提交并推送", commit_and_push),
    ]
    
    success = True
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}")
        try:
            if not step_func():
                print(f"  ❌ {step_name}失败")
                success = False
                break
        except Exception as e:
            print(f"  ❌ {step_name}出错: {e}")
            success = False
            break
    
    if success:
        print(f"\n🎉 GitHub Pages发布完成!")
        print(f"   网站: https://citriac.github.io")
        print(f"   日报: https://citriac.github.io/daily.html")
    else:
        print(f"\n⚠️  GitHub Pages发布部分完成或失败")
        print(f"   请检查错误并手动完成")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())