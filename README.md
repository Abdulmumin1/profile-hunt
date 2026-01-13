# Profile Research Agent

> **Demo application for [ai-query.dev](https://ai-query.dev)** - A Python framework for building AI agents with built-in persistence, streaming, and tool orchestration.

An OSINT-powered profile research application that demonstrates the capabilities of the `ai-query` framework. Built with a Python backend and SvelteKit frontend.

## What This Demonstrates

This project showcases `ai-query` features:

- **ChatAgent** - Conversational AI agents with memory and state
- **SQLiteAgent** - Built-in database persistence for agent data
- **SSE Streaming** - Real-time Server-Sent Events for live updates
- **Tool System** - Declarative tools with automatic schema generation
- **Event Replay** - Reconnect and replay missed events with `Last-Event-ID`
- **AgentServer** - Production-ready HTTP server with REST + WebSocket APIs

## Project Structure

```
packages/
├── server/          # Python backend using ai-query
│   ├── main.py      # AgentServer entry point
│   └── src/
│       ├── agent.py    # ProfileResearchAgent implementation
│       ├── tools.py    # Web search & scraping tools
│       └── scraper.py  # Social media scrapers
└── client/          # SvelteKit frontend (Svelte 5)
    └── src/routes/
        ├── +page.svelte           # Landing page
        └── [session_id]/+page.svelte  # Chat interface
```

## Features

- **Multi-Tool Agent** - 14+ tools for web search, social media scraping, and data management
- **Real-Time Streaming** - SSE-based live updates as the agent works
- **Session Persistence** - SQLite database per session with event replay
- **Profile Building** - Discovers and links social media accounts across platforms
- **Dossier Generation** - Compiles research into comprehensive reports

## Prerequisites

- Python 3.13+ (managed by `uv`)
- Node.js 18+ & pnpm
- API Keys:
  - `GOOGLE_API_KEY` - Google Gemini API
  - `TAVILY_API_KEY` - [Tavily](https://tavily.com) web search (free tier available)

## Local Development

### 1. Server (Backend)

```bash
cd packages/server

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the server
uv run python main.py
```

Server starts on `http://localhost:8081`

### 2. Client (Frontend)

```bash
cd packages/client

# Install dependencies
pnpm install

# Run dev server
pnpm dev
```

Open `http://localhost:5173` in your browser.

## Deployment

### Railway (Recommended)

The server is configured for Railway deployment:

1. Connect your repo to Railway
2. Set the root directory to `packages/server`
3. Add environment variables:
   - `GOOGLE_API_KEY`
   - `TAVILY_API_KEY`
   - `ALLOWED_ORIGINS` - Your frontend URL(s), comma-separated

Railway will automatically detect the `railway.toml` and `nixpacks.toml` configuration.

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | Yes |
| `TAVILY_API_KEY` | Tavily web search API key | Yes |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | For production |
| `PORT` | Server port (auto-set by Railway) | No |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/agents` | GET | List all active agents |
| `/agent/{id}/chat` | POST | Send message to agent |
| `/agent/{id}/events` | GET | SSE event stream |
| `/agent/{id}/state` | GET | Get agent state |
| `/agent/{id}/messages` | GET | Get message history |
| `/agent/{id}` | DELETE | Delete agent |

## Architecture

```
User → SvelteKit UI → SSE/REST → AgentServer → ProfileResearchAgent
                                                    ├── SQLite (persistence)
                                                    ├── Event Log (replay)
                                                    ├── Gemini LLM
                                                    └── Tools
                                                        ├── Web Search (Tavily)
                                                        ├── Social Scrapers
                                                        └── Data Management
```

## Learn More

- **ai-query Framework**: [ai-query.dev](https://ai-query.dev)
- **Documentation**: [docs.ai-query.dev](https://docs.ai-query.dev)

## License

MIT
