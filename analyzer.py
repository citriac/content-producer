#!/usr/bin/env python3
"""
内容分析器
分析抓取的内容，提取趋势关键词，生成有价值的洞察
"""

import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
POSTS_DIR = PROJECT_ROOT / "posts"

# 技术关键词分类
TECH_CATEGORIES = {
    "AI/LLM": [
        "ai", "llm", "gpt", "claude", "gemini", "llama", "mistral", "agent",
        "rag", "embedding", "fine-tuning", "transformer", "diffusion",
        "copilot", "chatgpt", "openai", "anthropic", "multimodal", "mcp",
        "inference", "model", "neural", "deep learning", "machine learning"
    ],
    "基础设施": [
        "kubernetes", "k8s", "docker", "terraform", "ansible", "devops",
        "ci/cd", "cloud", "serverless", "edge", "cdn", "aws", "gcp", "azure",
        "database", "redis", "postgres", "mysql", "mongodb", "vector"
    ],
    "编程语言/框架": [
        "rust", "go", "golang", "python", "typescript", "javascript",
        "react", "vue", "next.js", "deno", "bun", "swift", "kotlin",
        "wasm", "webassembly", "htmx", "tailwind"
    ],
    "安全": [
        "security", "vulnerability", "cve", "exploit", "breach", "malware",
        "ransomware", "phishing", "zero-day", "encryption", "crypto",
        "authentication", "oauth", "jwt"
    ],
    "开发工具": [
        "vscode", "neovim", "vim", "cursor", "copilot", "debugger",
        "profiler", "linter", "formatter", "cli", "terminal", "shell",
        "git", "github", "gitlab"
    ],
    "硬件/芯片": [
        "gpu", "cpu", "chip", "nvidia", "amd", "apple silicon", "risc-v",
        "tpu", "npu", "hardware", "semiconductor", "quantum"
    ],
    "Web3/区块链": [
        "blockchain", "bitcoin", "ethereum", "defi", "nft", "web3",
        "solana", "crypto", "token", "smart contract"
    ]
}

# 需要忽略的通用词
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "this", "that", "these", "those",
    "it", "its", "he", "she", "they", "we", "you", "i", "my", "your",
    "his", "her", "their", "our", "new", "how", "why", "what", "when",
    "where", "who", "which", "using", "use", "used", "show", "shows",
    "make", "makes", "made", "get", "gets", "got", "go", "goes", "went",
    "open", "source", "free", "fast", "simple", "easy", "based", "support"
}


def extract_keywords(texts, top_n=20):
    """从文本列表中提取关键词频率"""
    word_count = Counter()
    for text in texts:
        # 转小写，提取单词
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\.\-_]{2,}\b', text.lower())
        for word in words:
            if word not in STOP_WORDS and len(word) > 2:
                word_count[word] += 1
    return word_count.most_common(top_n)


def categorize_keywords(keywords):
    """将关键词映射到技术分类"""
    category_scores = Counter()
    keyword_list = [kw.lower() for kw, _ in keywords]

    for category, terms in TECH_CATEGORIES.items():
        for term in terms:
            for kw in keyword_list:
                if term in kw or kw in term:
                    category_scores[category] += 1

    return category_scores.most_common()


def analyze_hn_stories(stories):
    """分析 HN 故事，提取洞察"""
    if not stories:
        return {}

    titles = [s.get("title", "") for s in stories]
    all_text = " ".join(titles)

    # 提取关键词
    keywords = extract_keywords(titles, top_n=30)

    # 分类分析
    categories = categorize_keywords(keywords)

    # 高分故事（按 score 排序）
    sorted_stories = sorted(stories, key=lambda x: x.get("score", 0), reverse=True)
    top_stories = sorted_stories[:5]

    # 平均分
    scores = [s.get("score", 0) for s in stories]
    avg_score = sum(scores) / len(scores) if scores else 0

    return {
        "total": len(stories),
        "avg_score": round(avg_score, 1),
        "top_keywords": keywords[:10],
        "hot_categories": categories[:4],
        "top_stories": top_stories,
        "all_titles": titles
    }


