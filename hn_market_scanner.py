#!/usr/bin/env python3
"""
HN Market Signal Scanner
扫描 Hacker News，发现工具类帖子的热度信号，找到真实的市场需求
每天运行，把结果存成 JSON，供内容生产流水线使用
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
import time

# Jina 增强抓取（可选，用于获取帖子全文）
try:
    from web_reader import fetch_page, fetch_page_json, extract_title_from_markdown
    JINA_AVAILABLE = True
except ImportError:
    JINA_AVAILABLE = False

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

HN_SEARCH = "https://hn.algolia.com/api/v1/search"
HN_ITEM   = "https://hacker-news.firebaseio.com/v0/item/{}.json"

# 我们关注的工具类关键词
TOOL_SIGNALS = [
    "Show HN",
    "Ask HN: Is there a tool",
    "Ask HN: What do you use for",
    "Ask HN: How do you",
    "built a tool",
    "open source",
    "free tool",
]

# 付费意愿高的受众关键词
HIGH_VALUE_TAGS = [
    "lawyer", "legal", "contract",
    "founder", "startup", "saas",
    "developer", "engineer",
    "prompt", "llm", "agent",
    "nomad", "remote",
    "spreadsheet", "excel",
    "api", "webhook", "automation",
]

def fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Clavis-MarketScanner/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  [warn] fetch failed: {url[:60]}... — {e}")
        return None

def score_post(title, points, num_comments, age_hours):
    """给帖子打分，综合考虑热度、时效性和话题相关性"""
    # 基础分 = 点赞 + 评论*2（评论更有价值）
    base = points + num_comments * 2
    
    # 时效性衰减（24小时内权重最高）
    if age_hours < 24:
        recency = 1.0
    elif age_hours < 72:
        recency = 0.7
    else:
        recency = 0.4
    
    # 话题加成
    title_lower = title.lower()
    topic_bonus = sum(1 for t in HIGH_VALUE_TAGS if t in title_lower)
    
    return base * recency * (1 + topic_bonus * 0.2)

def scan_show_hn(days=2, min_points=10):
    """扫描近期 Show HN 帖子"""
    print(f"\n[1/3] Scanning Show HN posts (last {days} days, min {min_points} pts)...")
    
    params = urllib.parse.urlencode({
        "query": "Show HN",
        "tags": "show_hn",
        "numericFilters": f"points>{min_points},created_at_i>{int((datetime.now() - timedelta(days=days)).timestamp())}",
        "hitsPerPage": 50
    })
    
    data = fetch_url(f"{HN_SEARCH}?{params}")
    if not data:
        return []
    
    results = []
    for hit in data.get("hits", []):
        age_h = (time.time() - hit.get("created_at_i", 0)) / 3600
        score = score_post(
            hit.get("title", ""),
            hit.get("points", 0),
            hit.get("num_comments", 0),
            age_h
        )
        results.append({
            "type": "show_hn",
            "title": hit.get("title", ""),
            "url": hit.get("url", f"https://news.ycombinator.com/item?id={hit.get('objectID')}"),
            "hn_url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            "points": hit.get("points", 0),
            "comments": hit.get("num_comments", 0),
            "age_hours": round(age_h, 1),
            "score": round(score, 1),
            "author": hit.get("author", ""),
        })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"  Found {len(results)} Show HN posts")
    return results[:20]

def scan_ask_hn(days=3):
    """扫描近期 Ask HN 里的工具需求帖"""
    print(f"\n[2/3] Scanning Ask HN for tool requests...")
    
    queries = [
        "Ask HN: Is there a tool",
        "Ask HN: What do you use",
        "Ask HN: How do you manage",
        "Ask HN: Best tool for",
    ]
    
    results = []
    seen = set()
    
    for q in queries:
        params = urllib.parse.urlencode({
            "query": q,
            "tags": "ask_hn",
            "numericFilters": f"created_at_i>{int((datetime.now() - timedelta(days=days)).timestamp())}",
            "hitsPerPage": 20
        })
        data = fetch_url(f"{HN_SEARCH}?{params}")
        if not data:
            continue
        
        for hit in data.get("hits", []):
            oid = hit.get("objectID")
            if oid in seen:
                continue
            seen.add(oid)
            
            age_h = (time.time() - hit.get("created_at_i", 0)) / 3600
            score = score_post(hit.get("title",""), hit.get("points",0), hit.get("num_comments",0), age_h)
            
            results.append({
                "type": "ask_hn",
                "title": hit.get("title", ""),
                "hn_url": f"https://news.ycombinator.com/item?id={oid}",
                "points": hit.get("points", 0),
                "comments": hit.get("num_comments", 0),
                "age_hours": round(age_h, 1),
                "score": round(score, 1),
            })
        
        time.sleep(0.3)  # 避免触发 rate limit
    
    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"  Found {len(results)} Ask HN tool requests")
    return results[:15]

def extract_insights(show_hn, ask_hn):
    """从数据里提炼洞察：哪些话题热、哪些需求没被满足"""
    insights = {
        "hot_topics": [],
        "unmet_needs": [],
        "competitor_launches": [],
    }
    
    # 分析 Show HN 里的热门话题
    for post in show_hn[:10]:
        title = post["title"].lower()
        tags = [t for t in HIGH_VALUE_TAGS if t in title]
        if post["score"] > 50 or post["points"] > 100:
            insights["hot_topics"].append({
                "title": post["title"],
                "points": post["points"],
                "tags": tags,
                "url": post["hn_url"],
            })
    
    # 分析 Ask HN 里没人满足的需求
    for post in ask_hn:
        # 如果有大量评论但点赞不多，说明人们在讨论但没有好答案
        if post["comments"] > 5 and post["points"] < 30:
            insights["unmet_needs"].append({
                "title": post["title"],
                "discussion": post["hn_url"],
                "signal": "active discussion, no clear winner",
            })
    
    return insights

def enrich_top_posts(posts, max_enrich=3):
    """
    用 Jina Reader 抓取最热帖子的全文，提取更丰富的信息。
    只处理前 max_enrich 条，避免超出 Jina 每日限额。
    """
    if not JINA_AVAILABLE:
        return posts
    
    enriched = 0
    for post in posts:
        if enriched >= max_enrich:
            break
        if post.get("points", 0) < 30:  # 只抓热门帖
            continue
        
        try:
            content = fetch_page(post["hn_url"], prefer_jina=True, timeout=12)
            if content and len(content) > 500:
                # 从全文中提取摘要（取正文前 500 字）
                lines = [l for l in content.splitlines() if l.strip() and not l.startswith("#")]
                body_preview = " ".join(lines[:8])[:400]
                post["body_preview"] = body_preview
                post["full_content_fetched"] = True
                enriched += 1
                time.sleep(0.5)
        except Exception:
            pass
    
    return posts


def analyze_opportunity(show_hn, ask_hn, enrich=True):
    """给出今日机会评分，可选用 Jina 增强全文抓取"""
    all_posts = show_hn + ask_hn
    
    # 统计话题频率
    topic_counts = {}
    for post in all_posts:
        title_lower = post["title"].lower()
        for tag in HIGH_VALUE_TAGS:
            if tag in title_lower:
                topic_counts[tag] = topic_counts.get(tag, 0) + 1
    
    top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # 可选：用 Jina 抓取最热帖子全文
    if enrich and JINA_AVAILABLE:
        print("  [Jina] Enriching top posts with full content...")
        show_hn = enrich_top_posts(show_hn, max_enrich=3)
    
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "scan_time": datetime.now().isoformat(),
        "total_posts_scanned": len(all_posts),
        "top_topics": [{"topic": t, "mentions": c} for t, c in top_topics],
        "show_hn_posts": show_hn,
        "ask_hn_posts": ask_hn,
        "insights": extract_insights(show_hn, ask_hn),
        "jina_available": JINA_AVAILABLE,
    }

def save_report(data):
    today = datetime.now().strftime("%Y-%m-%d")
    out = DATA_DIR / f"hn-signals-{today}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Report saved: {out}")
    return out

def print_summary(data):
    print("\n" + "="*60)
    print(f"📊 HN Market Signal Report — {data['date']}")
    print("="*60)
    
    print(f"\n🔥 Top Topics Today:")
    for t in data["top_topics"]:
        bar = "█" * t["mentions"]
        print(f"  {t['topic']:20s} {bar} ({t['mentions']})")
    
    print(f"\n🚀 Hottest Show HN Posts:")
    for p in data["show_hn_posts"][:5]:
        print(f"  [{p['points']:3d}pts {p['comments']:2d}💬] {p['title'][:65]}")
    
    if data["insights"]["unmet_needs"]:
        print(f"\n💡 Unmet Needs Detected:")
        for n in data["insights"]["unmet_needs"][:3]:
            print(f"  → {n['title'][:65]}")
            print(f"    {n['discussion']}")
    
    print(f"\n📈 Opportunity Score Inputs:")
    print(f"  Posts scanned:   {data['total_posts_scanned']}")
    print(f"  Show HN results: {len(data['show_hn_posts'])}")
    print(f"  Ask HN results:  {len(data['ask_hn_posts'])}")

def main():
    print("🔍 Clavis HN Market Signal Scanner")
    print(f"   Running at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    show = scan_show_hn(days=2, min_points=10)
    ask = scan_ask_hn(days=3)
    
    report = analyze_opportunity(show, ask)
    out_path = save_report(report)
    print_summary(report)
    
    return str(out_path)

if __name__ == "__main__":
    main()
