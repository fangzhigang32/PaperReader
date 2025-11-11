
# 📚 PaperReader

> **每日自动抓取 arXiv、IEEE Xplore、ACM Digital Library 三大数据库前一天最新的论文，经 LLM 智能筛选出与你研究领域高度相关的内容后，直接推送至指定邮箱，无需手动监控数据库，还支持本地调试运行，高效跟进学术动态！**

---

## ✨ 核心功能

- ⏰ **定时执行**：每天 UTC 上午 9 点（北京时间下午 5 点）自动触发  
- 🔍 **多库检索**：同步抓取 arXiv、IEEE Xplore、ACM Digital Library 三大数据库最新论文  
- 🧠 **精准筛选**：通过 LLM 智能判断论文与研究方向的相关性  
- 📧 **邮箱推送**：筛选后的优质论文自动发送至指定邮箱  
- 💻 **本地运行**：支持通过 `uv` 命令行本地调试运行  

---

## 📋 前置准备

1. 拥有 GitHub 账号，且能正常访问 GitHub Actions  
2. 准备 OpenAI / Ollama 等模型的 API 密钥  
3. 配置发送方邮箱（需开启 SMTP 服务并获取授权码）  
4. 明确接收方邮箱地址  
5. 本地环境已安装 `uv` （Python 包管理器 & 运行工具）  
6. 推荐使用 **Python 3.12**

---

## 🚀 快速使用

### 1. Fork 仓库

点击仓库右上角 **"Fork"** 按钮，将本仓库复制到你的 GitHub 账号下。

---

### 2. 配置 Repository Secrets（GitHub Actions 专用）

进入 Fork 后的仓库，路径如下：

> `Settings → Secrets and variables → Actions → New repository secret`

添加以下 **必填 Secrets**：

| Secret 名称       | 详细说明 |
|-------------------|-----------|
| `OPENAI_API_KEY`  | OpenAI API 密钥（或其他模型密钥） |
| `OPENAI_API_BASE` | API 基础地址 |
| `MODEL_PROVIDER`  | 模型提供商：`openai` / `ollama` / 其他 |
| `MODEL`           | 模型名称（如 `gpt-3.5-turbo`、`llama3`） |
| `SEARCH_TEXT`     | 检索关键词（空格分隔多个，推荐只用最小数的关键词） |
| `ARXIV_COUNT`     | arXiv 最大检索数量（建议 ≤ 100） |
| `CROSSREF_COUNT`  | IEEE/ACM 最大检索数量（建议 ≤ 100） |
| `SENDER_EMAIL`    | 发送方邮箱地址（如 `xxx@qq.com`） |
| `SENDER_PASS`     | 邮箱授权码（非登录密码） |
| `RECEIVER_EMAIL`  | 接收方邮箱地址 |
| `SMTP_SERVER`     | SMTP 服务器地址（默认 `smtp.qq.com`） |
| `SMTP_PORT`       | SMTP 端口号（默认 `465`） |

---

### 3. 运行 GitHub Action（自动定时执行）

- 🕒 **自动触发**：每天 UTC 上午 9 点（北京时间下午 5 点）自动运行  
- 🧪 **手动测试**：  
  进入仓库 → `Actions → 选择对应 workflow → Run workflow → 点击 Run workflow`

---

## 💻 本地运行（调试 / 手动触发）

### 1. 配置本地环境变量

将上述 Secrets 对应项设置为系统环境变量。

#### 🐧 Windows（PowerShell）

```powershell
$env:OPENAI_API_KEY="你的API密钥"
$env:OPENAI_API_BASE="你的API基础地址"
$env:MODEL_PROVIDER="openai"
$env:MODEL="gpt-3.5-turbo"
$env:SEARCH_TEXT="你的检索关键词"
$env:SEARCH_TEXT="你的检索关键词"
$env:ARXIV_COUNT=50
$env:CROSSREF_COUNT=50
$env:SENDER_EMAIL="xxx@xx.xx"
$env:SENDER_PASS="Authorization code"
$env:RECEIVER_EMAIL="xxx@xx.xx"
$env:SMTP_SERVER="smtp.qq.com"
$env:SMTP_PORT=465
```

#### 🐧 macOS / Linux（Bash）

```bash
export OPENAI_API_KEY="你的API密钥"
export OPENAI_API_BASE="你的API基础地址"
export MODEL_PROVIDER="openai"
export MODEL="gpt-3.5-turbo"
export SEARCH_TEXT="你的检索关键词"
export ARXIV_COUNT=50
export CROSSREF_COUNT=50
export SENDER_EMAIL="xxx@xx.xx"
export SENDER_PASS="Authorization code"
export RECEIVER_EMAIL="xxx@xx.xx"
export SMTP_SERVER="smtp.qq.com"
export SMTP_PORT=465
```

---

### 2. 安装依赖 & 运行程序

进入项目根目录后执行：

```bash
# 安装依赖（自动读取 pyproject.toml）
uv sync

# 运行主程序（执行 检索 → 筛选 → 推送 全流程）
uv run src/main.py
```

---

## 🎯 自定义研究方向筛选规则

论文相关性判断逻辑由 `src/selectRelevantPaper.py` 中的  
`llm_is_relevant(title, abstract)` 方法控制，主要通过 `user_template` 定义筛选标准。

打开 `src/selectRelevantPaper.py` 文件，修改如下部分：

```python
user_template = """
My research focuses on Electronic Design Automation (EDA) and Large Language Model (LLM)-assisted chip design.\n\nIt includes code generation, static code analysis, lint violation detection and repair, coding standard violations, and security vulnerabilities.\n\nPlease determine whether the following paper is related to or potentially useful for my research.\n\nIf the paper involves EDA, code generation, code analysis, program repair, code quality improvement, or automatic error detection,please answer "Yes". Otherwise, please answer "No".\n\nTitle: {title}\n\nAbstract: {abstract}
"""
```

修改完成后，可运行以下命令验证效果：

```bash
uv sync
uv run src/main.py
```

---

## ❌ 常见问题排查

### 1. 邮箱接收不到论文？

✅ 检查以下配置项：`SENDER_EMAIL`、`SENDER_PASS`、`SMTP_SERVER`、`SMTP_PORT`  
✅ 确认发送邮箱已开启 **SMTP 服务**：
- QQ 邮箱：设置 → 账户 → 开启 POP3/IMAP/SMTP
- Gmail：开启两步验证 → 创建应用专用密码
✅ 查看运行日志：
- 本地运行：直接查看终端输出  
- GitHub Action：`Actions → 对应运行记录 → 查看日志`

---

### 2. 检索不到相关论文？

✅ 优化 `SEARCH_TEXT`（可使用更具体或更宽泛的关键词）  
✅ 适当提高 `ARXIV_COUNT` / `CROSSREF_COUNT`（建议 ≤ 100）  
✅ 检查模型配置是否匹配：`MODEL_PROVIDER` 与 `MODEL` 一致  

---

### 3. GitHub Action 运行失败？

✅ 确认所有 Secrets 拼写正确、无空值  
✅ 验证 API 密钥有效性（OpenAI 需有余额）  
✅ 查看 Action 日志中的错误详情（如 `API key invalid`、`SMTP authentication failed`）

---

## ⚠️ 免责声明

- 本项目仅用于 **学术研究目的**，请遵守各数据库使用条款  
- 论文版权归原作者及出版机构所有，请勿用于商业用途  
- 请合理设置检索频率与数量，避免对数据库服务器造成不必要压力  

---



