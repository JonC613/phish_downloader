"""
MCP Server for Phish Shows Database
Provides tools to query Phish concert data from normalized JSON files.
"""

import json
import os
from pathlib import Path
from typing import Any, List, Dict, Optional
from datetime import datetime
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("phish-mcp-server")

# Path to normalized shows
NORMALIZED_SHOWS_DIR = Path(__file__).parent / "normalized_shows"

# Initialize MCP server
server = Server("phish-shows-server")


def load_all_shows() -> List[Dict[str, Any]]:
    """Load all normalized show JSON files."""
    shows = []
    if not NORMALIZED_SHOWS_DIR.exists():
        logger.warning(f"Shows directory not found: {NORMALIZED_SHOWS_DIR}")
        return shows
    
    for json_file in NORMALIZED_SHOWS_DIR.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Flatten structure: merge show metadata with setlist data
                if 'show' in data and 'setlist' in data:
                    show_data = data['show'].copy()
                    show_data['setlist'] = data['setlist']
                    show_data['notes'] = data.get('notes', {})
                    show_data['facts'] = data.get('facts', [])
                    shows.append(show_data)
        except Exception as e:
            logger.error(f"Error loading {json_file}: {e}")
    
    logger.info(f"Loaded {len(shows)} shows")
    return shows


def format_show_summary(show: Dict[str, Any]) -> str:
    """Format a show as a summary string."""
    date = show.get('date', 'Unknown')
    venue = show.get('venue', {}).get('name', 'Unknown Venue')
    city = show.get('venue', {}).get('city', '')
    state = show.get('venue', {}).get('state', '')
    location = f"{city}, {state}" if city and state else city or state or ''
    
    summary = f"📅 {date} - 📍 {venue}"
    if location:
        summary += f", {location}"
    
    return summary


