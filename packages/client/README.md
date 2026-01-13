# Research Intelligence Agent

A real-world AI research agent built with `ai-query` (Python) and SvelteKit. This agent can search the web, read articles, track news, and maintain a persistent knowledge base.

## Features

### Real APIs & Capabilities

- **🔍 Web Search** - Powered by [Tavily API](https://tavily.com) for accurate, AI-optimized search results
- **📄 Webpage Reader** - Fetches and parses web pages to extract content
- **📰 News Search** - Find recent news articles on any topic
- **💾 Knowledge Base** - SQLite-backed persistent storage for research findings
- **📊 Report Generation** - Synthesize findings into comprehensive reports

### Agent Tools

| Tool | Description |
|------|-------------|
| `web_search` | Search the internet for current information |
| `read_webpage` | Fetch and read full content of web pages |
| `search_news` | Find recent news articles |
| `save_finding` | Store important research to knowledge base |
| `list_findings` | Review all saved findings |
| `search_findings` | Search through saved research |
| `generate_report` | Create reports from accumulated research |
| `clear_findings` | Clear the knowledge base |

## Project Structure

```
packages/
├── server/              # Python backend
│   ├── server.py        # Research Intelligence Agent
│   ├── pyproject.toml   # Dependencies (ai-query, tavily, beautifulsoup4)
│   └── .env.example     # API key configuration
└── client/              # SvelteKit frontend
    └── src/routes/
        └── +page.svelte # Chat interface
```

## Prerequisites

- Python 3.13+ (managed by `uv`)
- Node.js 18+
- **API Keys:**
  - [Google Gemini API Key](https://aistudio.google.com/app/apikey)
  - [Tavily API Key](https://tavily.com) (free tier available)

## Setup

### 1. Server

```bash
cd packages/server

# Install dependencies
uv sync

# Configure API keys
cp .env.example .env
# Edit .env and add your API keys

# Run the server
uv run server.py
```

### 2. Client

```bash
cd packages/client

# Install dependencies
npm install

# Run dev server
npm run dev
```

Open `http://localhost:5173` in your browser.

## Usage Examples

**Research a topic:**
> "Research the latest developments in quantum computing"

**Get news updates:**
> "Search for news about AI regulations this week"

**Deep dive into a source:**
> "Read this article: https://example.com/article"

**Build knowledge:**
> "Save that finding about quantum error correction"

**Generate reports:**
> "Generate a report on quantum computing from my saved findings"

## Architecture

```
User → SvelteKit UI → WebSocket → AgentServer
                                      ↓
                              ResearchAgent (SQLiteAgent)
                                      ↓
                     ┌────────────────┼────────────────┐
                     ↓                ↓                ↓
               Tavily API      httpx/BS4        SQLite DB
               (web search)    (page reader)   (knowledge base)
```

## Tech Stack

- **Backend:** Python, ai-query SDK, Tavily, BeautifulSoup4, SQLite
- **Frontend:** SvelteKit, Tailwind CSS, Lucide Icons
- **LLM:** Google Gemini 2.0 Flash
- **Communication:** WebSocket with JSON streaming
