#!/usr/bin/env python3
"""Quick tests for the MCP server functionality"""

from mcp_server import load_all_shows
import json

def test_load():
    """Test loading shows"""
    print("Testing load_all_shows()...")
    shows = load_all_shows()
    print(f"✓ Loaded {len(shows)} shows")
    
    dates = [s['date'] for s in shows]
    print(f"✓ Date range: {min(dates)} to {max(dates)}")
    return shows

def test_search_by_year(shows):
    """Test year filtering"""
    print("\nTesting search by year (1997)...")
    year_shows = [s for s in shows if s['date'].startswith('1997')]
    print(f"✓ Found {len(year_shows)} shows in 1997")
    if year_shows:
        print(f"  First: {year_shows[0]['date']} - {year_shows[0]['venue']['name']}")
        print(f"  Last: {year_shows[-1]['date']} - {year_shows[-1]['venue']['name']}")

def test_search_by_venue(shows):
    """Test venue search"""
    print("\nTesting search by venue (Madison Square Garden)...")
    msg_shows = [s for s in shows 
                 if 'madison' in s['venue']['name'].lower() 
                 and 'square' in s['venue']['name'].lower()]
    print(f"✓ Found {len(msg_shows)} shows at Madison Square Garden")
    for show in msg_shows[:5]:
        print(f"  {show['date']} - {show['venue']['name']}")

def test_search_songs(shows):
    """Test song search"""
    print("\nTesting song search (You Enjoy Myself)...")
    yem_count = 0
    yem_dates = []
    
    for show in shows:
        for set_data in show.get('setlist', []):
            for song in set_data.get('songs', []):
                if 'enjoy' in song.get('title', '').lower():
                    yem_count += 1
                    yem_dates.append(show['date'])
                    break
    
    print(f"✓ Found {yem_count} performances of YEM")
    if yem_dates:
        print(f"  First: {min(yem_dates)}")
        print(f"  Last: {max(yem_dates)}")

def test_statistics(shows):
    """Test statistics"""
    print("\nTesting statistics...")
    
    unique_venues = set()
    unique_songs = set()
    
    for show in shows:
        venue_name = show['venue'].get('name', '')
        if venue_name:
            unique_venues.add(venue_name)
        
        for set_data in show.get('setlist', []):
            for song in set_data.get('songs', []):
                song_name = song.get('title', '')
                if song_name:
                    unique_songs.add(song_name)
    
    print(f"✓ Total shows: {len(shows)}")
    print(f"✓ Unique venues: {len(unique_venues)}")
    print(f"✓ Unique songs: {len(unique_songs)}")

def test_specific_show(shows):
    """Test getting specific show details"""
    print("\nTesting specific show (1995-12-31)...")
    target_date = "1995-12-31"
    show = next((s for s in shows if s['date'] == target_date), None)
    
    if show:
        print(f"✓ Found show: {show['date']} at {show['venue']['name']}")
        print(f"  Location: {show['venue'].get('city', '')}, {show['venue'].get('state', '')}")
        
        set_count = len(show.get('setlist', []))
        print(f"  Sets: {set_count}")
        
        for set_data in show.get('setlist', []):
            set_name = set_data.get('set', 'Unknown')
            songs = set_data.get('songs', [])
            print(f"  {set_name}: {len(songs)} songs")
    else:
        print(f"✗ Show not found: {target_date}")

if __name__ == "__main__":
    print("=" * 60)
    print("MCP Server Functionality Tests")
    print("=" * 60)
    
    shows = test_load()
    test_search_by_year(shows)
    test_search_by_venue(shows)
    test_search_songs(shows)
    test_specific_show(shows)
    test_statistics(shows)
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
