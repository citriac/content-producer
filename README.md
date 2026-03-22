# 技术热点日报 · Clavis Content Producer

<div align="center">

**每天 07:00 自动抓取 Hacker News + GitHub Trending，生成技术日报**

[![Daily Pipeline](https://github.com/citriac/content-producer/actions/workflows/daily-generator.yml/badge.svg)](https://github.com/citriac/content-producer/actions/workflows/daily-generator.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

[🌐 在线阅读](https://citriac.github.io/content-producer) · [📡 API 服务](https://clavis-hn-api.citriac.deno.net) · [❤ 赞助](https://github.com/sponsors/citriac)

</div>

---

## 功能

- 🔥 **Hacker News 热点**：Top 15，按热度排序，带评论数
- 🚀 **GitHub Trending**：过去 7 天最热新项目，多语言覆盖
- 📊 **趋势分析**：自动提取技术领域热点（AI/LLM、Rust、安全等）
- 🌐 **在线展示站**：GitHub Pages，每日自动更新
- ⚡ **零干预运行**：GitHub Actions 全自动，不依赖本地机器

## 在线阅读

👉 **https://citriac.github.io/content-producer**

## API

所有数据通过 **[Clavis Tech API](https://clavis-hn-api.citriac.deno.net)** 对外开放：

```bash
# 今日摘要（HN + GitHub）
curl https://clavis-hn-api.citriac.deno.net/daily

# HN 热点
curl "https://clavis-hn-api.citriac.deno.net/hn/top?limit=10"

# GitHub 近期热门（按语言筛选）
curl "https://clavis-hn-api.citriac.deno.net/gh/trending?language=python"
```

## 本地运行

```bash
git clone https://github.com/citriac/content-producer.git
cd content-producer

# 生成今日日报
python3 generator.py

# 分析趋势
python3 analyzer.py

# 构建展示站
python3 build_site.py
```

无需额外依赖，Python 3.8+ 即可运行。

## 项目结构

```
content-producer/
├── generator.py       # 主生成器（HN + GitHub 双源）
├── analyzer.py        # 趋势分析器（关键词、领域分类）
├── github_fetcher.py  # GitHub Search API 抓取
├── build_site.py      # 站点构建器
├── docs/              # GitHub Pages 站点
│   ├── index.html     # 交互式日报阅读器
│   └── data/          # 每日 JSON 数据
├── posts/             # Markdown 格式日报
├── data/              # 原始数据（HN/GitHub JSON）
└── .github/workflows/ # 全自动定时任务
```

## 支持项目

如果这份日报对你有帮助：

- ⭐ **Star** 这个仓库
- 💰 [**赞助**](https://github.com/sponsors/citriac)——资助更好的基础设施和模型
- 📢 分享给感兴趣的朋友

---

<div align="center">

由 [Clavis](https://github.com/citriac) 驱动 · MIT License

</div>
