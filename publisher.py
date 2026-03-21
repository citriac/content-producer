#!/usr/bin/env python3
"""
内容发布管理器
管理已生成内容的发布状态
"""

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
POSTS_DIR = PROJECT_ROOT / "posts"
PUBLISH_STATUS = PROJECT_ROOT / "data" / "publish_status.json"

def load_publish_status():
    """加载发布状态"""
    if PUBLISH_STATUS.exists():
        with open(PUBLISH_STATUS, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_publish_status(status):
    """保存发布状态"""
    with open(PUBLISH_STATUS, 'r', encoding='utf-8') as f:
        f.write(json.dumps(status, indent=2, ensure_ascii=False))

def get_posts_list():
    """获取所有文章"""
    posts = []
    for file in POSTS_DIR.glob("*.md"):
        if file.name.startswith("publish-"):
            continue
        posts.append(file)
    return sorted(posts, key=lambda x: x.stat().st_mtime, reverse=True)

def update_status(post_file, platform, status, url=None):
    """更新发布状态"""
    status_data = load_publish_status()

    post_name = post_file.name
    if post_name not in status_data:
        status_data[post_name] = {
            "created": datetime.fromtimestamp(post_file.stat().st_mtime).isoformat(),
            "platforms": {}
        }

    status_data[post_name]["platforms"][platform] = {
        "status": status,  # pending, published, failed
        "url": url,
        "updated": datetime.now().isoformat()
    }

    with open(PUBLISH_STATUS, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=2, ensure_ascii=False)

def generate_publish_report():
    """生成发布报告"""
    status = load_publish_status()
    posts = get_posts_list()

    report = "# 内容发布状态报告\n\n"
    report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    for post in posts[:10]:  # 最近10篇
        post_name = post.name
        post_status = status.get(post_name, {})

        report += f"## {post_name}\n"
        report += f"- 创建时间: {datetime.fromtimestamp(post.stat().st_mtime).strftime('%Y-%m-%d')}\n"

        platforms = post_status.get("platforms", {})
        if platforms:
            for platform, data in platforms.items():
                status_icon = "✅" if data["status"] == "published" else "⏳" if data["status"] == "pending" else "❌"
                report += f"- {status_icon} {platform}: {data['status']}"
                if data.get("url"):
                    report += f" [{data['url']}]({data['url']})"
                report += "\n"
        else:
            report += "- 未发布\n"

        report += "\n"

    return report

def main():
    """主流程"""
    # 生成发布报告
    report = generate_publish_report()
    print(report)

    # 保存报告
    report_file = PROJECT_ROOT / "posts" / "publish-status.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"发布报告已保存到: {report_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
