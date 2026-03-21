# 推送到 GitHub

## 方法1：通过 GitHub Web 界面创建仓库（推荐）

1. 访问 https://github.com/new
2. 仓库名称：`content-producer`
3. 描述：自动化内容生产者 - 定时抓取技术热点，生成日报和分析报告
4. 选择 Public
5. 勾选 "Add a README file"（因为已经有 README 了，可以不勾选）
6. 点击 "Create repository"

创建后，在终端执行：

```bash
cd /Users/malt/WorkBuddy/Claw/content-producer
git remote add origin https://github.com/YOUR_USERNAME/content-producer.git
git branch -M main
git push -u origin main
```

## 方法2：使用 GitHub CLI（需要先安装）

```bash
# 安装 GitHub CLI（如果还没安装）
# macOS:
# brew install gh

# 登录
gh auth login

# 创建仓库并推送
cd /Users/malt/WorkBuddy/Claw/content-producer
gh repo create content-producer --public --source=. --remote=origin --push
```

## 方法3：使用 GitHub API（需要 Personal Access Token）

```bash
# 需要先在 GitHub 设置中创建 Personal Access Token
# Settings -> Developer settings -> Personal access tokens -> Tokens (classic)

curl -X POST \
  -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d '{"name":"content-producer","description":"自动化内容生产者","public":true}'
```

---

**建议使用方法1，最简单直接。**
