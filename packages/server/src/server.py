import asyncio
from aiohttp import web
from aiohttp_cors import setup as cors_setup, ResourceOptions
from ai_query.agents import AgentServer, AgentServerConfig

class ProfileServer(AgentServer):
    """
    Custom AgentServer that adds a REST API for triggering agent actions.
    """

    def serve(self, host="localhost", port=8080):
        app = web.Application()

        # Set up CORS
        allowed_origins = self.config.allowed_origins if self.config and self.config.allowed_origins else ["*"]

        # If allowed_origins is a list of strings, use it. If it's "*", map to ResourceOptions
        cors_options = {}
        for origin in allowed_origins:
            cors_options[origin] = ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
            )

        cors = cors_setup(app, defaults=cors_options)

        # 1. Register Custom Routes
        # Note: We use cors.add() to ensure CORS is applied

        # Message endpoint
        resource_msg = cors.add(app.router.add_resource("/agent/{agent_id}/message"))
        cors.add(resource_msg.add_route("POST", self.handle_message))

        # Status endpoint
        resource_status = cors.add(app.router.add_resource("/agent/{agent_id}/status"))
        cors.add(resource_status.add_route("GET", self.handle_status))

        # Health endpoint
        resource_health = cors.add(app.router.add_resource("/health"))
        cors.add(resource_health.add_route("GET", self.handle_health))

        # 2. Register Native AgentServer Routes
        # We manually register the handlers provided by AgentServer

        # SSE Events
        resource_sse = cors.add(app.router.add_resource("/agent/{agent_id}/events"))
        cors.add(resource_sse.add_route("GET", self._handle_sse))

        # WebSocket
        resource_ws = cors.add(app.router.add_resource("/agent/{agent_id}/ws"))
        cors.add(resource_ws.add_route("GET", self._handle_websocket))

        # REST API (if enabled)
        if self.config and self.config.enable_rest_api:
            # Get State
            resource_state = cors.add(app.router.add_resource("/agent/{agent_id}/state"))
            cors.add(resource_state.add_route("GET", self._handle_get_state))
            cors.add(resource_state.add_route("PUT", self._handle_put_state))

            # Delete Agent
            resource_del = cors.add(app.router.add_resource("/agent/{agent_id}"))
            cors.add(resource_del.add_route("DELETE", self._handle_delete_agent))

            # List Agents
            resource_list = cors.add(app.router.add_resource("/agents"))
            cors.add(resource_list.add_route("GET", self._handle_list_agents))

        print(f"📡 Profile Server running at http://{host}:{port}")
        web.run_app(app, host=host, port=port)

    async def handle_message(self, request: web.Request) -> web.Response:
        agent_id = request.match_info["agent_id"]

        try:
            data = await request.json()
            message = data.get("message")
        except:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        if not message:
            return web.json_response({"error": "Message required"}, status=400)

        # Get or create the agent
        try:
            agent = self.get_or_create(agent_id)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

        # Run the agent in the background
        asyncio.create_task(self._run_agent(agent, message))

        return web.json_response({"status": "started", "agent_id": agent_id})

    async def _run_agent(self, agent, message):
        """Execute the agent loop."""
        try:
            # Drive the generator to completion.
            # Output is automatically logged to DB and streamed to SSE clients.
            async for _ in agent.stream_chat(message):
                pass
        except Exception as e:
            print(f"Agent error: {e}")

    async def handle_status(self, request: web.Request) -> web.Response:
        agent_id = request.match_info["agent_id"]
        # Check if agent exists/is active
        return web.json_response({"active": True, "agent_id": agent_id})

    async def handle_health(self, request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})
