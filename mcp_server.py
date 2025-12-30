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
                    # Include phish.in enriched data if present
                    if 'phish_in' in data:
                        show_data['phish_in'] = data['phish_in']
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
        Tool(
            name="search_shows_with_audio",
            description="Find shows that have audio available, with optional filtering by audio status (complete/partial/missing).",
            inputSchema={
                "type": "object",
                "properties": {
                    "audio_status": {
                        "type": "string",
                        "description": "Filter by audio status: 'complete', 'partial', 'missing', or 'any' (default)",
                        "enum": ["complete", "partial", "missing", "any"]
                    },
                    "year": {
                        "type": "integer",
                        "description": "Filter by year"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="get_show_audio_info",
            description="Get detailed audio information for a specific show including MP3 URLs and jam timestamps.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Show date in YYYY-MM-DD format"
                    }
                },
                "required": ["date"]
            }
        ),
        Tool(
            name="search_by_tags",
            description="Find shows by phish.in tags like debuts, bustouts, special events, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Tag to search for (partial match, case-insensitive)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)",
                        "default": 50
                    }
                },
                "required": ["tag"]
            }
        ),
        Tool(
            name="get_venue_coordinates",
            description="Get venue information including coordinates for mapping and proximity searches.",
            inputSchema={
                "type": "object",
                "properties": {
                    "venue_name": {
                        "type": "string",
                        "description": "Venue name to search for (partial match)"
                    }
                },
                "required": ["venue_name"]
            }
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
    
    elif name == "search_shows_with_audio":
        shows = load_all_shows()
        
        audio_status = arguments.get('audio_status', 'any').lower()
        year = arguments.get('year')
        limit = arguments.get('limit', 50)
        
        results = []
        for show in shows:
            # Skip shows without phish.in data
            if 'phish_in' not in show:
                continue
            
            # Year filter
            if year:
                show_year = int(show.get('date', '').split('-')[0]) if show.get('date') else None
                if show_year != year:
                    continue
            
            # Audio status filter
            show_audio_status = show.get('phish_in', {}).get('audio_status', '').lower()
            if audio_status != 'any' and show_audio_status != audio_status:
                continue
            
            results.append(show)
            
            if len(results) >= limit:
                break
        
        if not results:
            return [TextContent(type="text", text="No shows found with matching audio criteria.")]
        
        lines = [f"Found {len(results)} show(s) with audio:", ""]
        for show in results:
            audio_status = show.get('phish_in', {}).get('audio_status', 'unknown')
            audio_emoji = {"complete": "🎵", "partial": "🔸", "missing": "❌"}.get(audio_status, "❓")
            lines.append(f"{audio_emoji} {format_show_summary(show)}")
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    elif name == "get_show_audio_info":
        shows = load_all_shows()
        target_date = arguments.get('date')
        
        show = None
        for s in shows:
            if s.get('date') == target_date:
                show = s
                break
        
        if not show:
            return [TextContent(type="text", text=f"No show found for date: {target_date}")]
        
        if 'phish_in' not in show:
            return [TextContent(type="text", text=f"No phish.in audio data available for {target_date}")]
        
        lines = [f"# 🎵 Audio Info for {target_date}", ""]\n        
        phish_in = show['phish_in']
        
        # Audio status
        audio_status = phish_in.get('audio_status', 'unknown')
        audio_emoji = {"complete": "🎵", "partial": "🔸", "missing": "❌"}.get(audio_status, "❓")
        lines.append(f"**Audio Status:** {audio_emoji} {audio_status.title()}")
        
        # Likes
        if phish_in.get('likes_count') is not None:
            lines.append(f"**Community Likes:** {phish_in['likes_count']} ❤️")
        
        # Taper notes
        if phish_in.get('taper_notes'):
            lines.append(f"**Taper Notes:** {phish_in['taper_notes']}")
        
        lines.append("")
        
        # Track info with MP3 URLs and jams
        track_count = 0
        mp3_count = 0
        jam_count = 0
        
        for set_data in show.get('setlist', []):
            set_num = set_data.get('set', 'Unknown')
            lines.append(f"## Set {set_num}")
            
            for song in set_data.get('songs', []):
                track_count += 1
                title = song.get('title', 'Unknown')
                line_parts = [f"• {title}"]
                
                # MP3 URL
                if song.get('mp3_url'):
                    mp3_count += 1
                    line_parts.append("🎧")
                
                # Jam timestamps
                if song.get('jam_starts_at_second'):
                    jam_count += 1
                    jam_start = song['jam_starts_at_second']
                    jam_end = song.get('jam_ends_at_second')
                    if jam_end:
                        duration = jam_end - jam_start
                        line_parts.append(f"🎸 Jam: {jam_start}s-{jam_end}s ({duration}s)")
                    else:
                        line_parts.append(f"🎸 Jam starts: {jam_start}s")
                
                # Track tags
                if song.get('track_tags'):
                    tags = [tag.get('name', tag) if isinstance(tag, dict) else str(tag) 
                           for tag in song['track_tags']]
                    line_parts.append(f"🏷️ {', '.join(tags)}")
                
                lines.append(" ".join(line_parts))
        
        lines.extend(["", f"**Summary:** {track_count} tracks, {mp3_count} with audio, {jam_count} with jams"])
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    elif name == "search_by_tags":
        shows = load_all_shows()
        tag_query = arguments.get('tag', '').lower()
        limit = arguments.get('limit', 50)
        
        results = []
        for show in shows:
            if 'phish_in' not in show:
                continue
            
            tags = show.get('phish_in', {}).get('tags', [])
            for tag in tags:
                tag_name = tag.get('name', str(tag)) if isinstance(tag, dict) else str(tag)
                if tag_query in tag_name.lower():
                    results.append({
                        'show': show,
                        'matching_tags': [t for t in tags 
                                        if tag_query in (t.get('name', str(t)) if isinstance(t, dict) else str(t)).lower()]
                    })
                    break
            
            if len(results) >= limit:
                break
        
        if not results:
            return [TextContent(type="text", text=f"No shows found with tags matching: {tag_query}")]
        
        lines = [f"Found {len(results)} show(s) with tags matching '{tag_query}':", ""]
        for result in results:
            show = result['show']
            tags = result['matching_tags']
            tag_names = [tag.get('name', str(tag)) if isinstance(tag, dict) else str(tag) for tag in tags]
            lines.append(f"🏷️ {format_show_summary(show)}")
            lines.append(f"   Tags: {', '.join(tag_names)}")
            lines.append("")
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    elif name == "get_venue_coordinates":
        shows = load_all_shows()
        venue_query = arguments.get('venue_name', '').lower()
        
        venue_info = {}
        for show in shows:
            if 'phish_in' not in show:
                continue
            
            venue_name = show.get('venue', {}).get('name', '')
            if venue_query not in venue_name.lower():
                continue
            
            venue_data = show.get('phish_in', {}).get('venue', {})
            if venue_data.get('latitude') and venue_data.get('longitude'):
                key = f"{venue_name}|{show.get('venue', {}).get('city', '')}|{show.get('venue', {}).get('state', '')}"
                if key not in venue_info:
                    venue_info[key] = {
                        'name': venue_name,
                        'city': show.get('venue', {}).get('city', ''),
                        'state': show.get('venue', {}).get('state', ''),
                        'latitude': venue_data['latitude'],
                        'longitude': venue_data['longitude'],
                        'shows_count': venue_data.get('shows_count', 0),
                        'slug': venue_data.get('slug', ''),
                    }
        
        if not venue_info:
            return [TextContent(type="text", text=f"No venue coordinates found for: {venue_query}")]
        
        lines = [f"Found {len(venue_info)} venue(s) matching '{venue_query}':", ""]
        for info in venue_info.values():
            location = f"{info['city']}, {info['state']}" if info['city'] and info['state'] else info['city'] or info['state']
            lines.append(f"📍 **{info['name']}**")
            if location:
                lines.append(f"   Location: {location}")
            lines.append(f"   Coordinates: {info['latitude']}, {info['longitude']}")
            if info['shows_count']:
                lines.append(f"   Total shows: {info['shows_count']}")
            lines.append("")
        
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
