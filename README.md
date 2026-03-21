# 自动化内容生产者

## 功能
定时抓取网络热点资讯，自动生成文章并保存。

## 已实现
- ✅ Hacker News 热点抓取
- ✅ 自动生成 Markdown 文章
- ✅ 本地文件系统保存
- ✅ 定时调度器（每天凌晨2点自动运行）
- ✅ GitHub Trending 基础框架
- ✅ 内容分析器框架

## 项目结构
```
content-producer/
├── generator.py      # 主脚本（Hacker News 抓取）
├── scheduler.py      # 定时调度器
├── github_fetcher.py # GitHub Trending 抓取（框架）
├── analyzer.py       # 内容分析器（框架）
├── launcher.sh       # 启动脚本
├── config.json       # 配置文件（自动生成）
├── posts/            # 保存的文章
├── data/             # 元数据
└── scheduler.log     # 调度器日志
```

## 使用

### 单次运行
```bash
python3 generator.py
```

### 启动定时调度器
```bash
./launcher.sh
```

调度器会在每天凌晨2点自动运行内容生成。

## 输出示例

### 技术热点日报
每天生成 Hacker News 热点汇总，包含：
- Top 10 热门故事
- 每个故事的标题、链接、热度
- Markdown 格式，便于阅读和发布

## 下一步计划
- [ ] 完善 GitHub Trending 解析（HTML 解析）
- [ ] 添加更多数据源（技术博客、新闻网站）
- [ ] 增强 AI 分析功能（关键词提取、趋势分析）
- [ ] 添加自动发布功能（发布到博客、社交媒体）
- [ ] 探索商业化变现路径
