#!/usr/bin/env python3
"""
Test script for enhanced MCP server with phish.in API integration.
"""
import json
import asyncio
from pathlib import Path
from mcp_server_enhanced import (
    load_all_shows,
    handle_search_shows_by_audio,
    handle_get_show_audio_info,
    handle_get_statistics,
)

async def test_enhanced_mcp():
    """Test the new enhanced MCP tools."""
    print("🧪 Testing Enhanced MCP Server")
    print("=" * 50)
    
    # Load data
    print("📂 Loading show data...")
    global ALL_SHOWS
    from mcp_server_enhanced import ALL_SHOWS
    if not ALL_SHOWS:
        import mcp_server_enhanced
        mcp_server_enhanced.ALL_SHOWS = load_all_shows()
        ALL_SHOWS = mcp_server_enhanced.ALL_SHOWS
    
    print(f"✅ Loaded {len(ALL_SHOWS)} shows")
    
    # Test 1: Search shows by audio status
    print("\n🔊 Test 1: Search shows with complete audio")
    result = await handle_search_shows_by_audio({
        "audio_status": "complete",
        "limit": 5
    })
    print(result[0].text)
    
    # Test 2: Get audio info for a specific enriched show
    print("\n🎵 Test 2: Get audio info for 2020-02-20")
    result = await handle_get_show_audio_info({
        "date": "2020-02-20"
    })
    print(result[0].text)
    
    # Test 3: Get enhanced statistics
    print("\n📊 Test 3: Enhanced statistics")
    result = await handle_get_statistics()
    print(result[0].text)
    
    # Test 4: Search by tour
    print("\n🎪 Test 4: Search shows by tour (enriched data)")
    result = await handle_search_shows_by_audio({
        "audio_status": "complete",
        "tour_name": "mexico",
        "limit": 3
    })
    print(result[0].text)
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_mcp())