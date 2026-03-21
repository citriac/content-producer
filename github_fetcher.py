#!/usr/bin/env python3
"""
GitHub Trending 信息抓取
"""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

def fetch_github_trending(period='daily', language=''):
    """
    获取 GitHub Trending

    period: daily, weekly, monthly
    language: 编程语言，如 'python', 'javascript'，空字符串表示所有语言
    """
    url = f"https://github.com/trending/{language}?since={period}"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')

        # 简单解析 HTML（不依赖 BeautifulSoup）
        repos = []
        lines = html.split('\n')

        for i, line in enumerate(lines):
            # 查找仓库名
            if '/repo/' in line or 'data-hydro-click' in line:
                # 这是一个简化版本，实际 GitHub Trending 页面需要更复杂的解析
                # 这里先返回占位数据，后续可以改进
                pass

        # 临时返回空列表，需要更好的解析方法
        return []

    except Exception as e:
        print(f"获取 GitHub Trending 失败: {e}", file=sys.stderr)
        return []

def save_trending(repos, date=None, period='daily'):
    """保存 trending 数据"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    data = {
        "date": date,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "count": len(repos),
        "repos": repos
    }

    filename = f"github-trending-{date}.json"
    filepath = DATA_DIR / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filepath

def main():
    """主流程"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 获取 GitHub Trending...")

    repos = fetch_github_trending(period='daily')

    if repos:
        filepath = save_trending(repos)
        print(f"已保存 {len(repos)} 个仓库到: {filepath}")
    else:
        print("未获取到数据（解析需要改进）")

    return 0 if repos else 1

if __name__ == "__main__":
    sys.exit(main())
