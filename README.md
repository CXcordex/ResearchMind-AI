<div align="center">

# 🧠 ResearchMind
### Multi-Agent AI Research Automation Platform

**NVIDIA NIM · OpenRouter · CrewAI · Streamlit**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.55+-00C896?style=flat)](https://crewai.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

*Automate research, analyse documents, and chat with your findings — all in one dark-themed Streamlit app.*

</div>

---

## 📌 What is ResearchMind?

ResearchMind is a single-page Streamlit application that combines three independent AI systems into one cohesive research platform:

| Mode | What it does | API |
|------|-------------|-----|
| **📝 Topic Research** | Runs a 5-agent pipeline that searches, validates, extracts evidence, and writes a citation-backed Markdown report | NVIDIA NIM |
| **📄 Document Analysis** | Uploads any PDF or image, extracts all text and figures, summarises, identifies findings, and answers your questions | OpenRouter #1 |
| **🧠 Mind AI Chat** | A floating chat assistant that references both your latest research report and document analysis | OpenRouter #2 |

Everything is gated behind an email + password authentication screen. All three modes share a single SQLite database so the chatbot always has full context.

---

## ✨ Features

### 🔐 Authentication
- Email + password login and sign-up screen before any app content loads
- Password validation, error banners, and "Forgot password?" link
- Google and GitHub OAuth stubs (coming in v2)
- Logout button in the sidebar that clears all session data

### 🔭 Topic Research Pipeline (5 Agents via NVIDIA NIM)
- **Research Strategist** — decomposes your topic into 4–6 targeted search queries
- **Academic Source Finder** — executes queries via Exa API with Tavily as fallback
- **Quality Evaluator** — scores and selects the top 5 sources (credibility + recency + depth)
- **Evidence Extractor** — fetches PDFs and webpages, pulls metrics, datasets, and quotes
- **Research Writer** — synthesises a full Markdown report with `[N]` inline citations
- Live execution log with colour-coded steps (INFO / TOOL / DONE / ERROR)
- Results in 4 tabs: Insights · Sources · Queries · Raw Report (downloadable `.md`)
- User-selectable NVIDIA NIM models and temperature slider

### 📂 Document Intelligence Studio (OpenRouter Vision)
- Upload: PDF, PNG, JPG, WEBP, TIFF, BMP
- **Single API handles everything:** OCR, text extraction, image/figure description, summary, key findings, and all Q&A on that document
- Results in 4 tabs: OCR Text · Key Findings · Q&A · Executive Summary
- Follow-up Q&A — ask unlimited questions using the already-extracted text (no re-upload)
- Download extracted text as `.txt`

### 💬 Mind AI Research Assistant
- Floating 🧠 button (bottom-right corner) — click to open, ✕ to close
- Full context injection from shared SQLite: latest research report + document analysis
- Conversation memory (last 12 turns)
- Export chat as `.DOCX` or `.TXT`
- Powered by OpenRouter free models with automatic fallback chain

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      app.py  (Streamlit)                        │
│                                                                 │
│   render_auth()  ──────────────────────────────────────────┐   │
│   (login / signup — renders before everything else)        │   │
│                                                            ↓   │
│  ┌──────────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │  NVIDIA NIM API  │  │ OpenRouter #1  │  │ OpenRouter #2 │  │
│  │                  │  │                │  │               │  │
│  │  Topic Research  │  │ Document Mode  │  │  Mind AI Chat │  │
│  │  5 CrewAI agents │  │  OCR + Vision  │  │  + DB context │  │
│  │  Planner         │  │  Text extract  │  │               │  │
│  │  Search          │  │  Image descr.  │  │               │  │
│  │  Validator       │  │  Q&A (initial) │  │               │  │
│  │  Extractor       │  │  Q&A (follow-  │  │               │  │
│  │  Synthesizer     │  │   up, same API)│  │               │  │
│  └────────┬─────────┘  └───────┬────────┘  └───────┬───────┘  │
│           └───────────────────┬┘                   │          │
│                               ↓                    │          │
│              ┌────────────────────────────────┐    │          │
│              │   SQLite  research_store.db     │←───┘          │
│              │   users                        │               │
│              │   research_sessions            │               │
│              │   document_sessions            │               │
│              │   chat_history                 │               │
│              └────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/CXcordex/Multi_Ai_Research_Agent.git
cd Multi_Ai_Research_Agent
```

### 2. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure API keys
```bash
cp .env.example .env
```

Edit `.env` with your keys:
```bash
# NVIDIA NIM — Topic Research Pipeline
NVIDIA_API_KEY=nvapi-your_key_here

# OpenRouter #1 — Document Analysis (OCR + ALL document Q&A)
OPENROUTER_PDF_KEY=sk-or-v1-your_key_here

# OpenRouter #2 — Mind AI Chatbot
OPENROUTER_CHAT_KEY=sk-or-v1-your_key_here

# Search APIs (used by CrewAI Search Agent)
EXA_API_KEY=your_exa_key_here
TAVILY_API_KEY=your_tavily_key_here
```

### 5. Run the app
```bash
streamlit run app.py
```

Open **http://localhost:8501** — the login screen will appear first.

**Demo credentials:**
| Email | Password |
|-------|---------|
| `demo@researchmind.ai` | `password123` |
| `admin@researchmind.ai` | `admin2024` |

---

## 📁 Project Structure

```
Multi_Ai_Research_Agent/
│
├── app.py                          # Entire Streamlit application
├── db.py                           # SQLite helper functions (CRUD)
├── .env                            # Your API keys (never commit this)
├── .env.example                    # Template for .env
├── requirements.txt                # Python dependencies
├── research_store.db               # SQLite DB (auto-created on first run)
│
├── research_crew/
│   ├── agents/
│   │   ├── planner_agent.py        # Research Strategist agent
│   │   ├── search_agent.py         # Academic Source Finder agent
│   │   ├── validator_agent.py      # Quality Evaluator agent
│   │   ├── extractor_agent.py      # Technical Evidence Extractor agent
│   │   └── synthesizer_agent.py    # Research Writer agent
│   │
│   ├── tasks/
│   │   ├── planning_task.py        # Planner task definition
│   │   ├── search_task.py          # Search task definition
│   │   ├── validation_task.py      # Validation task definition
│   │   ├── extraction_task.py      # Extraction task definition
│   │   └── summary_task.py        # Synthesis task definition
│   │
│   └── tools/
│       ├── search_tool.py          # ExaSearchTool + TavilySearchTool
│       ├── pdf_extractor.py        # PDFExtractorTool (PyMuPDF)
│       └── web_parser.py           # WebParserTool (BeautifulSoup4)
│
└── utils/
    ├── text_chunker.py             # Token-bounded document chunking
    └── token_utils.py              # tiktoken counting + truncation
```

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| **UI Framework** | Streamlit 1.35+ |
| **Agent Framework** | CrewAI 0.55+ |
| **LLM — Research** | NVIDIA NIM (`mistral-large-3-675b`, user-selectable) |
| **LLM — Documents** | OpenRouter free tier (vision + text models) |
| **LLM — Chatbot** | OpenRouter free tier (llama-3.1-8b) |
| **Search** | Exa API (primary) + Tavily (fallback) |
| **PDF Parsing** | PyMuPDF (fitz) |
| **Web Parsing** | BeautifulSoup4 |
| **Token Counting** | tiktoken (cl100k_base) |
| **Database** | SQLite 3 (shared across all three modes) |
| **Auth** | bcrypt via passlib |
| **HTTP / Retry** | requests + tenacity |

---

## 🤖 NVIDIA NIM Models (Topic Research)

Select from the sidebar dropdown:

| Model | Best for |
|-------|---------|
| `mistralai/mistral-large-3-675b-instruct-2512` | Default — balanced quality and speed |
| `google/gemma-3-27b-it` | Strong reasoning |
| `meta/llama-3.3-70b-instruct` | Complex synthesis |
| `deepseek-ai/deepseek-r1` | Deep technical analysis |
| `microsoft/phi-4` | Efficient, lower latency |

**Temperature guide:**

| Range | Label | Use case |
|-------|-------|---------|
| 0.0 – 0.3 | Precise | JSON output, citations, factual reports |
| 0.3 – 0.6 | Balanced | General research, natural writing |
| 0.6 – 1.0 | Creative | Brainstorming, exploratory topics |

---

## 📄 OpenRouter Models (Document Analysis + Chatbot)

### Document Analysis (OpenRouter #1)
The same API key handles **all** document tasks — there is no secondary API:

| Task | Model |
|------|-------|
| Initial OCR + image extraction | `meta-llama/llama-3.2-11b-vision-instruct:free` |
| Q&A on extracted text | `google/gemma-3-27b-it:free` |
| Fallback (if rate limited) | `mistralai/mistral-7b-instruct:free` |

### Chatbot (OpenRouter #2)
| Priority | Model |
|----------|-------|
| 1st | `meta-llama/llama-3.1-8b-instruct:free` |
| 2nd | `google/gemma-3-9b-it:free` |
| 3rd | `mistralai/mistral-7b-instruct:free` |

> **Rate limiting:** The app includes automatic fallback chains with exponential backoff (2s → 4s → 8s). If all free models are exhausted, a clear "please wait 30 seconds" message is shown.

---

## 🗄️ Database Schema

SQLite database (`research_store.db`) — auto-created on first run:

```sql
-- Authentication
users (id, email, full_name, password_hash, created_at, last_login)

-- Topic Research outputs — read by chatbot for context
research_sessions (id, user_id, topic, queries, sources, evidence, report,
                   elapsed_sec, model_used, temperature, created_at)

-- Document Analysis outputs — read by chatbot + follow-up Q&A
document_sessions (id, user_id, filename, file_size_kb, mime_type,
                   full_text, summary, key_findings, key_topics,
                   metadata_info, question, answer, model_used, created_at)

-- Mind AI conversation log
chat_history (id, user_id, role, content, session_tag, created_at)
```

---

## 🔒 Security Notes

- API keys loaded from `.env` — never hardcoded in source
- `.env` and `research_store.db` are in `.gitignore` — never committed
- Passwords stored as bcrypt hashes — never plaintext
- All SQL uses parameterised queries — no injection risk
- Document files processed in memory — never written to disk
- All HTTP requests have explicit timeouts
- User data scoped to `user_id` — no cross-user access

---

## 🐳 Docker

```bash
# Build and run
docker compose up -d --build

# View logs
docker compose logs -f

# Stop
docker compose down
```

```yaml
# docker-compose.yml
version: "3.9"
services:
  researchmind:
    build: .
    ports: ["8501:8501"]
    volumes: ["./data:/app/data"]
    env_file: [.env]
    restart: unless-stopped
```

---

## ☁️ Deploy to Streamlit Community Cloud

1. Push to GitHub (ensure `.env` and `*.db` are in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select `app.py`
3. Add your secrets (Settings → Secrets):

```toml
NVIDIA_API_KEY      = "nvapi-..."
OPENROUTER_PDF_KEY  = "sk-or-v1-..."
OPENROUTER_CHAT_KEY = "sk-or-v1-..."
EXA_API_KEY         = "..."
TAVILY_API_KEY      = "..."
DB_PATH             = "/tmp/research_store.db"
```

---

## 📋 Requirements

```txt
streamlit>=1.35.0
python-dotenv>=1.0.0
requests>=2.31.0
tenacity>=8.2.0
crewai>=0.55.0
tiktoken>=0.6.0
PyMuPDF>=1.23.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
passlib[bcrypt]>=1.7.4
pydantic>=2.0.0
```

---

## 🛣️ Roadmap

- [x] 5-agent topic research pipeline (NVIDIA NIM)
- [x] Document analysis with OCR + vision (OpenRouter)
- [x] Mind AI chatbot with shared DB context
- [x] Email + password authentication
- [x] OpenRouter fallback chain with 429 retry logic
- [ ] Real OAuth (Google, GitHub)
- [ ] Vector search over stored research reports
- [ ] Multi-user concurrent sessions
- [ ] Email-based password reset
- [ ] Export research report as PDF / DOCX

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with 🧠 by [CXcordex](https://github.com/CXcordex)**

*If this project helped you, please give it a ⭐*

</div>
