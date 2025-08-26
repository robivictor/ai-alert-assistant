#!/usr/bin/env python3
"""
Test script to list all available MCP tools from mcp-atlassian server.
"""

import asyncio
import os
import sys
sys.path.insert(0, 'src')

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

async def list_mcp_tools():
    # Load environment variables
    load_dotenv()
    
    confluence_url = os.getenv('CONFLUENCE_URL')
    username = os.getenv('CONFLUENCE_USERNAME')
    api_token = os.getenv('CONFLUENCE_API_TOKEN')
    
    print("=== MCP Atlassian Tool Discovery ===")
    print(f'Confluence URL: {confluence_url}')
    print(f'Username: {username}')
    print(f'API Token: {"*" * (len(api_token) - 10) + api_token[-10:] if api_token else "Not set"}')
    print()
    
    # Create MCP server parameters
    server_params = StdioServerParameters(
        command='mcp-atlassian',
        env={
            'CONFLUENCE_URL': confluence_url,
            'CONFLUENCE_USERNAME': username,
            'CONFLUENCE_API_TOKEN': api_token,
        }
    )
    
    try:
        print("Connecting to MCP server...")
        async with stdio_client(server_params) as streams:
            read_stream, write_stream = streams
            # Initialize the client
            print("Initializing MCP client...")
            await write_stream.initialize()
            
            # List available tools
            print("Requesting tools list...")
            tools_response = await write_stream.list_tools()
            
            print(f'\n✅ Successfully found {len(tools_response.tools)} tools:\n')
            
            for i, tool in enumerate(tools_response.tools, 1):
                print(f'{i:2d}. {tool.name}')
                print(f'    Description: {tool.description}')
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    print(f'    Input Schema: {tool.inputSchema}')
                print()
                
    except Exception as e:
        print(f'❌ Error listing tools: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(list_mcp_tools())