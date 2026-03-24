#!/usr/bin/env python3
"""
web_reader.py — Clavis 智能网页内容抓取器
策略优先级：
  1. Jina Reader (r.jina.ai) — 普通静态页面，返回干净 Markdown，零配置
  2. urllib fallback — Jina 失败时降级，返回原始 HTML
  3. (预留) Scrapling — 动态/反爬页面，需要安装依赖时启用

用法：
    from web_reader import fetch_page, fetch_page_json

    md = fetch_page("https://example.com")       # 返回 Markdown 字符串
    data = fetch_page_json("https://api.xxx/v1") # 返回 dict（适合 JSON API）
"""

import urllib.request
import urllib.parse
import json
import time
from typing import Optional

JINA_BASE = "https://r.jina.ai/"
DEFAULT_UA = "Clavis-WebReader/1.0 (github.com/citriac)"
DEFAULT_TIMEOUT = 15

# Jina 免费限额追踪（每天 200 次，跨进程不共享，仅供参考）
_jina_calls_today = 0
_jina_date = None
JINA_DAILY_LIMIT = 200


def _reset_jina_counter():
    global _jina_calls_today, _jina_date
    today = time.strftime("%Y-%m-%d")
    if _jina_date != today:
        _jina_calls_today = 0
        _jina_date = today


def fetch_page(url: str, prefer_jina: bool = True, timeout: int = DEFAULT_TIMEOUT) -> Optional[str]:
    """
    抓取网页内容，返回 Markdown 字符串（Jina）或原始 HTML（fallback）。
    
    Args:
        url: 目标 URL
        prefer_jina: True 时优先用 Jina Reader（推荐），False 时直接用 urllib
        timeout: 超时秒数
    
    Returns:
        字符串内容，失败时返回 None
    """
    global _jina_calls_today
    _reset_jina_counter()

    # 1. 尝试 Jina Reader
    if prefer_jina and _jina_calls_today < JINA_DAILY_LIMIT:
        jina_url = JINA_BASE + url
        try:
            req = urllib.request.Request(
                jina_url,
                headers={
                    "User-Agent": DEFAULT_UA,
                    "Accept": "text/plain",
                }
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content = resp.read().decode("utf-8", errors="replace")
                if content and len(content) > 100:
                    _jina_calls_today += 1
                    return content
        except Exception as e:
            # Jina 失败，降级
            pass

    # 2. Fallback: urllib 直接抓取
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": DEFAULT_UA}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            return content
    except Exception as e:
        return None


def fetch_page_json(url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[dict]:
    """
    抓取 JSON API，直接返回解析后的 dict。
    不使用 Jina（JSON API 不需要清洗），直接走 urllib。
    """
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": DEFAULT_UA}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return None


def fetch_multiple(urls: list, prefer_jina: bool = True, delay: float = 0.5) -> dict:
    """
    批量抓取多个 URL，返回 {url: content} 字典。
    delay: 每次请求间隔（秒），避免触发限频
    """
    results = {}
    for i, url in enumerate(urls):
        content = fetch_page(url, prefer_jina=prefer_jina)
        results[url] = content
        if i < len(urls) - 1:
            time.sleep(delay)
    return results


def extract_title_from_markdown(md: str) -> str:
    """从 Jina 返回的 Markdown 中提取标题"""
    for line in md.splitlines():
        line = line.strip()
        if line.startswith("Title:"):
            return line[6:].strip()
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def jina_usage_info() -> dict:
    """返回今日 Jina 使用情况"""
    _reset_jina_counter()
    return {
        "used_today": _jina_calls_today,
        "remaining": JINA_DAILY_LIMIT - _jina_calls_today,
        "limit": JINA_DAILY_LIMIT,
    }


# ── 快速测试 ────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://news.ycombinator.com"
    print(f"Testing web_reader with: {test_url}\n")

    print("[Jina] Fetching...")
    content = fetch_page(test_url, prefer_jina=True)
    if content:
        lines = content.splitlines()
        print(f"✅ Got {len(content)} chars, {len(lines)} lines")
        print("--- First 20 lines ---")
        print("\n".join(lines[:20]))
        print(f"\nJina usage: {jina_usage_info()}")
    else:
        print("❌ Failed to fetch")
