#!/usr/bin/env python3
"""
Simple test client for the Phish MCP Server.
Tests basic functionality by calling various tools.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_server():
    """Test the MCP server by calling various tools."""
    
    # Server parameters - points to our MCP server script
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env=None
    )
    
    print("🚀 Connecting to Phish MCP Server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            print("✅ Connected to server\n")
            
            # List available tools
            print("📋 Listing available tools...")
            tools = await session.list_tools()
            print(f"Found {len(tools.tools)} tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            print()
            
            # Test 1: Get statistics
            print("📊 Test 1: Getting database statistics...")
            result = await session.call_tool("get_statistics", {})
            print(result.content[0].text)
            print()
            
            # Test 2: Search shows by year
            print("🔍 Test 2: Searching for shows in 1997...")
            result = await session.call_tool("search_shows", {"year": 1997, "limit": 5})
            print(result.content[0].text)
            print()
            
            # Test 3: Get specific show details
            print("🎸 Test 3: Getting details for 1997-12-31 (New Year's Run)...")
            result = await session.call_tool("get_show_details", {"date": "1997-12-31"})
            print(result.content[0].text[:500] + "..." if len(result.content[0].text) > 500 else result.content[0].text)
            print()
            
            # Test 4: Search for a song
            print("🎵 Test 4: Searching for 'Harry Hood' performances...")
            result = await session.call_tool("search_songs", {"song_title": "Harry Hood", "limit": 3})
            print(result.content[0].text)
            print()
            
            # Test 5: Search shows with audio
            print("🔊 Test 5: Searching for shows with complete audio in 1997...")
            result = await session.call_tool("search_shows_with_audio", {
                "audio_status": "complete",
                "year": 1997,
                "limit": 3
            })
            print(result.content[0].text)
            print()
            
            print("✅ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
