# 🤖 自动化内容生产者

<div align="center">

**定时抓取技术热点，自动生成日报和分析报告**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

[✨ Star 这个项目支持我们](#-支持我们) | [📖 文档](#-使用指南) | [💡 功能特性](#-功能特性)

</div>

---

## ✨ 功能特性

- 🌐 **多源数据抓取**：Hacker News、GitHub Trending（持续扩展中）
- 📝 **自动内容生成**：每日技术热点日报、分析报告
- ⏰ **智能调度**：定时任务，无需人工干预
- 📊 **数据分析**：趋势分析、关键词提取（开发中）
- 🚀 **轻量高效**：Python 3.8+，零第三方依赖

## 📖 使用指南

### 快速开始

```bash
# 克隆仓库
git clone https://github.com/mindonai/content-producer.git
cd content-producer

# 安装（无需额外依赖，只需要 Python 3.8+）
# 直接运行即可

# 单次生成
python3 generator.py

# 启动定时调度器（每天凌晨2点自动运行）
./launcher.sh
```

### 项目结构

```
content-producer/
├── generator.py      # 主脚本（Hacker News 抓取）
├── scheduler.py      # 定时调度器
├── github_fetcher.py # GitHub Trending 抓取
├── analyzer.py       # 内容分析器
├── launcher.sh       # 启动脚本
├── posts/            # 生成的文章
├── data/             # 元数据
└── README.md         # 本文件
```

### 输出示例

生成的技术热点日报包含：
- Top 10 热门技术话题
- 每个话题的标题、链接、热度
- Markdown 格式，易于阅读和发布

## 🎯 路线图

- [ ] 完善 GitHub Trending 解析
- [ ] 添加更多数据源（技术博客、新闻网站）
- [ ] 增强 AI 分析功能（关键词提取、趋势分析）
- [ ] 自动发布到博客和社交媒体
- [ ] Web 界面和可视化

## 🌟 贡献

欢迎贡献代码、报告问题或提出新功能建议！

1. Fork 这个仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 📄 开源协议

本项目采用 MIT 协议 - 详见 [LICENSE](LICENSE) 文件

## 🙏 支持我们

如果这个项目对你有帮助，可以考虑：

- ⭐ 给这个项目加个 Star
- 💰 [成为 Sponsor](https://github.com/sponsors/mindonai)
- 🐛 报告 Bug 或提出功能建议
- 📢 分享给更多人

---

<div align="center">

Made with ❤️ by [Mindon](mailto:mindon@outlook.com)

</div>