def analyze_github_repos(repos):
    """分析 GitHub 仓库，提取趋势"""
    if not repos:
        return {}

    # 按类别分组
    by_category = {}
    for repo in repos:
        cat = repo.get("category", "其他")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(repo)

    # 语言分布
    lang_count = Counter(r.get("language", "Unknown") for r in repos)

    # 提取描述关键词
    descs = [r.get("description", "") + " " + r.get("name", "") for r in repos]
    keywords = extract_keywords(descs, top_n=20)

    # 热门 topics
    topic_count = Counter()
    for repo in repos:
        for topic in repo.get("topics", []):
            topic_count[topic] += 1

    # 最高 star 仓库
    top_repos = sorted(repos, key=lambda x: x.get("stars", 0), reverse=True)[:5]

    return {
        "total": len(repos),
        "by_category": by_category,
        "top_languages": lang_count.most_common(5),
        "top_topics": topic_count.most_common(8),
        "top_keywords": keywords[:10],
        "top_repos": top_repos
    }


def generate_insights(hn_analysis, gh_analysis, date=None):
    """生成综合洞察"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    insights = []

    # HN 趋势洞察
    if hn_analysis:
        top_kw = [kw for kw, _ in hn_analysis.get("top_keywords", [])[:5]]
        hot_cats = [cat for cat, _ in hn_analysis.get("hot_categories", [])[:2]]

        if hot_cats:
            insights.append(f"HN 社区今日讨论热点集中在 **{' / '.join(hot_cats)}** 领域")
        if top_kw:
            insights.append(f"高频词汇：{', '.join(f'`{k}`' for k in top_kw[:6])}")

        avg = hn_analysis.get("avg_score", 0)
        if avg > 100:
            insights.append(f"今日内容热度较高，平均热度 {avg} 分，社区参与度活跃")

    # GitHub 趋势洞察
    if gh_analysis:
        top_langs = [lang for lang, _ in gh_analysis.get("top_languages", [])[:3]
                     if lang != "Unknown"]
        top_topics = [t for t, _ in gh_analysis.get("top_topics", [])[:4]]
        top_repos = gh_analysis.get("top_repos", [])

        if top_langs:
            insights.append(f"GitHub 本周新项目主要使用 **{' / '.join(top_langs)}**")
        if top_topics:
            insights.append(f"热门标签：{', '.join(f'`{t}`' for t in top_topics)}")
        if top_repos:
            best = top_repos[0]
            insights.append(
                f"本周最受关注新项目：[{best['name']}]({best['url']})，"
                f"⭐ {best['stars']:,} stars"
            )

    # 综合判断
    if hn_analysis and gh_analysis:
        hn_cats = set(cat for cat, _ in hn_analysis.get("hot_categories", []))
        gh_kw = set(kw for kw, _ in gh_analysis.get("top_keywords", []))
        # 简单交叉：看 AI 是否双榜皆热
        ai_terms = {"ai", "llm", "agent", "model", "gpt", "claude", "openai"}
        if hn_cats & {"AI/LLM"} or any(t in gh_kw for t in ai_terms):
            insights.append("🔥 AI/LLM 持续占据技术圈热点，开发者关注度不减")

    return insights


def load_today_data(date=None):
    """加载今日数据"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    result = {"hn_stories": [], "gh_repos": []}

    # HN 数据
    hn_file = DATA_DIR / f"{date}.json"
    if hn_file.exists():
        with open(hn_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
        # 检查是否有完整 stories 数据
        stories_file = DATA_DIR / f"hn-stories-{date}.json"
        if stories_file.exists():
            with open(stories_file, "r", encoding="utf-8") as f:
                result["hn_stories"] = json.load(f)

    # GitHub 数据
    gh_file = DATA_DIR / f"github-trending-{date}.json"
    if gh_file.exists():
        with open(gh_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            result["gh_repos"] = data.get("repos", [])

    return result


def main():
    """主流程"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 运行内容分析...")

    data = load_today_data()
    stories = data["hn_stories"]
    repos = data["gh_repos"]

    print(f"  HN 故事数: {len(stories)}")
    print(f"  GitHub 仓库数: {len(repos)}")

    if not stories and not repos:
        print("  没有数据可分析，请先运行 generator.py")
        return 1

    hn_analysis = analyze_hn_stories(stories) if stories else {}
    gh_analysis = analyze_github_repos(repos) if repos else {}
    insights = generate_insights(hn_analysis, gh_analysis)

    print(f"\n洞察（{len(insights)} 条）：")
    for i, insight in enumerate(insights, 1):
        print(f"  {i}. {insight}")

    # 保存分析结果
    date = datetime.now().strftime("%Y-%m-%d")
    analysis_data = {
        "date": date,
        "timestamp": datetime.now().isoformat(),
        "hn": hn_analysis,
        "github": gh_analysis,
        "insights": insights
    }

    analysis_file = DATA_DIR / f"analysis-{date}.json"
    with open(analysis_file, "w", encoding="utf-8") as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)

    print(f"\n分析结果已保存: {analysis_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
