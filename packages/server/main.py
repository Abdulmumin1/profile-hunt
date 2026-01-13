"""
Profile Research Agent - OSINT Intelligence Tool with SSE

A professional-grade profile investigation agent with:
- Server-Sent Events (SSE) for real-time streaming
- Durable sessions - research continues if you disconnect
- Event replay on reconnect - never miss an update

Required environment variables:
- GOOGLE_API_KEY: For Gemini LLM
- TAVILY_API_KEY: For web search (get free key at tavily.com)
"""

import os
import sys
from aiohttp import web
from dotenv import load_dotenv
from ai_query.agents import AgentServer, AgentServerConfig

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.agent import ProfileResearchAgent

# Load environment variables
load_dotenv()

# Health check handler (works for both / and /health)
async def health_handler(request):
    return web.json_response({"status": "ok"})

if __name__ == "__main__":
    if not os.getenv("TAVILY_API_KEY"):
        print("⚠️  Warning: TAVILY_API_KEY not set. Web search will not work.")
        print("   Get a free API key at https://tavily.com")

    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Warning: GOOGLE_API_KEY not set. LLM calls will fail.")

    # Get allowed origins from environment (comma-separated) or use defaults
    default_origins = ['http://localhost:5173']
    env_origins = os.getenv("ALLOWED_ORIGINS", "")
    if env_origins:
        allowed_origins = [origin.strip() for origin in env_origins.split(",")]
    else:
        allowed_origins = default_origins

    config = AgentServerConfig(
        idle_timeout=3600,
        max_agents=800,
        allowed_origins=allowed_origins,
        enable_rest_api=True
    )

    # Create server and app
    server = AgentServer(ProfileResearchAgent, config=config)
    app = server.create_app()

    # Add health check endpoints for Railway
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)

    port = int(os.getenv("PORT", "8080"))

    print(f"🚀 Starting server on port {port}")
    print(f"📡 Health check: http://0.0.0.0:{port}/")

    web.run_app(app, host="0.0.0.0", port=port)
