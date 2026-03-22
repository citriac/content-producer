#!/usr/bin/env python3
"""
站点构建器
把 posts/*.md 对应的 JSON 数据导出到 docs/data/
并更新 docs/index.html 中的 REPORTS 列表
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
POSTS_DIR = PROJECT_ROOT / "posts"
DOCS_DIR = PROJECT_ROOT / "docs"
DOCS_DATA_DIR = DOCS_DIR / "data"

DOCS_DIR.mkdir(exist_ok=True)
DOCS_DATA_DIR.mkdir(exist_ok=True)


def build_report_json(date):
    """把某天的数据整合成前端友好的 JSON"""
    result = {
        "date": date,
        "generated_at": datetime.now().isoformat(),
        "hn_stories": [],
        "gh_repos": [],
        "trends": {}
    }

    # HN 故事
    hn_file = DATA_DIR / f"hn-stories-{date}.json"
    if hn_file.exists():
        with open(hn_file, "r", encoding="utf-8") as f:
            result["hn_stories"] = json.load(f)

    # GitHub 仓库
    gh_file = DATA_DIR / f"github-trending-{date}.json"
    if gh_file.exists():
        with open(gh_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            result["gh_repos"] = data.get("repos", [])

    # 分析结果
    analysis_file = DATA_DIR / f"analysis-{date}.json"
    if analysis_file.exists():
        with open(analysis_file, "r", encoding="utf-8") as f:
            analysis = json.load(f)
            gh = analysis.get("github", {})
            hn = analysis.get("hn", {})
            result["trends"] = {
                "hot_categories": hn.get("hot_categories", []) or gh.get("top_keywords", []),
                "top_keywords": hn.get("top_keywords", []),
                "insights": analysis.get("insights", [])
            }

    return result


def find_available_dates():
    """找出所有有完整数据的日期"""
    dates = set()

    # 从 meta 文件找日期
    for f in DATA_DIR.glob("????-??-??.json"):
        d = f.stem
        if re.match(r"\d{4}-\d{2}-\d{2}", d):
            dates.add(d)

    # 从 posts 找日期
    for f in POSTS_DIR.glob("????-??-??.md"):
        d = f.stem
        if re.match(r"\d{4}-\d{2}-\d{2}", d):
            dates.add(d)

    return sorted(dates, reverse=True)


def update_index_html(dates):
    """把日期列表写入 index.html"""
    index_file = DOCS_DIR / "index.html"
    if not index_file.exists():
        print("  [!] docs/index.html 不存在，跳过", file=sys.stderr)
        return

    with open(index_file, "r", encoding="utf-8") as f:
        html = f.read()

    dates_json = json.dumps(dates, ensure_ascii=False)
    new_html = re.sub(
        r'const REPORTS = .*?;',
        f'const REPORTS = {dates_json};',
        html
    )

    with open(index_file, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"  ✓ 更新 index.html，包含 {len(dates)} 个日期")


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 构建站点数据...")

    dates = find_available_dates()
    print(f"  找到 {len(dates)} 个日期: {', '.join(dates)}")

    built = 0
    for date in dates:
        out_file = DOCS_DATA_DIR / f"{date}.json"
        data = build_report_json(date)

        # 只有有实际内容才写出
        if data["hn_stories"] or data["gh_repos"]:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            print(f"  ✓ {date}: HN {len(data['hn_stories'])} 条, GitHub {len(data['gh_repos'])} 个")
            built += 1
        else:
            print(f"  - {date}: 无详细数据，跳过")

    # 更新 index.html
    valid_dates = [
        d for d in dates
        if (DOCS_DATA_DIR / f"{d}.json").exists()
    ]
    update_index_html(valid_dates)

    print(f"\n构建完成：{built} 个日报 → docs/data/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
