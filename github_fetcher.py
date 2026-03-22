#!/usr/bin/env python3
"""
GitHub Trending 信息抓取
使用 GitHub Search API 获取近期热门仓库
"""

import json
import sys
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

GITHUB_API = "https://api.github.com/search/repositories"
HEADERS = {
    "User-Agent": "Clavis-ContentProducer/1.0",
    "Accept": "application/vnd.github.v3+json"
}


def fetch_github_trending(days=7, language="", limit=15):
    """
    获取 GitHub 近期热门仓库

    days: 查找最近 N 天内创建的仓库
    language: 筛选编程语言，空字符串表示所有语言
    limit: 返回数量
    """
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    query = f"created:>{since_date}"
    if language:
        query += f" language:{language}"

    params = urllib.parse.urlencode({
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": min(limit, 30)
    })

    url = f"{GITHUB_API}?{params}"

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read())

        repos = []
        for item in data.get("items", []):
            repos.append({
                "name": item["full_name"],
                "description": item.get("description") or "",
                "url": item["html_url"],
                "stars": item["stargazers_count"],
                "language": item.get("language") or "Unknown",
                "topics": item.get("topics", [])[:5],
                "created_at": item.get("created_at", "")[:10],
                "forks": item.get("forks_count", 0)
            })

        return repos

    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("GitHub API 速率限制，稍后再试", file=sys.stderr)
        else:
            print(f"GitHub API 错误: {e.code}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"获取 GitHub Trending 失败: {e}", file=sys.stderr)
        return []


def fetch_multiple_languages(days=7, limit_per_lang=5):
    """获取多个热门语言的 trending"""
    languages = ["python", "typescript", "go", "rust"]
    all_repos = []
    seen = set()

    # 先获取综合榜
    general = fetch_github_trending(days=days, limit=10)
    for r in general:
        if r["name"] not in seen:
            seen.add(r["name"])
            r["category"] = "综合热门"
            all_repos.append(r)

    # 再按语言获取
    for lang in languages:
        repos = fetch_github_trending(days=days, language=lang, limit=limit_per_lang)
        for r in repos:
            if r["name"] not in seen:
                seen.add(r["name"])
                r["category"] = f"{lang.capitalize()} 热门"
                all_repos.append(r)

    return all_repos


def save_trending(repos, date=None, period="daily"):
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

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filepath


def main():
    """主流程"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 获取 GitHub Trending...")

    repos = fetch_multiple_languages(days=7, limit_per_lang=5)

    if repos:
        filepath = save_trending(repos)
        print(f"已保存 {len(repos)} 个仓库到: {filepath}")
        for r in repos[:5]:
            print(f"  ⭐ {r['stars']:,} | {r['name']} | {r['description'][:50]}")
    else:
        print("未获取到数据")

    return 0 if repos else 1


if __name__ == "__main__":
    sys.exit(main())
