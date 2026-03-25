# content-producer

<div align="center">

**Automated daily tech digest: Hacker News + GitHub Trending → Markdown + web, every morning at 7am.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![No dependencies](https://img.shields.io/badge/dependencies-none-green.svg)](requirements.txt)

[📖 Read the Article](https://citriac.github.io/how-i-built-daily-tech-digest.html) · [🌐 Live Output](https://citriac.github.io/daily.html) · [🚀 Get the Kit — $15](https://citriac.gumroad.com/l/daily-tech-digest-automation-kit) · [❤ Sponsor](https://github.com/sponsors/citriac)

</div>

---

A Python pipeline that runs daily (no external dependencies, no API keys required) and produces:

- A curated Markdown digest of the top 15 HN stories + 12 trending GitHub repos
- A trend analysis JSON (dominant topics, hot categories, keyword frequencies)
- Updated GitHub Pages website

**No database. No framework. No dependencies outside stdlib.**

## How It Works

```
07:00 trigger
    │
    ▼
generator.py      ←── HN Firebase API + GitHub Search API
    │   writes: posts/YYYY-MM-DD.md
    │           data/hn-stories-*.json, data/github-trending-*.json
    ▼
analyzer.py       ←── reads today's data/*.json
    │   writes: data/analysis-YYYY-MM-DD.json
    ▼
publish_to_github_pages.py
        git add + commit + push → citriac.github.io updated ✓
```

## Quick Start

```bash
git clone https://github.com/citriac/content-producer.git
cd content-producer

# Generate today's digest
python3 generator.py

# Run trend analysis
python3 analyzer.py

# Publish to GitHub Pages (optional)
python3 publish_to_github_pages.py
```

Requires Python 3.8+. Zero external dependencies.

## Output Example

**`posts/2026-03-23.md`** (excerpt):

```markdown
# Tech Digest | 2026-03-23

> Auto-generated · 2026-03-23 07:07

## 📊 Today's Trends

**Hot topics**: Security  ·  AI/LLM  ·  Infrastructure
**Keywords**: `cloudflare`  `security`  `windows`  `agent`

## 🔥 Hacker News Top Stories

| # | Title | Score | Comments |
|---|-------|-------|----------|
| 1 | [Cloudflare flags archive.today](https://...) | ⬆ 354 | 💬 257 |
| 2 | [Windows native app dev is a mess](https://...) | ⬆ 295 | 💬 322 |
...
```

**`data/analysis-2026-03-23.json`** (excerpt):

```json
{
  "hn": {
    "avg_score": 130.1,
    "hot_categories": [["Security", 8], ["AI/LLM", 6]],
    "top_keywords": [["cloudflare", 4], ["security", 3]]
  },
  "github": {
    "top_languages": [["Python", 4], ["TypeScript", 3]],
    "top_repos": [{"name": "HKUDS/ClawTeam", "stars": 2793}]
  }
}
```

## Project Structure

```
content-producer/
├── generator.py              # Main pipeline: fetch HN + GitHub, generate digest
├── analyzer.py               # Trend analysis: keywords, categories, insights
├── build_site.py             # Prepare data files for GitHub Pages
├── publish_to_github_pages.py # Copy data + git push to pages repo
├── config.json               # Configuration (sources, limits, etc.)
├── posts/                    # Markdown digests (one per day)
├── data/                     # Raw JSON: HN stories, GitHub repos, analysis
└── docs/                     # GitHub Pages data output
```

## Scheduling

**Cron (simplest):**
```bash
0 7 * * * cd /path/to/content-producer && \
  python3 generator.py && \
  python3 analyzer.py && \
  python3 publish_to_github_pages.py && \
  git add posts/ && \
  git commit -m "auto: daily report $(date +%Y-%m-%d)" && \
  git push
```

**GitHub Actions:** See `.github/workflows/` for a ready-to-use workflow.

## Implementation Notes

- **HN data**: Uses the [official Firebase API](https://github.com/HackerNews/API) — no auth, no rate limits for occasional use
- **GitHub trending**: GitHub Search API with `created:>DATE&sort=stars` approximates the trending page
- **Trend analysis**: Keyword frequency + hand-crafted category classifier (no LLM required)
- **Publishing**: Plain `git push` to a separate GitHub Pages repo

Full technical walkthrough: [How I Built a Daily Tech Digest That Runs Itself](https://citriac.github.io/how-i-built-daily-tech-digest.html)

## Live Output

👉 **https://citriac.github.io/daily.html** — updated daily

---

<div align="center">

Built by [Clavis](https://github.com/citriac) · MIT License

**Want a pre-packaged, ready-to-deploy version?**  
[🚀 Daily Tech Digest Automation Kit — $15](https://citriac.gumroad.com/l/daily-tech-digest-automation-kit)  
Everything bundled with setup instructions, GitHub Actions workflow, and config. Deploy in 30 minutes.

---

If this is useful, consider ⭐ starring or [sponsoring](https://github.com/sponsors/citriac)

</div>
