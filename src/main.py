import os
import json
import asyncio
import contextlib
import requests
import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route
from event_store import InMemoryEventStore
from helper.logger import logging
from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
import mcp.types as types
from dotenv import load_dotenv

load_dotenv() 


ENFORMION_URL = "https://devapi.enformion.com/Contact/Enrich"
server = Server("enformion-mcp")


def check_and_raise_on_error(result: dict) -> dict:
    if not result.get("success", True):
        raise Exception(result.get("error", "Unknown error occurred"))
    return result


def call_enformion_api(request_body: dict) -> dict:
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "galaxy-ap-name": os.getenv("GALAXY_AP_NAME", ""),
        "galaxy-ap-password": os.getenv("GALAXY_AP_PASSWORD", ""),
        "galaxy-search-type": "DevAPIContactEnrich",
    }
    try:
        response = requests.post(ENFORMION_URL, headers=headers, json=request_body)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.RequestException as e:
        error_text = ''
        if e.response is not None:
            error_text = e.response.text
        return {
            "success": False,
            "error": f"{str(e)}. Response content: {error_text}"
        }


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    # Define input schema matching Enformion API expected fields
    input_schema = {
        "type": "object",
        "properties": {
            "FirstName": {"type": ["string", "null"]},
            "MiddleName": {"type": ["string", "null"]},
            "LastName": {"type": ["string", "null"]},
            "Dob": {"type": ["string", "null"], "pattern": r"\d{2}/\d{2}/\d{4}"},
            "Age": {"type": ["integer", "null"]},
            "Address": {
                "type": "object",
                "properties": {
                    "AddressLine1": {"type": ["string", "null"]},
                    "AddressLine2": {"type": ["string", "null"]},
                },
                "required": [],
            },
            "Phone": {"type": ["string", "null"]},
            "Email": {"type": ["string", "null"]},
        },
        "required": [],
    }
    return [
        types.Tool(
            name="enformion_contact_enrich",
            description="Call Enformion's Contact Enrich API to enrich contact details.",
            inputSchema=input_schema,
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> types.CallToolResult:
    try:
        if name != "enformion_contact_enrich":
            raise Exception("Invalid tool name")
        logging.info(f"Arguments: {arguments}")
        result = call_enformion_api(arguments)
        result = check_and_raise_on_error(result)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logging.error(f"Error in tool call: {e}")
        raise e


async def create_app():
    event_store = InMemoryEventStore(max_events_per_stream=100)

    try:
        session_manager = StreamableHTTPSessionManager(
            app=server,
            event_store=event_store,
            json_response=False,
            stateless=True,
        )
    except TypeError:
        session_manager = StreamableHTTPSessionManager(app=server)

    class HandleStreamableHttp:
        def __init__(self, session_manager):
            self.session_manager = session_manager

        async def __call__(self, scope, receive, send):
            try:
                await self.session_manager.handle_request(scope, receive, send)
            except Exception as e:
                logging.error(f"Streamable HTTP error: {e}")
                await send({
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [(b"content-type", b"application/json")],
                })
                await send({
                    "type": "http.response.body",
                    "body": json.dumps({"error": str(e)}).encode("utf-8"),
                })
    
    routes = [
        Route("/initialize", endpoint=HandleStreamableHttp(session_manager), methods=["POST"]),
        Route("/", endpoint=HandleStreamableHttp(session_manager), methods=["POST"]),  # Optional root
    ]

    middleware = [Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])]

    return Starlette(routes=routes, middleware=middleware)


if __name__ == "__main__":
    import uvicorn
    app = asyncio.run(create_app())
    uvicorn.run(app, host="0.0.0.0", port=8080)

#     routes = [Route("/mcp", endpoint=HandleStreamableHttp(session_manager), methods=["POST"])]
#     middleware = [Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])]

#     @contextlib.asynccontextmanager
#     async def lifespan(app):
#         async with session_manager.run():
#             yield

#     return Starlette(routes=routes, middleware=middleware, lifespan=lifespan)


# async def start_server():
#     app = await create_app()
#     host, port = "0.0.0.0", 8080
#     logging.info(f"Starting Enformion MCP server at {host}:{port}")
#     config = uvicorn.Config(app, host=host, port=port)
#     server = uvicorn.Server(config)
#     await server.serve()


# if __name__ == "__main__":
#     while True:
#         try:
#             asyncio.run(start_server())
#         except KeyboardInterrupt:
#             logging.info("Server stopped by user")
#             break
#         except Exception as e:
#             logging.error(f"Server crashed: {e}")
#             continue
