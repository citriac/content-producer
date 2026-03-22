#!/usr/bin/env python3
"""
自动化内容生产者 - 主生成器
整合 Hacker News + GitHub Trending，生成高质量技术日报
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
POSTS_DIR = PROJECT_ROOT / "posts"
CONFIG_FILE = PROJECT_ROOT / "config.json"

DATA_DIR.mkdir(exist_ok=True)
POSTS_DIR.mkdir(exist_ok=True)


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "sources": ["hn", "github"],
        "hn_limit": 15,
        "github_days": 7,
        "output_format": "markdown"
    }


# ─── Hacker News 抓取 ─────────────────────────────────────────────────────────

def fetch_hn_stories(limit=15):
    """获取 HN 热门故事"""
    try:
        import urllib.request
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        with urllib.request.urlopen(url, timeout=10) as r:
            story_ids = json.loads(r.read())[:limit * 2]  # 多抓一些备用

        stories = []
        for sid in story_ids:
            if len(stories) >= limit:
                break
            detail_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
            try:
                with urllib.request.urlopen(detail_url, timeout=5) as r:
                    item = json.loads(r.read())
                    if item.get("type") == "story" and item.get("url"):
                        stories.append({
                            "id": sid,
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "score": item.get("score", 0),
                            "by": item.get("by", ""),
                            "descendants": item.get("descendants", 0),
                            "time": item.get("time", 0)
                        })
            except Exception:
                continue

        return sorted(stories, key=lambda x: x["score"], reverse=True)
    except Exception as e:
        print(f"  [!] HN 抓取失败: {e}", file=sys.stderr)
        return []


# ─── GitHub Trending 抓取 ─────────────────────────────────────────────────────

def fetch_github_trending(days=7, limit=10):
    """通过 GitHub Search API 获取热门仓库"""
    try:
        import urllib.request
        import urllib.parse
        from datetime import timedelta

        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        params = urllib.parse.urlencode({
            "q": f"created:>{since}",
            "sort": "stars",
            "order": "desc",
            "per_page": limit
        })
        url = f"https://api.github.com/search/repositories?{params}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Clavis/1.0", "Accept": "application/vnd.github.v3+json"}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())

        repos = []
        for item in data.get("items", []):
            repos.append({
                "name": item["full_name"],
                "description": item.get("description") or "",
                "url": item["html_url"],
                "stars": item["stargazers_count"],
                "language": item.get("language") or "Unknown",
                "topics": item.get("topics", [])[:5],
                "created_at": item.get("created_at", "")[:10]
            })
        return repos
    except Exception as e:
        print(f"  [!] GitHub 抓取失败: {e}", file=sys.stderr)
        return []


# ─── 关键词分析 ───────────────────────────────────────────────────────────────

TECH_KEYWORDS = {
    "AI/LLM": ["ai", "llm", "gpt", "claude", "gemini", "llama", "agent", "rag",
                "mcp", "copilot", "chatgpt", "openai", "anthropic", "transformer",
                "diffusion", "inference", "model", "neural"],
    "基础设施": ["kubernetes", "k8s", "docker", "terraform", "cloud", "serverless",
               "database", "redis", "postgres", "vector", "edge"],
    "编程语言": ["rust", "go", "python", "typescript", "javascript", "deno",
               "bun", "swift", "wasm", "react", "next.js"],
    "安全": ["security", "vulnerability", "cve", "exploit", "breach",
            "encryption", "authentication"],
    "开发工具": ["cli", "vscode", "terminal", "debugger", "linter", "git"]
}

STOP_WORDS = {
    "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of",
    "with", "by", "is", "are", "was", "be", "have", "has", "do", "will",
    "new", "how", "what", "using", "use", "open", "source", "free", "fast",
    "simple", "easy", "based", "support", "from", "this", "that"
}


def detect_hot_topics(hn_stories, gh_repos):
    """检测热门话题"""
    import re
    from collections import Counter

    all_text = []
    for s in hn_stories:
        all_text.append(s.get("title", "").lower())
    for r in gh_repos:
        all_text.append((r.get("name", "") + " " + r.get("description", "")).lower())

    # 词频统计
    word_freq = Counter()
    for text in all_text:
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\-_\.]{2,}\b', text)
        for w in words:
            if w not in STOP_WORDS:
                word_freq[w] += 1

    # 分类打分
    cat_scores = Counter()
    kw_list = [w for w, _ in word_freq.most_common(50)]
    for cat, terms in TECH_KEYWORDS.items():
        for term in terms:
            for kw in kw_list:
                if term in kw or kw in term:
                    cat_scores[cat] += word_freq.get(kw, 1)

    top_words = word_freq.most_common(8)
    hot_cats = cat_scores.most_common(3)
    return top_words, hot_cats


# ─── 日报生成 ─────────────────────────────────────────────────────────────────

def generate_daily_report(hn_stories, gh_repos, date=None):
    """生成高质量技术日报"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 分析热点
    top_words, hot_cats = detect_hot_topics(hn_stories, gh_repos)
    cat_names = [cat for cat, _ in hot_cats]

    # ─── 文章头部 ───
    content = f"# 技术热点日报 | {date}\n\n"
    content += f"> 自动采集 · {now_str} 生成  \n"
    content += f"> 来源：Hacker News {len(hn_stories)} 条 + GitHub Trending {len(gh_repos)} 个项目\n\n"

    # ─── 今日趋势摘要 ───
    if cat_names or top_words:
        content += "## 📊 今日趋势速览\n\n"
        if cat_names:
            content += f"**热门领域**：{'　·　'.join(cat_names)}\n\n"
        if top_words:
            kw_str = "　".join(f"`{w}`" for w, _ in top_words[:6])
            content += f"**高频词汇**：{kw_str}\n\n"

    # ─── HN 热点 ───
    if hn_stories:
        content += "## 🔥 Hacker News 热点\n\n"
        content += "| # | 标题 | 热度 | 评论 |\n"
        content += "|---|------|------|------|\n"
        for i, s in enumerate(hn_stories[:12], 1):
            title = s["title"].replace("|", "｜")
            url = s["url"]
            hn_url = f"https://news.ycombinator.com/item?id={s['id']}"
            comments = s.get("descendants", 0)
            content += f"| {i} | [{title}]({url}) | ⬆ {s['score']} | [💬 {comments}]({hn_url}) |\n"
        content += "\n"

        # Top 3 详细展示
        content += "### 重点关注\n\n"
        for s in hn_stories[:3]:
            content += f"**[{s['title']}]({s['url']})**  \n"
            content += f"热度 {s['score']} · 评论 {s.get('descendants', 0)} · 作者 {s.get('by', 'unknown')}  \n\n"

    # ─── GitHub Trending ───
    if gh_repos:
        content += "## 🚀 GitHub 本周新项目 TOP\n\n"
        for i, r in enumerate(gh_repos[:10], 1):
            lang = r.get("language", "")
            lang_str = f" `{lang}`" if lang and lang != "Unknown" else ""
            desc = r.get("description", "").strip()
            desc_str = f"  \n   > {desc}" if desc else ""
            topics = r.get("topics", [])
            topics_str = " ".join(f"`{t}`" for t in topics[:3]) if topics else ""
            topics_line = f"  \n   {topics_str}" if topics_str else ""
            content += (
                f"**{i}. [{r['name']}]({r['url']})**{lang_str}  \n"
                f"   ⭐ {r['stars']:,} stars{desc_str}{topics_line}\n\n"
            )

    # ─── 尾部 ───
    content += "---\n\n"
    content += "*由 [Clavis](https://github.com/citriac/content-producer) 自动生成*  \n"
    content += "*如果这份日报对你有价值，欢迎 [支持我们](https://github.com/sponsors/citriac)*\n"

    return content


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始内容生成...")

    config = load_config()
    date = datetime.now().strftime("%Y-%m-%d")

    # 1. 获取数据
    print("  正在获取 Hacker News 热点...")
    hn_stories = fetch_hn_stories(limit=config.get("hn_limit", 15))
    print(f"  ✓ 获取到 {len(hn_stories)} 条 HN 故事")

    print("  正在获取 GitHub Trending...")
    gh_repos = fetch_github_trending(
        days=config.get("github_days", 7),
        limit=12
    )
    print(f"  ✓ 获取到 {len(gh_repos)} 个 GitHub 项目")

    if not hn_stories and not gh_repos:
        print("  [!] 未获取到任何数据，退出")
        return 1

    # 2. 保存原始数据
    if hn_stories:
        stories_file = DATA_DIR / f"hn-stories-{date}.json"
        with open(stories_file, "w", encoding="utf-8") as f:
            json.dump(hn_stories, f, indent=2, ensure_ascii=False)

    if gh_repos:
        gh_file = DATA_DIR / f"github-trending-{date}.json"
        with open(gh_file, "w", encoding="utf-8") as f:
            json.dump({"date": date, "count": len(gh_repos), "repos": gh_repos},
                      f, indent=2, ensure_ascii=False)

    # 3. 生成日报
    print("  生成日报...")
    content = generate_daily_report(hn_stories, gh_repos, date)

    # 4. 保存日报
    report_file = POSTS_DIR / f"{date}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ 日报已保存: {report_file}")

    # 5. 保存元数据
    meta = {
        "date": date,
        "timestamp": datetime.now().isoformat(),
        "hn_count": len(hn_stories),
        "github_count": len(gh_repos),
        "file": str(report_file)
    }
    with open(DATA_DIR / f"{date}.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    # 6. 打印摘要
    print(f"\n  日报预览（前 3 条 HN 热点）：")
    for s in hn_stories[:3]:
        print(f"    ⬆ {s['score']:4d} | {s['title'][:60]}")

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 完成!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