def format_show_details(show: Dict[str, Any]) -> str:
    """Format a show with full setlist details."""
    lines = []
    
    # Header
    date = show.get('date', 'Unknown')
    venue = show.get('venue', {}).get('name', 'Unknown Venue')
    city = show.get('venue', {}).get('city', '')
    state = show.get('venue', {}).get('state', '')
    location = f"{city}, {state}" if city and state else city or state or ''
    
    lines.append(f"# 🎸 Phish - {date}")
    lines.append(f"**Venue:** {venue}")
    if location:
        lines.append(f"**Location:** {location}")
    
    tour = show.get('tour', {}).get('name')
    if tour:
        lines.append(f"**Tour:** {tour}")
    
    lines.append("")
    
    # Setlist
    setlist = show.get('setlist', {})
    if setlist:
        lines.append("## 🎵 Setlist")
        lines.append("")
        
        for set_num in sorted(setlist.keys()):
            songs = setlist[set_num]
            lines.append(f"**Set {set_num}** ({len(songs)} songs)")
            
            for i, song in enumerate(songs, 1):
                song_line = f"{i}. {song.get('title', 'Unknown')}"
                
                if song.get('transition'):
                    song_line += f" → {song['transition']}"
                
                notes = song.get('notes', [])
                if notes:
                    song_line += f" *({', '.join(notes)})*"
                
                lines.append(song_line)
            
            lines.append("")
    
    # Show notes
    notes = show.get('notes', [])
    if notes:
        lines.append("## 📝 Notes")
        lines.append("")
        for note in notes:
            if isinstance(note, dict):
                content = note.get('content', str(note))
            else:
                content = str(note)
            lines.append(f"- {content}")
        lines.append("")
    
    return "\n".join(lines)


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="search_shows",
            description="Search for Phish shows by year, venue, city, state, or tour. Returns matching shows with basic info.",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "Filter by year (e.g., 1997)",
                    },
                    "venue": {
                        "type": "string",
                        "description": "Search venue names (case-insensitive, partial match)",
                    },
                    "city": {
                        "type": "string",
                        "description": "Filter by city name",
                    },
                    "state": {
                        "type": "string",
                        "description": "Filter by state/province",
                    },
                    "tour": {
                        "type": "string",
                        "description": "Filter by tour name (partial match)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50,
                    },
                },
            },
        ),
        Tool(
            name="get_show_details",
            description="Get complete details for a specific show including full setlist, notes, and venue information. Use the show date in YYYY-MM-DD format.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Show date in YYYY-MM-DD format (e.g., '1997-12-31')",
                    },
                },
                "required": ["date"],
            },
        ),
        Tool(
            name="search_songs",
            description="Find all performances of a specific song across all shows. Returns list of shows where the song was played.",
            inputSchema={
                "type": "object",
                "properties": {
                    "song_title": {
                        "type": "string",
                        "description": "Song title to search for (case-insensitive, partial match)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 100)",
                        "default": 100,
                    },
                },
                "required": ["song_title"],
            },
        ),
        Tool(
            name="get_statistics",
            description="Get overall statistics about the Phish shows database including total shows, date ranges, venues, and songs.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution."""
    
    if name == "search_shows":
        shows = load_all_shows()
        
        # Apply filters
        year = arguments.get('year')
        venue = arguments.get('venue', '').lower()
        city = arguments.get('city', '').lower()
        state = arguments.get('state', '').lower()
        tour = arguments.get('tour', '').lower()
        limit = arguments.get('limit', 50)
        
        results = []
        for show in shows:
            # Year filter
            if year:
                show_year = int(show.get('date', '').split('-')[0]) if show.get('date') else None
                if show_year != year:
                    continue
            
            # Venue filter
            if venue:
                show_venue = show.get('venue', {}).get('name', '').lower()
                if venue not in show_venue:
                    continue
            
            # City filter
            if city:
                show_city = show.get('venue', {}).get('city', '').lower()
                if city not in show_city:
                    continue
            
            # State filter
            if state:
                show_state = show.get('venue', {}).get('state', '').lower()
                if state not in show_state:
                    continue
            
            # Tour filter
            if tour:
                show_tour = show.get('tour', {}).get('name', '').lower()
                if tour not in show_tour:
                    continue
            
            results.append(show)
            
            if len(results) >= limit:
                break
        
        # Format results
        if not results:
            return [TextContent(type="text", text="No shows found matching the criteria.")]
        
        lines = [f"Found {len(results)} show(s):", ""]
        for show in results:
            lines.append(format_show_summary(show))
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    elif name == "get_show_details":
        date = arguments.get('date')
        if not date:
            return [TextContent(type="text", text="Error: 'date' parameter is required")]
        
        shows = load_all_shows()
        
        # Find matching show
        for show in shows:
            if show.get('date') == date:
                return [TextContent(type="text", text=format_show_details(show))]
        
        return [TextContent(type="text", text=f"No show found for date: {date}")]
    
    elif name == "search_songs":
        song_title = arguments.get('song_title', '').lower()
        if not song_title:
            return [TextContent(type="text", text="Error: 'song_title' parameter is required")]
        
        limit = arguments.get('limit', 100)
        shows = load_all_shows()
        
        results = []
        for show in shows:
            setlist = show.get('setlist', {})
            found = False
            
            for set_num, songs in setlist.items():
                for song in songs:
                    if song_title in song.get('title', '').lower():
                        results.append({
                            'date': show.get('date'),
                            'venue': show.get('venue', {}).get('name'),
                            'city': show.get('venue', {}).get('city'),
                            'state': show.get('venue', {}).get('state'),
                            'set': set_num,
                            'song': song.get('title'),
                            'notes': song.get('notes', []),
                        })
                        found = True
                        break
                if found:
                    break
            
            if len(results) >= limit:
                break
        
        if not results:
            return [TextContent(type="text", text=f"No performances found for song: {song_title}")]
        
        lines = [f"Found {len(results)} performance(s) of songs matching '{song_title}':", ""]
        for perf in results:
            location = f"{perf['city']}, {perf['state']}" if perf.get('city') and perf.get('state') else perf.get('city') or perf.get('state') or ''
            line = f"📅 {perf['date']} - {perf['song']} (Set {perf['set']}) @ {perf['venue']}"
            if location:
                line += f", {location}"
            if perf.get('notes'):
                line += f" *({', '.join(perf['notes'])})*"
            lines.append(line)
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    elif name == "get_statistics":
        shows = load_all_shows()
        
        if not shows:
            return [TextContent(type="text", text="No shows found in database")]
        
        # Calculate stats
        total_shows = len(shows)
        
        # Date range
        dates = [show.get('date') for show in shows if show.get('date')]
        dates.sort()
        first_show = dates[0] if dates else "Unknown"
        last_show = dates[-1] if dates else "Unknown"
        
        # Years
        years = set()
        for show in shows:
            date = show.get('date', '')
            if date:
                year = date.split('-')[0]
                years.add(year)
        
        # Venues
        venues = set()
        for show in shows:
            venue = show.get('venue', {}).get('name')
            if venue:
                venues.add(venue)
        
        # Songs
        all_songs = set()
        total_song_performances = 0
        for show in shows:
            setlist = show.get('setlist', {})
            for songs in setlist.values():
                for song in songs:
                    title = song.get('title')
                    if title:
                        all_songs.add(title)
                        total_song_performances += 1
        
        lines = [
            "# 📊 Phish Shows Database Statistics",
            "",
            f"**Total Shows:** {total_shows}",
            f"**Date Range:** {first_show} to {last_show}",
            f"**Years Covered:** {len(years)} ({min(years) if years else 'N/A'} - {max(years) if years else 'N/A'})",
            f"**Unique Venues:** {len(venues)}",
            f"**Unique Songs:** {len(all_songs)}",
            f"**Total Song Performances:** {total_song_performances}",
        ]
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    logger.info("Starting Phish Shows MCP Server...")
    
    # Verify data directory exists
    if not NORMALIZED_SHOWS_DIR.exists():
        logger.error(f"Normalized shows directory not found: {NORMALIZED_SHOWS_DIR}")
        logger.error("Please run the downloader and formatter first.")
        return
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="phish-shows-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
