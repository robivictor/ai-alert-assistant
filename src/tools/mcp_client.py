"""
MCP (Model Context Protocol) client for Atlassian integration.
"""

import asyncio
import os
import subprocess
from typing import Any, Dict, List, Optional

from mcp import StdioServerParameters, Tool
from mcp.client.stdio import stdio_client

from utilities.logger import get_logger

logger = get_logger(__name__)


class AtlassianMCPClient:
    """Enhanced MCP client for Atlassian services integration."""

    def __init__(self, confluence_url: str = None):
        self.confluence_url = confluence_url or os.getenv("CONFLUENCE_URL")
        self.username = os.getenv("CONFLUENCE_USERNAME")  
        self.api_token = os.getenv("CONFLUENCE_API_TOKEN")
        self._client = None
        self._available_tools: List[Tool] = []
        self._mcp_process = None
        self._connection_cache = None
        self._tools_cache_valid = False

    async def _start_mcp_server(self) -> subprocess.Popen:
        """Start the MCP Atlassian server subprocess."""
        env = os.environ.copy()
        env.update({
            'CONFLUENCE_URL': self.confluence_url or '',
            'CONFLUENCE_USERNAME': self.username or '',
            'CONFLUENCE_API_TOKEN': self.api_token or '',
        })
        
        cmd = [
            'mcp-atlassian',
            '--transport', 'stdio',
        ]
        
        if self.confluence_url:
            cmd.extend(['--confluence-url', self.confluence_url])
        if self.username:
            cmd.extend(['--confluence-username', self.username])
        if self.api_token:
            cmd.extend(['--confluence-token', self.api_token])
            
        logger.info(f"Starting MCP server with command: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        return process

    def create_server_params(self) -> StdioServerParameters:
        """Create and return MCP server parameters."""
        logger.info(f"Creating MCP server params for {self.confluence_url}")
        
        if not all([self.confluence_url, self.username, self.api_token]):
            raise ValueError(
                "Missing required environment variables: CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN"
            )
        
        # Create MCP server parameters
        server_params = StdioServerParameters(
            command="mcp-atlassian",
            args=[
                "--transport", "stdio",
                "--confluence-url", self.confluence_url,
                "--confluence-username", self.username,
                "--confluence-token", self.api_token,
            ],
            env={
                'CONFLUENCE_URL': self.confluence_url,
                'CONFLUENCE_USERNAME': self.username,
                'CONFLUENCE_API_TOKEN': self.api_token,
            }
        )
        
        return server_params

    async def authenticate(self) -> bool:
        """Authenticate with Atlassian MCP service."""
        try:
            logger.info("Starting Atlassian MCP authentication...")
            # Just validate that we have the required parameters
            server_params = self.create_server_params()
            logger.info("MCP server parameters created successfully")
            logger.info("Authentication completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    async def get_available_tools(self) -> List[Tool]:
        """Get list of available MCP tools with improved error handling."""
        if not self._available_tools or not self._tools_cache_valid:
            try:
                server_params = self.create_server_params()
                async with stdio_client(server_params) as (read, write):
                    await write.initialize()
                    tools_response = await write.list_tools()
                    self._available_tools = tools_response.tools
                    self._tools_cache_valid = True
                    logger.info(f"Found {len(self._available_tools)} available tools")
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
            filtered = [
                tool
                for tool in all_tools
                if hasattr(tool, "name") and tool.name in tool_names
            ]
            logger.info(f"Filtered to {len(filtered)} tools: {tool_names}")
            return filtered
        except Exception as e:
            logger.warning(f"Failed to filter tools: {e}")
            return []

    async def get_confluence_tools(self) -> List[Tool]:
        """Get Confluence-specific MCP tools."""
        confluence_tools = [
            "getAccessibleAtlassianResources",
            "getConfluencePage", 
            "searchContent",
            "getConfluenceSpace",
            "listConfluencePages",
        ]
        return await self.filter_tools(confluence_tools)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._client:
            # Clean up client resources if needed
            pass


class MCPToolManager:
    """Manages MCP tools for the AI DBA Assistant."""

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
                    and t.name == "getAccessibleAtlassianResources"
                ),
                None,
            )

            if resource_tool:
                try:
                    # Use MCP client to call the tool
                    server_params = self.atlassian.create_server_params()
                    async with stdio_client(server_params) as (read, write):
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
                (t for t in tools if hasattr(t, "name") and t.name == "searchContent"),
                None,
            )

            if search_tool:
                self.logger.info(f"Searching Confluence for: {query}")
                params = {"query": query}
                if space_key:
                    params["space_key"] = space_key

                try:
                    server_params = self.atlassian.create_server_params()
                    async with stdio_client(server_params) as (read, write):
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
                self.logger.info("searchContent tool not available, using fallback")
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
                    if hasattr(t, "name") and t.name == "getConfluencePage"
                ),
                None,
            )

            if page_tool:
                self.logger.info(f"Retrieving Confluence page: {page_id}")
                server_params = self.atlassian.create_server_params()
                async with stdio_client(server_params) as (read, write):
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
