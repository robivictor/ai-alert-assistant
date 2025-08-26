"""
MCP (Model Context Protocol) client for Atlassian integration.
"""

import os
from typing import Any, Dict, List, Optional

from mcp import Tool
from mcp.client.streamable_http import streamablehttp_client

from utilities.logger import get_logger

logger = get_logger(__name__)


class AtlassianMCPClient:
    """Enhanced MCP client for Atlassian services integration."""

    def __init__(self, confluence_url: str = None, mcp_server_url: str = None):
        self.confluence_url = confluence_url or os.getenv("CONFLUENCE_URL")
        self.username = os.getenv("CONFLUENCE_USERNAME")
        self.api_token = os.getenv("CONFLUENCE_API_TOKEN")
        self.mcp_server_url = mcp_server_url or os.getenv("MCP_SERVER_URL", "http://localhost:9000")
        self._client = None
        self._available_tools: List[Tool] = []
        self._connection_cache = None
        self._tools_cache_valid = False

    def get_server_url(self) -> str:
        """Get MCP server URL for HTTP connection."""
        logger.info(f"Using MCP server at {self.mcp_server_url}")

        if not self.mcp_server_url:
            raise ValueError("MCP_SERVER_URL not configured")

        return self.mcp_server_url

    async def validate_configuration(self) -> bool:
        """Validate MCP client configuration."""
        try:
            logger.info("Validating MCP client configuration...")
            # Just validate that we have the required parameters
            server_url = self.get_server_url()
            logger.info("MCP server URL validated successfully")
            logger.info("MCP client configuration validated")
            return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    async def get_available_tools(self) -> List[Tool]:
        """Get list of available MCP tools with improved error handling."""
        if not self._available_tools or not self._tools_cache_valid:
            try:
                server_url = self.get_server_url()
                logger.info(f"Connecting to MCP server at: {server_url}")
                # Use streamablehttp_client for streamable-http transport
                async with streamablehttp_client(server_url) as (read, write):
                    # Initialize the session
                    logger.info("Initializing MCP session...")
                    init_result = await write.initialize()
                    logger.info(f"MCP session initialized successfully: {init_result}")

                    # List available tools
                    logger.info("Requesting tools list from MCP server...")
                    tools_response = await write.list_tools()
                    logger.info(f"MCP server response: {tools_response}")
                    self._available_tools = tools_response.tools
                    self._tools_cache_valid = True
                    logger.info(f"Found {len(self._available_tools)} available tools")
                    for tool in self._available_tools:
                        logger.info(f"Available tool: {tool.name} - {tool.description}")
            except Exception as e:
                logger.error(f"Failed to list tools: {e}")
                # Return empty list if tools can't be loaded
                self._available_tools = []
                self._tools_cache_valid = False
        return self._available_tools

    async def filter_tools(self, tool_names: List[str]) -> List[Tool]:
        """Filter tools by name with graceful handling."""
        try:
            all_tools = await self.get_available_tools()
            logger.info(f"Available tools from server: {[tool.name for tool in all_tools if hasattr(tool, 'name')]}")
            logger.info(f"Looking for tools: {tool_names}")
            filtered = [
                tool
                for tool in all_tools
                if hasattr(tool, "name") and tool.name in tool_names
            ]
            logger.info(f"Filtered to {len(filtered)} tools: {[tool.name for tool in filtered]}")
            return filtered
        except Exception as e:
            logger.warning(f"Failed to filter tools: {e}")
            return []

    async def get_confluence_tools(self) -> List[Tool]:
        """Get Confluence-specific MCP tools."""
        # These are the actual tool names enabled in the Docker container
        confluence_tools = [
            "confluence_search",
            "confluence_get_comments",
            "confluence_get_labels",
            "confluence_get_page",
            "confluence_get_page_children",
        ]
        return await self.filter_tools(confluence_tools)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Clean up client resources if needed
        pass


