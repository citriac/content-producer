#!/usr/bin/env python3
"""
日报内容分发脚本
基于 content-distribution 技能，将技术热点日报发布到多个平台
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent


class DailyReportDistributor:
    """日报分发器"""
    
    def __init__(self, date_str: Optional[str] = None):
        """
        初始化分发器
        
        Args:
            date_str: 日期字符串，格式如"2026-03-22"
        """
        self.date_str = date_str or datetime.now().strftime("%Y-%m-%d")
        self.report_path = PROJECT_ROOT / "posts" / f"{self.date_str}.md"
        self.json_path = PROJECT_ROOT / "docs" / "data" / f"{self.date_str}.json"
        
    def load_report(self) -> Dict:
        """加载日报数据"""
        if not self.report_path.exists():
            raise FileNotFoundError(f"日报文件不存在: {self.report_path}")
        
        # 读取Markdown内容
        with open(self.report_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # 读取JSON数据（如果有）
        json_data = {}
        if self.json_path.exists():
            with open(self.json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        
        return {
            "markdown": markdown_content,
            "json": json_data,
            "date": self.date_str,
            "title": f"技术热点日报 {self.date_str}",
            "source_url": f"https://citriac.github.io/content-producer/#/daily/{self.date_str}"
        }
    
    def optimize_for_platform(self, content: Dict, platform: str) -> Dict:
        """为特定平台优化内容"""
        base_content = content.copy()
        
        if platform == "juejin":
            # 掘金：实战教程风格
            return self._optimize_for_juejin(base_content)
        elif platform == "zhihu":
            # 知乎：深度分析风格
            return self._optimize_for_zhihu(base_content)
        elif platform == "reddit":
            # Reddit：简洁讨论风格
            return self._optimize_for_reddit(base_content)
        elif platform == "twitter":
            # Twitter：线程风格
            return self._optimize_for_twitter(base_content)
        else:
            # 默认：通用格式
            return base_content
    
    def _optimize_for_juejin(self, content: Dict) -> Dict:
        """为掘金优化"""
        markdown = content["markdown"]
        json_data = content["json"]
        
        # 提取关键信息
        summary = f"📊 {content['date']} 技术热点日报更新！\n\n"
        
        if json_data.get("trends") and "insights" in json_data["trends"]:
            insights = json_data["trends"]["insights"]
            summary += "今日趋势速览:\n"
            for insight in insights[:3]:  # 取前3个洞察
                summary += f"• {insight}\n"
            summary += "\n"
        
        if json_data.get("top_projects"):
            projects = json_data["top_projects"][:2]  # 取前2个项目
            summary += "热门开源项目:\n"
            for project in projects:
                name = project.get("name", "")
                url = project.get("html_url", "")
                summary += f"• [{name}]({url})\n"
        
        # 构建完整内容
        optimized_markdown = f"""# 技术热点日报 {content['date']}

## 📊 今日概览
这是我自动生成的技术热点日报，涵盖GitHub热门项目和Hacker News技术讨论。

{summary}

## 🔍 详细内容
{markdown}

## 🌐 在线阅读
[完整日报在此]({content['source_url']}) 包含所有项目和趋势的详细分析。

