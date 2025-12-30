#!/usr/bin/env python3
"""
Enhanced MCP Server for Phish Shows Database with phish.in API Integration.

Provides comprehensive show search capabilities including:
- Original tools: search shows, get show details, search songs, get statistics  
- New enriched tools: search by audio status, get audio info with MP3 URLs
- Supports both normalized and enriched show data
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List
import asyncio
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp import types
from mcp.types import Tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory paths
NORMALIZED_SHOWS_DIR = Path(__file__).parent / "normalized_shows"
ENRICHED_SHOWS_DIR = Path(__file__).parent / "enriched_shows"

# Global variables for cached data
ALL_SHOWS: List[Dict[str, Any]] = []


def load_all_shows() -> List[Dict[str, Any]]:
    """
    Load all show data from JSON files.
    Prefers enriched shows if available, falls back to normalized shows.
    """
    shows = []
    
    # Get list of enriched files
    if ENRICHED_SHOWS_DIR.exists():
        enriched_files = set(f.name for f in ENRICHED_SHOWS_DIR.glob("*.json"))
    else:
        enriched_files = set()
    
    for json_file in sorted(NORMALIZED_SHOWS_DIR.glob("*.json")):
        try:
            # Use enriched version if available
            if json_file.name in enriched_files:
                data_file = ENRICHED_SHOWS_DIR / json_file.name
            else:
                data_file = json_file
            
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle both nested and flat structures
            if "show" in data and "setlist" in data:
                # Merge nested structure
                show_data = data["show"]
                show_data["setlist"] = data["setlist"]
                shows.append(show_data)
            elif "show" in data:
                # Already merged or new enriched format
                if "tracks" in data:
                    # New enriched format with tracks
                    show_data = data["show"]
                    show_data["tracks"] = data["tracks"]
                    shows.append(show_data)
                else:
                    shows.append(data["show"])
            else:
                # Flat structure
                shows.append(data)
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error loading {json_file}: {e}")
            
    logger.info(f"Loaded {len(shows)} shows ({len(enriched_files)} enriched)")
    return shows


class Tools:
    SearchShows = "search_shows"
    GetShowDetails = "get_show_details" 
    SearchSongs = "search_songs"
    SearchShowsByAudio = "search_shows_by_audio"
    GetShowAudioInfo = "get_show_audio_info"
    GetStatistics = "get_statistics"


# Handler functions
async def handle_search_shows(args: Dict[str, Any]) -> List[types.TextContent]:
    """Search shows by year, venue, city, state, or tour."""
    year = args.get("year")
    venue = args.get("venue", "").lower()
    city = args.get("city", "").lower()
    state = args.get("state", "").lower()
    tour = args.get("tour", "").lower()
    limit = args.get("limit", 50)
    
    matching_shows = []
    for show in ALL_SHOWS:
        # Year filter
        if year and str(year) not in show.get("date", ""):
            continue
            
        # Venue filter
        if venue and venue not in show.get("venue", {}).get("name", "").lower():
            continue
            
        # City filter  
        if city and city not in show.get("venue", {}).get("city", "").lower():
            continue
            
        # State filter
        if state and state not in show.get("venue", {}).get("state", "").lower():
            continue
            
        # Tour filter (if enriched data available)
        if tour and tour not in show.get("tour_name", "").lower():
            continue
            
        matching_shows.append({
            "date": show.get("date"),
            "venue": show.get("venue", {}).get("name", "Unknown"),
            "city": show.get("venue", {}).get("city", "Unknown"),
            "state": show.get("venue", {}).get("state", ""),
            "tour_name": show.get("tour_name", "Unknown"),
            "audio_status": show.get("audio_status", "unknown")
        })
        
        if len(matching_shows) >= limit:
            break
    
    if not matching_shows:
        return [types.TextContent(
            type="text",
            text="No shows found matching your criteria."
        )]
    
    # Format results
    results = [f"Found {len(matching_shows)} shows:"]
    
    for show in matching_shows:
        location = f"{show['city']}"
        if show['state']:
            location += f", {show['state']}"
            
        audio_icon = {"complete": "🎵", "partial": "⚠️", "missing": "❌", "unknown": "❓"}.get(show['audio_status'], "❓")
        
        results.append(
            f"  {show['date']} - {show['venue']} ({location}) {audio_icon}"
        )
    
    return [types.TextContent(type="text", text="\\n".join(results))]


async def handle_get_show_details(args: Dict[str, Any]) -> List[types.TextContent]:
    """Get complete setlist and details for a specific show."""
    target_date = args.get("date")
    
    # Find the show
    show = None
    for s in ALL_SHOWS:
        if s.get("date") == target_date:
            show = s
            break
    
    if not show:
        return [types.TextContent(
            type="text",
            text=f"Show not found for date: {target_date}"
        )]
    
    # Build response
    venue = show.get("venue", {})
    results = [
        f"🎪 Show: {target_date}",
        f"📍 Venue: {venue.get('name', 'Unknown')} - {venue.get('city', 'Unknown')}"
    ]
    
    # Add tour info if available (from enriched data)
    if show.get("tour_name"):
        results.append(f"🎭 Tour: {show['tour_name']}")
    
    if show.get("audio_status"):
        audio_icon = {"complete": "🎵", "partial": "⚠️", "missing": "❌"}.get(show['audio_status'], "❓")
        results.append(f"🔊 Audio: {show['audio_status']} {audio_icon}")
    
    # Show setlist/tracks
    if show.get("tracks"):
        # New enriched format with tracks
        results.append("\\n📋 Setlist:")
        current_set = None
        for track in show["tracks"]:
            set_name = track.get("set_name", "Unknown")
            if set_name != current_set:
                results.append(f"\\n  📀 {set_name}:")
                current_set = set_name
            
            title = track.get("title", "Unknown")
            position = track.get("position", "?")
            results.append(f"    {position}. {title}")
            
    elif show.get("setlist"):
        # Original format
        results.append("\\n📋 Setlist:")
        for i, set_data in enumerate(show["setlist"], 1):
            if isinstance(set_data, dict):
                set_name = set_data.get("name", f"Set {i}")
                results.append(f"\\n  📀 {set_name}:")
                
                songs = set_data.get("songs", [])
                for j, song in enumerate(songs, 1):
                    if isinstance(song, dict):
                        song_title = song.get("title", "Unknown")
                    else:
                        song_title = str(song)
                    results.append(f"    {j}. {song_title}")
    
    return [types.TextContent(type="text", text="\\n".join(results))]


async def handle_search_songs(args: Dict[str, Any]) -> List[types.TextContent]:
    """Search for all performances of a specific song."""
    target_song = args.get("song", "").lower()
    limit = args.get("limit", 100)
    
    performances = []
    for show in ALL_SHOWS:
        show_date = show.get("date", "Unknown")
        
        # Check tracks first (enriched format)
        if show.get("tracks"):
            for track in show["tracks"]:
                song_title = track.get("title", "")
                if target_song in song_title.lower():
                    performances.append({
                        "date": show_date,
                        "song": song_title,
                        "set": track.get("set_name", "Unknown"),
                        "venue": show.get("venue", {}).get("name", "Unknown"),
                        "city": show.get("venue", {}).get("city", "Unknown")
                    })
        
        # Check original setlist format
        elif show.get("setlist"):
            for set_data in show["setlist"]:
                if isinstance(set_data, dict) and "songs" in set_data:
                    set_name = set_data.get("name", "Unknown Set")
                    for song in set_data["songs"]:
                        if isinstance(song, dict):
                            song_title = song.get("title", "")
                        else:
                            song_title = str(song)
                            
                        if target_song in song_title.lower():
                            performances.append({
                                "date": show_date,
                                "song": song_title,
                                "set": set_name,
                                "venue": show.get("venue", {}).get("name", "Unknown"),
                                "city": show.get("venue", {}).get("city", "Unknown")
                            })
        
        if len(performances) >= limit:
            break
    
    if not performances:
        return [types.TextContent(
            type="text",
            text=f"No performances found for '{target_song}'"
        )]
    
    # Format results
    results = [f"Found {len(performances)} performances of songs matching '{target_song}':"]
    
    for perf in performances:
        results.append(
            f"  {perf['date']} ({perf['set']}) - {perf['venue']}, {perf['city']}"
        )
    
    return [types.TextContent(type="text", text="\\n".join(results))]


async def handle_search_shows_by_audio(args: Dict[str, Any]) -> List[types.TextContent]:
    """Search shows by audio availability status (enriched data only)."""
    audio_status = args.get("audio_status")
    tour_name = args.get("tour_name", "").lower()
    has_tags = args.get("has_tags", False)
    limit = args.get("limit", 50)
    
    matching_shows = []
    for show in ALL_SHOWS:
        # Check audio status (from enriched data)
        show_audio = show.get("audio_status")
        if show_audio != audio_status:
            continue
            
        # Filter by tour if specified
        if tour_name and tour_name not in show.get("tour_name", "").lower():
            continue
            
        # Filter by tags if specified
        if has_tags and not show.get("tags"):
            continue
            
        matching_shows.append({
            "date": show.get("date"),
            "venue": show.get("venue", {}).get("name", "Unknown"),
            "city": show.get("venue", {}).get("city", "Unknown"),
            "audio_status": show_audio,
            "tour_name": show.get("tour_name", "Unknown"),
            "tags": [tag.get("name", "") for tag in show.get("tags", [])],
            "track_count": len(show.get("tracks", []))
        })
        
        if len(matching_shows) >= limit:
            break
    
    if not matching_shows:
        return [types.TextContent(
            type="text",
            text=f"No shows found with audio status '{audio_status}'"
        )]
    
    # Format results
    audio_icon = {"complete": "🎵", "partial": "⚠️", "missing": "❌"}.get(audio_status, "❓")
    results = [f"Found {len(matching_shows)} shows with audio status '{audio_status}' {audio_icon}:"]
    
    for show in matching_shows:
        tags_str = f" 🏷️{', '.join(show['tags'])}" if show['tags'] else ""
        results.append(
            f"  {show['date']} - {show['venue']} ({show['city']}) - {show['tour_name']} - {show['track_count']} tracks{tags_str}"
        )
    
    return [types.TextContent(type="text", text="\\n".join(results))]


async def handle_get_show_audio_info(args: Dict[str, Any]) -> List[types.TextContent]:
    """Get detailed audio information for a specific show including MP3 URLs."""
    target_date = args.get("date")
    
    # Find the show
    show = None
    for s in ALL_SHOWS:
        if s.get("date") == target_date:
            show = s
            break
    
    if not show:
        return [types.TextContent(
            type="text",
            text=f"Show not found for date: {target_date}"
        )]
    
    # Check if this is an enriched show
    if not show.get("audio_status"):
        return [types.TextContent(
            type="text",
            text=f"No audio information available for {target_date}. This show may not be enriched with phish.in data."
        )]
    
    # Build audio info response
    venue = show.get("venue", {})
    audio_icon = {"complete": "🎵", "partial": "⚠️", "missing": "❌"}.get(show['audio_status'], "❓")
    
    results = [
        f"🎵 Audio Information for {target_date}",
        f"📍 Venue: {venue.get('name', 'Unknown')} - {venue.get('city', 'Unknown')}",
        f"🎪 Tour: {show.get('tour_name', 'Unknown')}",
        f"🔊 Audio Status: {show.get('audio_status', 'Unknown')} {audio_icon}",
    ]
    
    if show.get('duration_ms'):
        duration_min = show['duration_ms'] // 1000 // 60
        results.append(f"⏱️  Duration: {duration_min} minutes")
    
    if show.get('likes_count'):
        results.append(f"💙 Likes: {show['likes_count']:,}")
    
    # Add tags if present
    tags = show.get("tags", [])
    if tags:
        tag_info = []
        for tag in tags:
            name = tag.get("name", "")
            desc = tag.get("description", "")
            if name:
                tag_info.append(f"{name}" + (f" ({desc})" if desc and desc != name else ""))
        if tag_info:
            results.append(f"🏷️ Tags: {', '.join(tag_info)}")
    
    # Add track information with MP3 URLs
    tracks = show.get("tracks", [])
    if tracks:
        results.append(f"\\n🎵 Tracks ({len(tracks)}):")
        
        current_set = None
        track_count = 0
        for track in tracks:
            if track_count >= 15:  # Limit to first 15 tracks for readability
                results.append(f"    ... and {len(tracks) - track_count} more tracks")
                break
                
            set_name = track.get("set_name", "Unknown")
            if set_name != current_set:
                results.append(f"\\n  📀 {set_name}:")
                current_set = set_name
            
            title = track.get("title", "Unknown")
            position = track.get("position", "?")
            
            # Duration info
            duration = track.get("duration_ms")
            duration_str = f" ({duration//1000//60}:{duration//1000%60:02d})" if duration else ""
            
            # MP3 availability
            mp3_url = track.get("mp3_url")
            mp3_str = " 🔗" if mp3_url else ""
            
            # Jam timing
            jam_start = track.get("jam_starts_at_second")
            jam_str = f" 🎸@{jam_start//60}:{jam_start%60:02d}" if jam_start else ""
            
            results.append(f"    {position}. {title}{duration_str}{mp3_str}{jam_str}")
            track_count += 1
    
    # Add download links if available
    if show.get("album_zip_url"):
        results.append(f"\\n📦 Full show download: Available")
    
    if show.get("album_cover_url"):
        results.append(f"🎨 Cover art: Available")
    
    # Add notes if available
    if show.get("taper_notes"):
        results.append(f"\\n📝 Taper notes: {show['taper_notes']}")
    
    return [types.TextContent(type="text", text="\\n".join(results))]


async def handle_get_statistics(args: Dict[str, Any] = None) -> List[types.TextContent]:
    """Get comprehensive database statistics including enriched data."""
    total_shows = len(ALL_SHOWS)
    
    # Count audio statuses
    audio_stats = {"complete": 0, "partial": 0, "missing": 0, "unknown": 0}
    enriched_count = 0
    
    for show in ALL_SHOWS:
        if show.get("audio_status"):
            enriched_count += 1
            status = show.get("audio_status")
            audio_stats[status] = audio_stats.get(status, 0) + 1
        else:
            audio_stats["unknown"] += 1
    
    # Get unique venues
    venues = set()
    for show in ALL_SHOWS:
        venue_name = show.get("venue", {}).get("name")
        if venue_name:
            venues.add(venue_name)
    
    # Get unique songs
    songs = set()
    for show in ALL_SHOWS:
        # Check both old setlist format and new tracks format
        setlist = show.get("setlist", [])
        tracks = show.get("tracks", [])
        
        for set_data in setlist:
            if isinstance(set_data, dict) and "songs" in set_data:
                for song in set_data["songs"]:
                    if isinstance(song, dict) and "title" in song:
                        songs.add(song["title"])
                    elif isinstance(song, str):
                        songs.add(song)
        
        for track in tracks:
            if isinstance(track, dict) and "title" in track:
                songs.add(track["title"])
    
    # Get tours from enriched shows
    tours = set()
    tagged_shows = 0
    for show in ALL_SHOWS:
        if show.get("tour_name"):
            tours.add(show["tour_name"])
        if show.get("tags"):
            tagged_shows += 1
    
    # Date range
    dates = [show.get("date") for show in ALL_SHOWS if show.get("date")]
    dates = [d for d in dates if d]  # Filter None values
    
    stats = [
        "🎪 Phish Show Database Statistics",
        f"📊 Total Shows: {total_shows:,}",
        f"🎵 Unique Songs: {len(songs):,}",
        f"🏛️  Unique Venues: {len(venues):,}",
        f"📅 Date Range: {min(dates) if dates else 'Unknown'} to {max(dates) if dates else 'Unknown'}",
        "",
        "🔊 Audio Information (phish.in enriched):",
        f"   📈 Enriched Shows: {enriched_count:,} ({enriched_count/total_shows*100:.1f}%)",
        f"   ✅ Complete Audio: {audio_stats['complete']:,}",
        f"   ⚠️  Partial Audio: {audio_stats['partial']:,}",
        f"   ❌ Missing Audio: {audio_stats['missing']:,}",
        f"   ❓ Unknown Status: {audio_stats['unknown']:,}",
        "",
        f"🎪 Tours: {len(tours):,} different tours",
        f"🏷️ Tagged Shows: {tagged_shows:,}"
    ]
    
    return [types.TextContent(type="text", text="\\n".join(stats))]


# Initialize the MCP server
server = Server("phish-shows-enhanced")


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List all available tools."""
    return [
        Tool(
            name=Tools.SearchShows.value,
            description="Search for shows by year, venue, city, state, or tour name",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "Year to filter by (optional)"},
                    "venue": {"type": "string", "description": "Venue name to search for (optional)"},
                    "city": {"type": "string", "description": "City to filter by (optional)"},
                    "state": {"type": "string", "description": "State to filter by (optional)"},
                    "tour": {"type": "string", "description": "Tour name to filter by (optional, enriched shows only)"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50}
                }
            }
        ),
        Tool(
            name=Tools.GetShowDetails.value,
            description="Get complete setlist and details for a specific show",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Show date in YYYY-MM-DD format"}
                },
                "required": ["date"]
            }
        ),
        Tool(
            name=Tools.SearchSongs.value,
            description="Search for all performances of a specific song",
            inputSchema={
                "type": "object",
                "properties": {
                    "song": {"type": "string", "description": "Song title to search for (partial matches allowed)"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 100}
                },
                "required": ["song"]
            }
        ),
        Tool(
            name=Tools.SearchShowsByAudio.value,
            description="Search for shows by audio availability status (requires enriched data)",
            inputSchema={
                "type": "object",
                "properties": {
                    "audio_status": {
                        "type": "string", 
                        "enum": ["complete", "partial", "missing"], 
                        "description": "Audio completeness status"
                    },
                    "tour_name": {"type": "string", "description": "Filter by tour name (optional)"},
                    "has_tags": {"type": "boolean", "description": "Only shows with special tags (optional)"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50}
                },
                "required": ["audio_status"]
            }
        ),
        Tool(
            name=Tools.GetShowAudioInfo.value,
            description="Get detailed audio information for a specific show including MP3 URLs and track details",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Show date in YYYY-MM-DD format"}
                },
                "required": ["date"]
            }
        ),
        Tool(
            name=Tools.GetStatistics.value,
            description="Get comprehensive database statistics including audio availability",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """Handle tool calls."""
    try:
        if name == Tools.SearchShows.value:
            return await handle_search_shows(arguments)
        elif name == Tools.GetShowDetails.value:
            return await handle_get_show_details(arguments)
        elif name == Tools.SearchSongs.value:
            return await handle_search_songs(arguments)
        elif name == Tools.SearchShowsByAudio.value:
            return await handle_search_shows_by_audio(arguments)
        elif name == Tools.GetShowAudioInfo.value:
            return await handle_get_show_audio_info(arguments)
        elif name == Tools.GetStatistics.value:
            return await handle_get_statistics(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Error in {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Main entry point."""
    global ALL_SHOWS
    
    # Load show data at startup
    logger.info("Loading show data...")
    ALL_SHOWS = load_all_shows()
    
    # Start the server
    async with app.create_session() as session:
        await session.run_server(
            server,
            InitializationOptions(
                server_name="phish-shows-enhanced",
                server_version="2.0.0",
                capabilities=server.get_capabilities()
            )
        )


if __name__ == "__main__":
    asyncio.run(main())