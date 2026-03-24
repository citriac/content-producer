#!/usr/bin/env python3
"""
自动化内容生产者 V2 - 使用智能 API 客户端
整合 Hacker News + GitHub Trending，生成高质量技术日报
支持多端点降级、缓存和故障恢复
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
POSTS_DIR = PROJECT_ROOT / "posts"
CONFIG_FILE = PROJECT_ROOT / "config.json"

DATA_DIR.mkdir(exist_ok=True)
POSTS_DIR.mkdir(exist_ok=True)

# 导入智能 API 客户端
sys.path.insert(0, str(PROJECT_ROOT))
try:
    from api_client import get_client, APIType
    CLIENT_AVAILABLE = True
except ImportError:
    logger.warning("智能 API 客户端不可用，使用旧版生成器")
    CLIENT_AVAILABLE = False
    # 回退到旧版客户端
    import urllib.request
    import urllib.error


def load_config() -> Dict:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return {
        "sources": ["hn", "github"],
        "hn_limit": 15,
        "github_days": 7,
        "github_limit": 12,
        "output_format": "markdown",
        "use_cache": True,
        "enable_fallback": True,
        "generate_backup": True
    }


class ContentGeneratorV2:
    """内容生成器 V2"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or load_config()
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        
        if CLIENT_AVAILABLE:
            self.client = get_client()
            logger.info("使用智能 API 客户端")
        else:
            self.client = None
            logger.info("使用基础 HTTP 客户端")
    
    def fetch_hn_stories(self, limit: int = 15) -> Optional[List[Dict]]:
        """获取 Hacker News 热门故事"""
        logger.info(f"获取 Hacker News 热门故事 (limit={limit})...")
        
        if self.client:
            # 使用智能客户端
            try:
                # 先获取故事 ID 列表
                top_stories = self.client.get_top_hn_stories(limit * 2)  # 多取一些备用
                
                if not top_stories:
                    logger.error("获取 Hacker News 故事列表失败")
                    return None
                
                # 获取故事详情
                stories = []
                story_ids = top_stories[:limit * 2] if top_stories else []
                for story_id in story_ids:
                    if len(stories) >= limit:
                        break
                    
                    story = self.client.get_hn_item(story_id)
                    if story:
                        stories.append(story)
                
                logger.info(f"成功获取 {len(stories)} 个 Hacker News 故事")
                return stories
                
            except Exception as e:
                logger.error(f"获取 Hacker News 故事失败: {e}")
                return None
        else:
            # 回退到基础 HTTP 客户端
            return self._fetch_hn_stories_basic(limit)
    
    def _fetch_hn_stories_basic(self, limit: int = 15) -> Optional[List[Dict]]:
        """基础 HTTP 客户端获取 Hacker News 故事"""
        try:
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            with urllib.request.urlopen(url, timeout=15) as r:
                story_ids = json.loads(r.read())[:limit * 2]
            
            stories = []
            for sid in story_ids:
                if len(stories) >= limit:
                    break
                
                detail_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                try:
                    with urllib.request.urlopen(detail_url, timeout=10) as r:
                        story = json.loads(r.read())
                        if story and story.get("type") == "story":
                            stories.append(story)
                except Exception as e:
                    logger.warning(f"获取故事 {sid} 失败: {e}")
                    continue
            
            logger.info(f"基础客户端获取 {len(stories)} 个 Hacker News 故事")
            return stories
            
        except Exception as e:
            logger.error(f"基础客户端获取 Hacker News 失败: {e}")
            return None
    
    def fetch_github_repos(self, days: int = 7, limit: int = 12) -> Optional[List[Dict]]:
        """获取 GitHub 热门仓库"""
        logger.info(f"获取 GitHub {days} 天内热门仓库 (limit={limit})...")
        
        if self.client:
            # 使用智能客户端
            try:
                result = self.client.get_github_trending(days=days, limit=limit)
                
                if not result or "items" not in result:
                    logger.error("获取 GitHub 仓库失败")
                    return None
                
                repos = result["items"]
                logger.info(f"成功获取 {len(repos)} 个 GitHub 仓库")
                return repos
                
            except Exception as e:
                logger.error(f"获取 GitHub 仓库失败: {e}")
                return None
        else:
            # 回退到基础 HTTP 客户端
            return self._fetch_github_repos_basic(days, limit)
    
    def _fetch_github_repos_basic(self, days: int = 7, limit: int = 12) -> Optional[List[Dict]]:
        """基础 HTTP 客户端获取 GitHub 仓库"""
        try:
            from datetime import timedelta
            import urllib.parse
            
            # 构建查询参数
            since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            query = f"created:>{since_date}"
            
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": limit
            }
            
            url = f"https://api.github.com/search/repositories?{urllib.parse.urlencode(params)}"
            
            # 添加 User-Agent 头
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Clavis-ContentProducer/1.0",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            with urllib.request.urlopen(req, timeout=20) as r:
                result = json.loads(r.read())
            
            repos = result.get("items", [])
            logger.info(f"基础客户端获取 {len(repos)} 个 GitHub 仓库")
            return repos
            
        except Exception as e:
            logger.error(f"基础客户端获取 GitHub 仓库失败: {e}")
            return None
    
    def generate_markdown(self, hn_stories: List[Dict], github_repos: List[Dict]) -> str:
        """生成 Markdown 格式的日报"""
        date_str = self.date_str
        
        # 构建标题
        markdown = f"""# 技术热点日报 {date_str}

> 🤖 本日报由 **Clavis** 自动生成，数据来源：Hacker News + GitHub Trending
> 📅 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 今日概览

- **Hacker News 热门故事**: {len(hn_stories)} 篇
- **GitHub 热门仓库**: {len(github_repos)} 个
- **生成方式**: {'智能 API 客户端 (多端点降级)' if self.client else '基础 HTTP 客户端'}

"""
        
        # Hacker News 部分
        if hn_stories:
            markdown += "## 🗞️ Hacker News 热门讨论\n\n"
            markdown += "| 排名 | 标题 | 分数 | 评论 | 链接 |\n"
            markdown += "|------|------|------|------|------|\n"
            
            for i, story in enumerate(hn_stories[:15], 1):
                title = story.get("title", "No Title")
                score = story.get("score", 0)
                descendants = story.get("descendants", 0)
                url = story.get("url", f"https://news.ycombinator.com/item?id={story.get('id', '')}")
                
                # 简化标题显示
                if len(title) > 80:
                    title = title[:77] + "..."
                
                markdown += f"| {i} | {title} | {score} | {descendants} | [链接]({url}) |\n"
            
            markdown += "\n"
        
        # GitHub 部分
        if github_repos:
            markdown += "## ⭐ GitHub 热门新仓库\n\n"
            markdown += "| 仓库 | 描述 | 语言 | 星标 | 创建时间 |\n"
            markdown += "|------|------|------|------|----------|\n"
            
            for repo in github_repos[:12]:
                name = repo.get("name", "")
                full_name = repo.get("full_name", "")
                description = repo.get("description") or "No description"
                language = repo.get("language", "Unknown")
                stars = repo.get("stargazers_count", 0)
                created_at = repo.get("created_at", "")[:10]
                html_url = repo.get("html_url", "#")
                
                # 简化描述
                if len(description) > 100:
                    description = description[:97] + "..."
                
                markdown += f"| [{name}]({html_url}) | {description} | {language} | {stars} | {created_at} |\n"
            
            markdown += "\n"
        
        # 添加分析部分
        markdown += "## 🔍 趋势分析\n\n"
        
        if hn_stories and github_repos:
            # 简单的趋势分析
            markdown += "### 📈 今日技术热点\n"
            
            # 统计热门技术关键词
            tech_keywords = ["AI", "Rust", "Python", "TypeScript", "React", "Vue", 
                           "Docker", "Kubernetes", "LLM", "API"]
            
            keyword_counts = {}
            all_text = ""
            
            for story in hn_stories:
                title = story.get("title", "").lower()
                for keyword in tech_keywords:
                    if keyword.lower() in title:
                        keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            
            for repo in github_repos:
                description = (repo.get("description") or "").lower()
                language = repo.get("language", "")
                if language:
                    keyword_counts[language] = keyword_counts.get(language, 0) + 1
                
                for keyword in tech_keywords:
                    if keyword.lower() in description:
                        keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            
            # 显示热门关键词
            if keyword_counts:
                sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                markdown += "**热门技术关键词**:\n"
                for keyword, count in sorted_keywords:
                    markdown += f"- **{keyword}**: {count} 次提及\n"
            
            markdown += "\n"
        
        # 添加 API 状态信息
        if self.client:
            stats = self.client.get_stats()
            markdown += f"""## 🔧 系统状态

- **API 请求统计**:
  - 总请求数: {stats['request_stats']['total_requests']}
  - 成功请求: {stats['request_stats']['successful_requests']}
  - 缓存命中: {stats['request_stats']['cache_hits']}
  - 降级使用: {stats['request_stats']['fallback_used']}

- **数据新鲜度**: 实时获取
- **服务可靠性**: 多端点降级保障

"""
        
        # 结尾
        markdown += f"""---

## 📝 关于本日报

**Clavis** 是一个 AI 自动化内容生产者，专注于技术热点分析和内容生成。

### 技术栈
- **数据来源**: Hacker News API + GitHub REST API
- **处理引擎**: Python + 智能 API 客户端
- **发布渠道**: 自动部署到 Cloudflare Pages、Vercel、GitHub Pages
- **内容分发**: 支持掘金、知乎、Reddit、Twitter 等多平台

### 开源项目
- [content-producer](https://github.com/citriac/content-producer) - 内容生产者源码
- [clavis-hn-api](https://github.com/citriac/clavis-hn-api) - Hacker News API 服务

---

*日报 ID: {date_str.replace('-', '')}*
*生成批次: {datetime.now().strftime('%Y%m%d%H%M%S')}*
"""
        
        return markdown
    
    def save_output(self, markdown_content: str):
        """保存输出文件"""
        # 保存 Markdown 文件
        md_file = POSTS_DIR / f"{self.date_str}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        logger.info(f"Markdown 文件已保存: {md_file}")
        
        # 保存 JSON 数据文件（供网站使用）
        json_file = DATA_DIR / f"{self.date_str}.json"
        output_data = {
            "date": self.date_str,
            "generated_at": datetime.now().isoformat(),
            "format": "markdown",
            "file_path": str(md_file.relative_to(PROJECT_ROOT)),
            "client_stats": self.client.get_stats() if self.client else None
        }
        
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON 数据文件已保存: {json_file}")
        
        # 如果配置了生成备份，保存到备份目录
        if self.config.get("generate_backup", True):
            backup_dir = PROJECT_ROOT / "backup" / self.date_str
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_md = backup_dir / f"daily_{self.date_str}.md"
            with open(backup_md, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            
            backup_json = backup_dir / f"metadata_{self.date_str}.json"
            with open(backup_json, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"备份文件已保存到: {backup_dir}")
    
    def generate(self):
        """主生成函数"""
        logger.info(f"开始生成 {self.date_str} 技术热点日报")
        
        # 获取配置
        hn_limit = self.config.get("hn_limit", 15)
        github_days = self.config.get("github_days", 7)
        github_limit = self.config.get("github_limit", 12)
        
        # 获取数据
        hn_stories = self.fetch_hn_stories(hn_limit)
        github_repos = self.fetch_github_repos(github_days, github_limit)
        
        # 检查数据获取情况
        if not hn_stories and not github_repos:
            logger.error("无法获取任何数据，日报生成失败")
            return False
        
        if not hn_stories:
            logger.warning("Hacker News 数据获取失败，仅使用 GitHub 数据")
            hn_stories = []
        
        if not github_repos:
            logger.warning("GitHub 数据获取失败，仅使用 Hacker News 数据")
            github_repos = []
        
        # 生成 Markdown
        markdown = self.generate_markdown(hn_stories, github_repos)
        
        # 保存输出
        self.save_output(markdown)
        
        # 显示统计信息
        if self.client:
            stats = self.client.get_stats()
            logger.info("生成完成，客户端统计:")
            logger.info(f"  总请求数: {stats['request_stats']['total_requests']}")
            logger.info(f"  成功请求: {stats['request_stats']['successful_requests']}")
            logger.info(f"  缓存命中: {stats['request_stats']['cache_hits']}")
            logger.info(f"  降级使用: {stats['request_stats']['fallback_used']}")
        else:
            logger.info("生成完成 (使用基础客户端)")
        
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="技术热点日报生成器 V2")
    parser.add_argument("--date", help="指定日期 (格式: YYYY-MM-DD)，默认为今天")
    parser.add_argument("--config", default="config.json", help="配置文件路径")
    parser.add_argument("--no-cache", action="store_true", help="禁用缓存")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 加载配置
    config = load_config()
    if args.config != "config.json":
        config_path = Path(args.config)
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config.update(json.load(f))
    
    if args.no_cache:
        config["use_cache"] = False
    
    # 创建生成器
    generator = ContentGeneratorV2(config)
    
    if args.date:
        # 这里可以扩展支持指定日期，目前先使用当前日期
        logger.info(f"注意: 指定日期功能暂未实现，使用当前日期")
    
    # 生成日报
    success = generator.generate()
    
    if success:
        print(f"\n✅ {generator.date_str} 技术热点日报生成完成!")
        print(f"📁 文件位置: posts/{generator.date_str}.md")
        print(f"📊 数据文件: data/{generator.date_str}.json")
        
        if CLIENT_AVAILABLE:
            client = get_client()
            stats = client.get_stats()
            print(f"📈 API 统计: {stats['request_stats']['successful_requests']}/{stats['request_stats']['total_requests']} 成功")
        
        sys.exit(0)
    else:
        print("\n❌ 日报生成失败")
        sys.exit(1)


if __name__ == "__main__":
    main()