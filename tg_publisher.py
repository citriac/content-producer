#!/usr/bin/env python3
"""
Telegram 推送器
将每日技术日报推送到 Telegram Channel
使用方式：
  1. 在 @BotFather 创建 Bot，拿到 BOT_TOKEN
  2. 把 Bot 添加为 Channel 管理员
  3. 获取 Channel 的 CHAT_ID（如 @mychannel 或 -1001234567890）
  4. 设置环境变量：TG_BOT_TOKEN 和 TG_CHAT_ID
  5. 运行: python3 tg_publisher.py

在 GitHub Actions 中：
  在仓库 Settings → Secrets → Actions 添加这两个 secret
"""

import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
POSTS_DIR = PROJECT_ROOT / "posts"

TG_API = "https://api.telegram.org/bot{token}/{method}"


def tg_request(token, method, data):
    """调用 Telegram Bot API"""
    url = TG_API.format(token=token, method=method)
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "User-Agent": "Clavis/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  Telegram API 错误: {e}", file=sys.stderr)
        return None


def format_digest(date=None):
    """将日报格式化为 Telegram 消息（Markdown v2）"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # 加载 HN 数据
    hn_file = DATA_DIR / f"hn-stories-{date}.json"
    gh_file = DATA_DIR / f"github-trending-{date}.json"
    analysis_file = DATA_DIR / f"analysis-{date}.json"

    hn_stories = []
    gh_repos = []
    insights = []

    if hn_file.exists():
        with open(hn_file, "r", encoding="utf-8") as f:
            hn_stories = json.load(f)

    if gh_file.exists():
        with open(gh_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            gh_repos = data.get("repos", [])

    if analysis_file.exists():
        with open(analysis_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            insights = data.get("insights", [])

    if not hn_stories and not gh_repos:
        return None

    # ── 构建消息（HTML 模式，更安全） ──
    lines = [
        f"<b>📡 技术热点日报 | {date}</b>",
        f"<i>来源：HN {len(hn_stories)} 条 + GitHub {len(gh_repos)} 项目</i>",
        "",
    ]

    # 洞察
    if insights:
        lines.append("📊 <b>今日趋势</b>")
        for insight in insights[:3]:
            # 去掉 Markdown 加粗符号
            clean = insight.replace("**", "").replace("`", "")
            lines.append(f"• {clean}")
        lines.append("")

    # HN Top 5
    if hn_stories:
        lines.append("🔥 <b>Hacker News 热点</b>")
        for i, s in enumerate(hn_stories[:5], 1):
            score = s.get("score", 0)
            title = s.get("title", "")[:60]
            url = s.get("url", "")
            lines.append(f'{i}. <a href="{url}">{title}</a> ⬆{score}')
        lines.append("")

    # GitHub Top 3
    if gh_repos:
        lines.append("🚀 <b>GitHub 本周热门</b>")
        for r in gh_repos[:3]:
            name = r.get("name", "")
            url = r.get("url", "")
            stars = r.get("stars", 0)
            desc = (r.get("description") or "")[:40]
            lang = r.get("language", "")
            lang_str = f" [{lang}]" if lang and lang != "Unknown" else ""
            lines.append(f'• <a href="{url}">{name}</a>{lang_str} ⭐{stars:,}')
            if desc:
                lines.append(f'  <i>{desc}</i>')
        lines.append("")

    # 底部
    lines.append(
        '📖 <a href="https://citriac.github.io/content-producer">在线阅读</a> · '
        '📡 <a href="https://clavis-hn-api.citriac.deno.net/daily">API</a> · '
        '❤ <a href="https://github.com/sponsors/citriac">赞助</a>'
    )

    return "\n".join(lines)


def send_digest(token, chat_id, date=None):
    """发送日报到 Telegram"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    message = format_digest(date)
    if not message:
        print(f"  无法生成 {date} 的消息（数据缺失）")
        return False

    result = tg_request(token, "sendMessage", {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "disable_notification": False,
    })

    if result and result.get("ok"):
        msg_id = result["result"].get("message_id")
        print(f"  ✓ 消息发送成功，message_id: {msg_id}")
        return True
    else:
        print(f"  ✗ 发送失败: {result}", file=sys.stderr)
        return False


def main():
    token = os.environ.get("TG_BOT_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")

    if not token or not chat_id:
        print("缺少环境变量 TG_BOT_TOKEN 或 TG_CHAT_ID")
        print("使用方法：")
        print("  TG_BOT_TOKEN=<token> TG_CHAT_ID=<chat_id> python3 tg_publisher.py")
        print("")
        print("Telegram Bot 设置步骤：")
        print("  1. 找 @BotFather 创建 bot，拿到 token")
        print("  2. 创建 Channel，把 bot 加为管理员")
        print("  3. CHAT_ID = Channel 的 @username 或数字 ID")
        return 1

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 推送日报到 Telegram...")
    success = send_digest(token, chat_id)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
