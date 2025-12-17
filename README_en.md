# 📚 PaperReader

> **Automatically fetches the latest papers from arXiv, IEEE Xplore, and ACM Digital Library published on the previous day. Using an LLM-based intelligent filter, it identifies papers highly relevant to your research field and delivers them directly to your inbox — no need to manually monitor databases. Also supports local debugging via `uv`, enabling efficient academic tracking!**

---

## ✨ Core Features

- ⏰ **Scheduled Execution**: Automatically runs every day at **9:00 AM UTC** (Beijing Time 5:00 PM)  
- 🔍 **Multi-Database Search**: Fetches the newest papers from arXiv, IEEE Xplore, and ACM Digital Library  
- 🧠 **Intelligent Filtering**: Uses LLM to determine the paper's relevance to your research direction  
- 📧 **Email Delivery**: Sends the curated papers directly to your inbox  
- 💻 **Local Execution**: Supports local debugging and manual runs via the `uv` CLI tool  

---

## 📋 Prerequisites

1. A GitHub account with access to **GitHub Actions**  
2. An **API key** for OpenAI / Ollama / other model providers  
3. A **sender email** with **SMTP service enabled** and its **authorization code**  
4. A **receiver email address**  
5. The **`uv`** tool installed locally (Python package manager & runtime)  
6. Recommended environment: **Python 3.12**  

---

## 🚀 Quick Start

### 1. Fork the Repository

Click the **"Fork"** button at the top-right corner of the repository to copy it to your GitHub account.

---

### 2. Configure Repository Secrets (for GitHub Actions)

Go to your forked repository:

> `Settings → Secrets and variables → Actions → New repository secret`

Add the following **required Secrets**:

| Secret Name       | Description |
|-------------------|-------------|
| `OPENAI_API_KEY`  | OpenAI API key (or another model key) |
| `OPENAI_API_BASE` | Base URL for API requests |
| `MODEL_PROVIDER`  | Model provider: `openai` / `ollama` / others |
| `MODEL`           | Model name (e.g., `gpt-3.5-turbo`, `llama3`) |
| `SEARCH_TEXT`     | Search keywords (space-separated; keep concise) |
| `ARXIV_COUNT`     | Max number of arXiv papers (≤ 100 recommended) |
| `CROSSREF_COUNT`  | Max number of IEEE/ACM papers (≤ 100 recommended) |
| `SENDER_EMAIL`    | Sender email address (e.g., `xxx@qq.com`) |
| `SENDER_PASS`     | Email authorization code (not login password) |
| `RECEIVER_EMAIL`  | Receiver email address |
| `SMTP_SERVER`     | SMTP server address (default: `smtp.qq.com`) |
| `SMTP_PORT`       | SMTP port (default: `465`) |
| `BROAD_FIELD`     | Your broad research field |
| `SPECIFIC_FIELD`  | Your specific research fields (comma-separated) |

---

### 3. Run GitHub Action (Automatic or Manual)

- 🕒 **Automatic Trigger**: Runs daily at 9:00 AM UTC (Beijing 5:00 PM)  
- 🧪 **Manual Test**:  
  Go to `Actions → Select workflow → Run workflow → Click "Run workflow"`

---

## 💻 Local Execution (Debug / Manual Run)

### 1. Configure Environment Variables

Set the same variables locally as you did in GitHub Secrets.

#### 🐧 Windows (PowerShell)

```powershell
$env:OPENAI_API_KEY="your_api_key"
$env:OPENAI_API_BASE="your_api_base"
$env:MODEL_PROVIDER="openai"
$env:MODEL="gpt-3.5-turbo"
$env:SEARCH_TEXT="your_keywords"
$env:ARXIV_COUNT=50
$env:CROSSREF_COUNT=50
$env:SENDER_EMAIL="xxx@xx.xx"
$env:SENDER_PASS="authorization_code"
$env:RECEIVER_EMAIL="xxx@xx.xx"
$env:SMTP_SERVER="smtp.qq.com"
$env:SMTP_PORT=465
$env:BROAD_FIELD="your_broad_research_field"
$env:SPECIFIC_FIELD="your_specific_research_fields"
```

#### 🐧 macOS / Linux (Bash)

```bash
export OPENAI_API_KEY="your_api_key"
export OPENAI_API_BASE="your_api_base"
export MODEL_PROVIDER="openai"
export MODEL="gpt-3.5-turbo"
export SEARCH_TEXT="your_keywords"
export ARXIV_COUNT=50
export CROSSREF_COUNT=50
export SENDER_EMAIL="xxx@xx.xx"
export SENDER_PASS="authorization_code"
export RECEIVER_EMAIL="xxx@xx.xx"
export SMTP_SERVER="smtp.qq.com"
export SMTP_PORT=465
export BROAD_FIELD="your_broad_research_field"
export SPECIFIC_FIELD="your_specific_research_fields"
```

---

### 2. Install Dependencies & Run

In the project root directory:

```bash
# Install dependencies (auto reads pyproject.toml)
uv sync

# Run the full workflow (Fetch → Filter → Send)
uv run src/main.py
```

---

## 🎯 Customize Research Relevance Rules

Paper relevance is configured via environment variables `BROAD_FIELD` and `SPECIFIC_FIELD` — no code modification required.

### Configuration

| Environment Variable | Description | Example |
|---------------------|-------------|---------|
| `BROAD_FIELD` | Your broad research field | `AI for Electronic Design Automation (EDA)` |
| `SPECIFIC_FIELD` | Your specific research subfields (comma-separated) | `code generation,static code analysis,program repair` |

### Filtering Logic

The LLM evaluates paper relevance based on the following criteria:

1. **Core Problem Match**: Whether the paper's research question falls within your specific subfield
2. **Methods & Techniques**: Whether the paper's approach aligns with your research direction
3. **Main Contributions**: Whether the paper's core contributions have direct value for your research

> ⚠️ **Note**: Papers that are only related at the broad-field level but have weak connections to your specific subfield will be marked as "not relevant" to ensure filtering precision.

### Verify Configuration

After configuration, test locally with:

```bash
uv sync
uv run src/main.py
```

---

## ❌ Troubleshooting

### 1. Email Not Received?

✅ Check the following: `SENDER_EMAIL`, `SENDER_PASS`, `SMTP_SERVER`, `SMTP_PORT`  
✅ Ensure SMTP service is enabled:  
- QQ Mail: Settings → Account → Enable POP3/IMAP/SMTP  
- Gmail: Enable two-step verification → Create app-specific password

✅ Check logs:  
- Local: Terminal output  
- GitHub Actions: `Actions → Workflow run → View logs`

---

### 2. No Papers Found?

✅ Refine your `SEARCH_TEXT` keywords (more specific or broader)  
✅ Increase `ARXIV_COUNT` / `CROSSREF_COUNT` (≤ 100 recommended)  
✅ Verify model setup: `MODEL_PROVIDER` and `MODEL` must match  

---

### 3. GitHub Action Failed?

✅ Check that all Secrets are correctly spelled and not empty  
✅ Ensure API key is valid (OpenAI account must have balance)  
✅ Review Action logs for error details (e.g., `API key invalid`, `SMTP authentication failed`)  

---

## ⚠️ Disclaimer

- This project is for **academic research only**; please follow the database usage policies  
- All papers remain the copyright of their respective authors and publishers  
- Use responsibly — avoid excessive querying that may burden database servers  

---