## 📈 自动化流程
这份日报由 [Clavis](https://github.com/citriac) 自动生成，使用Python从GitHub和Hacker News API获取数据，通过AI分析生成趋势洞察。

---

**标签**: #技术日报 #GitHub趋势 #开源项目 #AI分析 #自动化
**作者**: Clavis (AI自动化内容生产者)
"""
        
        content["markdown"] = optimized_markdown
        content["tags"] = ["技术日报", "GitHub趋势", "开源项目", "AI分析", "自动化"]
        return content
    
    def _optimize_for_zhihu(self, content: Dict) -> Dict:
        """为知乎优化"""
        markdown = content["markdown"]
        json_data = content["json"]
        
        # 知乎适合深度分析
        analysis = "## 🤖 技术趋势分析\n\n"
        
        if json_data.get("trends") and "insights" in json_data["trends"]:
            insights = json_data["trends"]["insights"]
            analysis += "基于今日数据，我观察到以下技术趋势:\n\n"
            for i, insight in enumerate(insights, 1):
                analysis += f"{i}. {insight}\n\n"
        
        if json_data.get("recommendations"):
            recs = json_data["recommendations"]
            analysis += "## 💡 开发者建议\n\n"
            for rec in recs:
                analysis += f"### {rec.get('title', '')}\n"
                analysis += f"{rec.get('description', '')}\n\n"
        
        optimized_markdown = f"""# 2026年{content['date'][5:]} 技术热点分析与趋势洞察

## 引言
本文分析{content['date']}的技术热点，基于GitHub热门项目和Hacker News讨论，提供深度技术趋势洞察。

{analysis}

## 数据来源
1. **GitHub API**: 获取过去24小时热门新仓库
2. **Hacker News API**: 获取技术社区讨论热点
3. **自动化分析**: 使用Python进行关键词提取和趋势识别

## 方法论
1. **数据收集**: 实时获取原始技术数据
2. **趋势分析**: 识别重复出现的模式和技术
3. **价值提取**: 从噪声中提取有意义的信号
4. **内容生成**: 将分析结果转化为可读报告

## 完整报告
[在线日报链接]({content['source_url']}) 包含所有详细数据和项目信息。

---

*本文由AI自动化内容生产者Clavis生成，数据来源公开透明。*
"""
        
        content["markdown"] = optimized_markdown
        content["tags"] = ["技术趋势", "数据分析", "开源生态", "AI应用", "开发者工具"]
        return content
    
    def _optimize_for_reddit(self, content: Dict) -> Dict:
        """为Reddit优化"""
        markdown = content["markdown"]
        json_data = content["json"]
        
        # Reddit喜欢简洁和讨论
        highlights = "## Highlights of the Day\n\n"
        
        if json_data.get("hn_stories"):
            stories = json_data["hn_stories"][:3]
            highlights += "**Top Hacker News Stories**:\n\n"
            for story in stories:
                title = story.get("title", "")
                url = story.get("url", "")
                highlights += f"- [{title}]({url})\n"
            highlights += "\n"
        
        if json_data.get("top_projects"):
            projects = json_data["top_projects"][:3]
            highlights += "**Top GitHub Projects**:\n\n"
            for project in projects:
                name = project.get("name", "")
                url = project.get("html_url", "")
                stars = project.get("stargazers_count", 0)
                highlights += f"- [{name}]({url}) ({stars} stars)\n"
        
        optimized_markdown = f"""# Daily Tech Digest {content['date']}

{highlights}

## About This Report
This is an automated daily tech digest generated by [Clavis](https://github.com/citriac), an AI content producer.

## How It Works
1. **Data Collection**: Fetches data from GitHub and Hacker News APIs
2. **Trend Analysis**: Identifies patterns and emerging technologies
3. **Content Generation**: Creates readable summaries and insights

## Full Report
[Complete daily report here]({content['source_url']})

## Discussion Questions
- What technologies are you most excited about right now?
- Have you found any interesting open-source projects recently?
- How do you stay updated with tech trends?

---
*Generated automatically, data from public APIs.*
"""
        
        content["markdown"] = optimized_markdown
        content["tags"] = ["tech", "programming", "opensource", "github", "hackernews"]
        return content
    
    def _optimize_for_twitter(self, content: Dict) -> Dict:
        """为Twitter优化"""
        json_data = content["json"]
        
        # Twitter线程格式
        thread = []
        
        # 第一条：标题
        thread.append(f"🚀 Tech Digest {content['date']} is ready!\n\nA daily automated report of GitHub trends and Hacker News discussions.\n\n{content['source_url']}")
        
        # 第二条：趋势速览
        if json_data.get("trends") and "insights" in json_data["trends"]:
            insights = json_data["trends"]["insights"]
            trend_text = "📈 Today's Trends:\n"
            for i, insight in enumerate(insights[:2], 1):
                desc = insight[:80]
                trend_text += f"{i}. {desc}\n"
            thread.append(trend_text)
        
        # 第三条：热门项目
        if json_data.get("top_projects"):
            projects = json_data["top_projects"][:2]
            project_text = "⭐ Top Projects:\n"
            for i, project in enumerate(projects, 1):
                name = project.get("name", "")
                url = project.get("html_url", "")
                stars = project.get("stargazers_count", 0)
                project_text += f"{i}. {name} ({stars}★)\n{url}\n"
            thread.append(project_text)
        
        # 第四条：自动化说明
        thread.append("🤖 This thread is auto-generated by Clavis, an AI content producer.\n\nTech: Python + GitHub API + HN API + AI analysis\n\n#Tech #Programming #OpenSource #AI")
        
        content["twitter_thread"] = thread
        return content
    
    def create_distribution_plan(self) -> Dict:
        """创建分发计划"""
        content = self.load_report()
        
        plan = {
            "date": self.date_str,
            "source_report": content["source_url"],
            "platforms": {
                "juejin": {
                    "enabled": True,
                    "content": self.optimize_for_platform(content, "juejin"),
                    "best_time": "19:00 CST",
                    "auto_publish": False,  # 需要API密钥
                    "tags": ["技术日报", "GitHub趋势", "开源项目", "AI分析", "自动化"]
                },
                "zhihu": {
                    "enabled": True,
                    "content": self.optimize_for_platform(content, "zhihu"),
                    "best_time": "20:00 CST",
                    "auto_publish": False,  # 需要API密钥
                    "tags": ["技术趋势", "数据分析", "开源生态", "AI应用", "开发者工具"]
                },
                "reddit": {
                    "enabled": True,
                    "content": self.optimize_for_platform(content, "reddit"),
                    "subreddit": "r/programming",
                    "best_time": "06:00 PST",
                    "auto_publish": False,  # 需要认证
                    "flair": "Showcase"
                },
                "twitter": {
                    "enabled": True,
                    "content": self.optimize_for_platform(content, "twitter"),
                    "best_time": "09:00 Local",
                    "auto_publish": False,  # 需要API密钥
                    "hashtags": ["#Tech", "#Programming", "#OpenSource", "#AI"]
                }
            },
            "preview_files": [
                f"distribute/preview_{self.date_str}_juejin.md",
                f"distribute/preview_{self.date_str}_zhihu.md",
                f"distribute/preview_{self.date_str}_reddit.md",
                f"distribute/preview_{self.date_str}_twitter.txt"
            ]
        }
        
        return plan
    
    def generate_previews(self, plan: Dict):
        """生成预览文件"""
        preview_dir = PROJECT_ROOT / "distribute"
        preview_dir.mkdir(exist_ok=True)
        
        date_str = plan["date"]
        
        for platform, config in plan["platforms"].items():
            if not config["enabled"]:
                continue
            
            content = config["content"]
            
            if platform == "twitter":
                # Twitter线程保存为文本文件
                thread = content.get("twitter_thread", [])
                if thread:
                    filename = preview_dir / f"preview_{date_str}_twitter.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"Twitter Thread Preview for {date_str}\n")
                        f.write("=" * 50 + "\n\n")
                        for i, tweet in enumerate(thread, 1):
                            f.write(f"Tweet {i}:\n")
                            f.write(tweet + "\n")
                            f.write("-" * 30 + "\n\n")
                    logger.info(f"生成Twitter预览: {filename}")
            else:
                # 其他平台保存为Markdown
                filename = preview_dir / f"preview_{date_str}_{platform}.md"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"# {platform.upper()} Preview for {date_str}\n\n")
                    f.write(f"**最佳发布时间**: {config.get('best_time', 'N/A')}\n")
                    f.write(f"**标签**: {', '.join(config.get('tags', []))}\n\n")
                    f.write("---\n\n")
                    f.write(content.get("markdown", ""))
                logger.info(f"生成{platform}预览: {filename}")
    
    def create_summary_report(self, plan: Dict) -> str:
        """创建分发摘要报告"""
        report = f"""# 内容分发计划 - {plan['date']}

## 概览
- **报告日期**: {plan['date']}
- **源报告**: {plan['source_report']}
- **目标平台**: {len([p for p in plan['platforms'].values() if p['enabled']])} 个
- **状态**: 预览已生成，等待手动发布

## 平台详情
"""
        
        for platform, config in plan["platforms"].items():
            if not config["enabled"]:
                continue
            
            report += f"\n### {platform.upper()}\n"
            report += f"- **状态**: {'✅ 已启用' if config['enabled'] else '❌ 禁用'}\n"
            report += f"- **最佳时间**: {config.get('best_time', 'N/A')}\n"
            report += f"- **自动发布**: {'✅ 是' if config.get('auto_publish') else '❌ 否 (需要API密钥)'}\n"
            
            if config.get('tags'):
                report += f"- **标签**: {', '.join(config['tags'])}\n"
            
            if config.get('subreddit'):
                report += f"- **Subreddit**: {config['subreddit']}\n"
            
            report += f"- **预览文件**: `distribute/preview_{plan['date']}_{platform}.md`\n"
        
        report += f"""
## 下一步行动

### 立即行动
1. 查看生成的预览文件
2. 确认内容质量和格式
3. 手动发布到各平台（需要API密钥）

### 自动化设置（可选）
如需完全自动化，需要：
1. 申请各平台API密钥
2. 配置环境变量
3. 集成到GitHub Actions

### 监控建议
- 跟踪各平台互动数据
- 收集用户反馈
- 优化发布时间和内容格式

---
*基于 content-distribution 技能生成*
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return report


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="技术日报分发工具")
    parser.add_argument("--date", help="日期 (格式: YYYY-MM-DD), 默认为今天")
    parser.add_argument("--preview-only", action="store_true", help="仅生成预览，不创建报告")
    parser.add_argument("--output", default="distribute_summary.md", help="报告输出文件")
    
    args = parser.parse_args()
    
    try:
        # 初始化分发器
        distributor = DailyReportDistributor(args.date)
        
        # 创建分发计划
        logger.info(f"创建 {distributor.date_str} 的分发计划...")
        plan = distributor.create_distribution_plan()
        
        # 生成预览文件
        logger.info("生成各平台预览文件...")
        distributor.generate_previews(plan)
        
        if not args.preview_only:
            # 生成摘要报告
            logger.info("生成分发摘要报告...")
            summary = distributor.create_summary_report(plan)
            
            # 保存报告
            output_path = PROJECT_ROOT / args.output
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            logger.info(f"✅ 完成！预览文件和报告已生成")
            logger.info(f"📁 预览文件位置: distribute/")
            logger.info(f"📋 摘要报告: {args.output}")
            logger.info(f"🌐 源报告: {plan['source_report']}")
            
            # 打印简短摘要
            print("\n" + "="*60)
            print(f"📅 日报分发计划: {plan['date']}")
            print("="*60)
            enabled_count = len([p for p in plan['platforms'].values() if p['enabled']])
            print(f"📤 目标平台: {enabled_count} 个")
            print(f"📁 预览文件: {len(plan['preview_files'])} 个")
            print(f"📋 报告文件: {args.output}")
            print("="*60)
            print("下一步: 查看预览文件，确认后手动发布到各平台")
        else:
            logger.info("✅ 预览文件已生成到 distribute/ 目录")
            
    except Exception as e:
        logger.error(f"分发失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()