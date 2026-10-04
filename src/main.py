#!/usr/bin/env python3
"""
MCP server entry point.

Connects the MCP protocol layer (mcp SDK) to the application container.
All logging goes to stderr — stdout is reserved for the stdio transport.
"""

import asyncio
import sys

import mcp.types as types
from mcp.server import Server, ServerRequestContext
from mcp.server.stdio import stdio_server

from application.handlers.tool_registry import ALL_TOOLS
from container import get_container
from libraries.logger import get_logger

logger = get_logger(__name__)


def create_server() -> Server:
    container = get_container()

    async def on_list_tools(
        ctx: ServerRequestContext, params: types.PaginatedRequestParams | None
    ) -> types.ListToolsResult:
        return types.ListToolsResult(tools=ALL_TOOLS)

    async def on_call_tool(
        ctx: ServerRequestContext, params: types.CallToolRequestParams
    ) -> types.CallToolResult:
        content = await container.tool_handler.handle(params.name, params.arguments)
        return types.CallToolResult(content=content)

    return Server(
        container.config.server.name,
        version=container.config.server.version,
        on_list_tools=on_list_tools,
        on_call_tool=on_call_tool,
    )


async def _run() -> None:
    container = get_container()
    server = create_server()

    logger.info("%s v%s starting — API: %s",
                container.config.server.name,
                container.config.server.version,
                container.config.api.base_url)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        logger.info("Server stopped")
    except Exception as e:
        logger.exception("Fatal: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
