#!/usr/bin/env python3
"""
Client for phish.in API v2.

Fetches comprehensive Phish show data including audio status, tracks with MP3 URLs,
tags, tour information, and venue coordinates.

API: https://phish.in/api/v2
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from urllib.error import URLError
from urllib.request import urlopen

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://phish.in/api/v2"


def fetch_json(endpoint: str, params: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch JSON from phish.in API with error handling.
    
    Args:
        endpoint: API endpoint (e.g., "/shows/2024-12-31")
        params: Query parameters as dict
        
    Returns:
        Parsed JSON response or None on error
    """
    url = f"{BASE_URL}{endpoint}"
    
    if params:
        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{param_str}"
    
    try:
        logger.info(f"Fetching: {url}")
        with urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            time.sleep(0.5)  # Rate limiting
            return data
    except URLError as e:
        logger.error(f"API Error: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON Error: {e}")
        return None


def get_show(date: str) -> Optional[Dict[str, Any]]:
    """
    Fetch complete show data by date (YYYY-MM-DD format).
    
    Includes:
    - Setlist with track positions
    - Audio status and URLs
    - Venue details with coordinates
    - Tour information
    - Tags (debuts, special events, etc.)
    - Taper notes
    
    Args:
        date: Show date in YYYY-MM-DD format
        
    Returns:
        Complete show data dict or None
    """
    return fetch_json(f"/shows/{date}")


def get_all_shows(
    year: Optional[int] = None,
    venue_slug: Optional[str] = None,
    audio_status: str = "any",
    per_page: int = 100,
) -> List[Dict[str, Any]]:
    """
    Fetch all shows with optional filtering.
    
    Args:
        year: Filter by year
        venue_slug: Filter by venue slug
        audio_status: 'any', 'complete', 'partial', 'missing'
        per_page: Results per page (max 1000)
        
    Returns:
        List of show dicts
    """
    params = {
        "per_page": str(per_page),
        "audio_status": audio_status,
        "sort": "date:asc",
    }
    
    if year:
        params["year"] = str(year)
    if venue_slug:
        params["venue_slug"] = venue_slug
    
    shows = []
    page = 1
    
    while True:
        params["page"] = str(page)
        data = fetch_json("/shows", params)
        
        if not data:
            break
        
        shows.extend(data)
        
        # Check if we got less than per_page items (end of results)
        if len(data) < per_page:
            break
        
        page += 1
        logger.info(f"Fetched {len(shows)} shows so far...")
    
    logger.info(f"Total shows fetched: {len(shows)}")
    return shows


def get_venue(slug: str) -> Optional[Dict[str, Any]]:
    """
    Fetch venue details by slug.
    
    Includes:
    - Coordinates (lat/long)
    - All aliases
    - Show count
    - Shows with audio count
    
    Args:
        slug: Venue slug
        
    Returns:
        Venue data dict or None
    """
    return fetch_json(f"/venues/{slug}")


def get_song(slug: str) -> Optional[Dict[str, Any]]:
    """
    Fetch song details by slug.
    
    Includes:
    - Performance count
    - Audio availability
    - Performance gaps
    - Original vs. cover status
    
    Args:
        slug: Song slug
        
    Returns:
        Song data dict or None
    """
    return fetch_json(f"/songs/{slug}")


def get_tour(slug: str) -> Optional[Dict[str, Any]]:
    """
    Fetch tour details including all shows.
    
    Args:
        slug: Tour slug
        
    Returns:
        Tour data dict with shows or None
    """
    return fetch_json(f"/tours/{slug}")


def search(
    term: str,
    scope: str = "all",
    audio_status: str = "any",
) -> Optional[Dict[str, List[Dict[str, Any]]]]:
    """
    Search across shows, songs, venues, tours, and tags.
    
    Args:
        term: Search term (min 3 chars)
        scope: 'all', 'shows', 'songs', 'venues', 'tours', 'tracks', 'tags'
        audio_status: 'any', 'complete', 'partial', 'missing'
        
    Returns:
        Dict with keys: exact_show, other_shows, songs, venues, tracks, tags, playlists
    """
    params = {
        "audio_status": audio_status,
        "scope": scope,
    }
    return fetch_json(f"/search/{term}", params)


def get_years() -> Optional[List[Dict[str, Any]]]:
    """
    Fetch all years with era designations and statistics.
    
    Returns:
        List of year dicts with period, shows_count, era, etc.
    """
    return fetch_json("/years")


def get_tracks(
    year: Optional[int] = None,
    song_slug: Optional[str] = None,
    audio_status: str = "complete",
    per_page: int = 100,
) -> List[Dict[str, Any]]:
    """
    Fetch tracks with MP3 URLs.
    
    Includes:
    - Direct MP3 URLs
    - Jam timestamps
    - Track-level tags
    
    Args:
        year: Filter by year
        song_slug: Filter by song
        audio_status: 'any', 'complete', 'partial', 'missing'
        per_page: Results per page
        
    Returns:
        List of track dicts with MP3 URLs
    """
    params = {
        "per_page": str(per_page),
        "audio_status": audio_status,
        "sort": "date:desc",
    }
    
    if year:
        params["year"] = str(year)
    if song_slug:
        params["song_slug"] = song_slug
    
    tracks = []
    page = 1
    
    while True:
        params["page"] = str(page)
        data = fetch_json("/tracks", params)
        
        if not data:
            break
        
        tracks.extend(data)
        
        if len(data) < per_page:
            break
        
        page += 1
    
    return tracks


def get_statistics() -> Optional[Dict[str, Any]]:
    """
    Get database statistics.
    
    Returns:
        Stats dict with total shows, venues, songs, etc.
    """
    # Stats are included in the API info, but we can infer from a /shows request
    years = get_years()
    if years:
        total_shows = sum(y.get("shows_count", 0) for y in years)
        return {"total_shows": total_shows, "years_data": years}
    return None


if __name__ == "__main__":
    # Quick test
    print("Testing phish.in API client...")
    
    # Test 1: Get a specific show
    show = get_show("2024-12-31")
    if show:
        print(f"[OK] Got show: {show.get('date')} at {show.get('venue_name')}")
        if show.get('tracks'):
            print(f"   Tracks: {len(show['tracks'])}")
            for track in show['tracks'][:3]:
                print(f"   - {track.get('title')} ({track.get('mp3_url', 'no audio')[:50]}...)")
    
    # Test 2: Get years
    years = get_years()
    if years:
        print(f"[OK] Got {len(years)} year periods")
        print(f"   Latest: {years[-1].get('period')} - {years[-1].get('era')}")
    
    # Test 3: Search
    results = search("trey", scope="all")
    if results:
        print(f"[OK] Search results: {len(results)} categories returned")
