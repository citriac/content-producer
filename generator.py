#!/usr/bin/env python3
"""
自动化内容生产者
定期抓取热点资讯，生成文章并发布
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
POSTS_DIR = PROJECT_ROOT / "posts"
CONFIG_FILE = PROJECT_ROOT / "config.json"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
POSTS_DIR.mkdir(exist_ok=True)

def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "sources": [
            {"name": "Hacker News", "type": "hn"},
            {"name": "GitHub Trending", "type": "github"},
        ],
        "output_format": "markdown",
        "target_platforms": ["local"],
        "schedule": "daily"
    }

def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def fetch_hacker_news_top_stories(limit=10):
    """获取 Hacker News 头条"""
    try:
        import urllib.request
        import urllib.error
        
        # 获取 top stories ID 列表
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        with urllib.request.urlopen(url, timeout=10) as response:
            story_ids = json.loads(response.read())[:limit]
        
        # 获取每个 story 的详情
        stories = []
        for story_id in story_ids:
            detail_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            try:
                with urllib.request.urlopen(detail_url, timeout=5) as response:
                    story = json.loads(response.read())
                    if story.get('type') == 'story' and story.get('url'):
                        stories.append({
                            'title': story.get('title'),
                            'url': story.get('url'),
                            'score': story.get('score', 0),
                            'time': story.get('time'),
                            'id': story_id
                        })
            except:
                continue
        
        return stories
    except Exception as e:
        print(f"获取 Hacker News 失败: {e}", file=sys.stderr)
        return []

def generate_post(stories, date=None):
    """生成文章"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    content = f"""# 技术热点日报 - {date}

> 自动生成

## 今日热点 ({len(stories)} 条)

"""
    
    for i, story in enumerate(stories, 1):
        content += f"""
### {i}. {story['title']}

**热度**: {story['score']} 点  
**链接**: [{story['url']}]({story['url']})

---

"""
    
    content += f"""
---
*本文由自动化内容生产者生成 | {datetime.now().strftime('%H:%M')}*
"""
    
    return content

def save_post(content, date=None):
    """保存文章"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    filename = f"{date}.md"
    filepath = POSTS_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def main():
    """主流程"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行...")
    
    # 加载配置
    config = load_config()
    print(f"配置已加载: {len(config['sources'])} 个信息源")
    
    # 获取 Hacker News 热点
    print("获取 Hacker News 热点...")
    stories = fetch_hacker_news_top_stories(limit=10)
    
    if not stories:
        print("未获取到热点数据，退出")
        return 1
    
    print(f"获取到 {len(stories)} 条热点")
    
    # 生成文章
    print("生成文章...")
    content = generate_post(stories)
    
    # 保存文章
    print("保存文章...")
    filepath = save_post(content)
    print(f"文章已保存到: {filepath}")
    
    # 记录元数据
    metadata = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
        "source": "hacker_news",
        "count": len(stories),
        "file": str(filepath)
    }
    
    meta_file = DATA_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 完成!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