class MCPToolManager:
    """Manages MCP tools for the AI Alert Assistant."""

    def __init__(self, atlassian_client: AtlassianMCPClient):
        self.atlassian = atlassian_client
        self.logger = get_logger(__name__)

    async def discover_confluence_resources(self) -> Dict[str, Any]:
        """Discover available Confluence resources with graceful fallback."""
        try:
            tools = await self.atlassian.get_confluence_tools()

            # Get accessible resources
            resource_tool = next(
                (
                    t
                    for t in tools
                    if hasattr(t, "name")
                    and t.name == "confluence_get_space"
                ),
                None,
            )

            if resource_tool:
                try:
                    # Use MCP client to call the tool
                    server_url = self.atlassian.get_server_url()
                    async with streamablehttp_client(server_url) as (read, write):
                        await write.initialize()
                        result = await write.call_tool(resource_tool.name, {})
                        self.logger.info("Discovered Confluence resources")
                        return {
                            "status": "success",
                            "resources_available": True,
                            "data": result.content,
                        }
                except Exception as resource_error:
                    self.logger.warning(f"Resource discovery failed: {resource_error}")
                    return {
                        "status": "partial_success",
                        "resources_available": False,
                        "message": "Resource discovery unavailable",
                    }
            else:
                self.logger.info("Resource discovery tool not available")
                return {
                    "status": "partial_success",
                    "resources_available": False,
                    "message": "Resource discovery tool not available",
                }

        except Exception as e:
            self.logger.warning(f"Failed to discover resources: {e}")
            return {
                "status": "partial_success",
                "resources_available": False,
                "message": "Resource discovery unavailable"
            }

    async def search_confluence_content(
        self, query: str, space_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search Confluence content using MCP with graceful fallback."""
        try:
            tools = await self.atlassian.get_confluence_tools()

            search_tool = next(
                (t for t in tools if hasattr(t, "name") and t.name == "confluence_search"),
                None,
            )

            if search_tool:
                self.logger.info(f"Searching Confluence for: {query}")
                params = {"query": query}
                if space_key:
                    params["space_key"] = space_key

                try:
                    server_url = self.atlassian.get_server_url()
                    async with streamablehttp_client(server_url) as (read, write):
                        await write.initialize()
                        result = await write.call_tool(search_tool.name, params)
                        return {"status": "success", "query": query, "results": result.content}
                except Exception as search_error:
                    self.logger.warning(f"MCP search failed, using fallback: {search_error}")
                    return {
                        "status": "partial_success",
                        "query": query,
                        "message": "Documentation search unavailable, using general guidance",
                        "fallback": True
                    }
            else:
                self.logger.info("confluence_search tool not available, using fallback")
                return {
                    "status": "partial_success",
                    "query": query,
                    "message": "Search tool not available, providing general guidance",
                    "fallback": True
                }

        except Exception as e:
            self.logger.warning(f"Search failed, using fallback: {e}")
            return {
                "status": "partial_success",
                "query": query,
                "message": "Documentation search unavailable, using general guidance",
                "fallback": True
            }

    async def get_confluence_page(self, page_id: str) -> Dict[str, Any]:
        """Retrieve specific Confluence page content."""
        try:
            tools = await self.atlassian.get_confluence_tools()

            page_tool = next(
                (
                    t
                    for t in tools
                    if hasattr(t, "name") and t.name == "confluence_get_page"
                ),
                None,
            )

            if page_tool:
                self.logger.info(f"Retrieving Confluence page: {page_id}")
                server_url = self.atlassian.get_server_url()
                async with streamablehttp_client(server_url) as (read, write):
                    await write.initialize()
                    result = await write.call_tool(page_tool.name, {"page_id": page_id})
                    return {"status": "success", "page_id": page_id, "content": result.content}
            else:
                self.logger.warning("getConfluencePage tool not found")
                return {
                    "status": "error",
                    "message": "Page retrieval tool not available",
                }

        except Exception as e:
            self.logger.error(f"Page retrieval failed: {e}")
            return {"status": "error", "message": str(e)}
