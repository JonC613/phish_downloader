#!/usr/bin/env python3
"""
Direct function test for enhanced features.
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_enrichment():
    """Test enhanced features directly."""
    print("🧪 Testing Enhanced Phish MCP Features")
    print("=" * 50)
    
    # Import and load data
    print("📂 Loading show data...")
    
    from mcp_server_enhanced import load_all_shows
    
    shows = load_all_shows()
    print(f"✅ Loaded {len(shows)} shows")
    
    # Count enriched shows
    enriched = sum(1 for show in shows if show.get('audio_status'))
    print(f"🎵 Enriched with phish.in data: {enriched} shows ({enriched/len(shows)*100:.1f}%)")
    
    # Show sample enriched data
    print("\n📊 Sample Enriched Shows:")
    count = 0
    for show in shows:
        if show.get('audio_status') and count < 5:
            date = show.get('date', 'Unknown')
            venue = show.get('venue', {}).get('name', 'Unknown')
            audio = show.get('audio_status', 'Unknown')
            tour = show.get('tour_name', 'Unknown')
            tracks = len(show.get('tracks', []))
            tags = len(show.get('tags', []))
            
            audio_icon = {"complete": "🎵", "partial": "⚠️", "missing": "❌"}.get(audio, "❓")
            
            print(f"  {date} - {venue}")
            print(f"    🔊 Audio: {audio} {audio_icon}")
            print(f"    🎪 Tour: {tour}")
            print(f"    🎵 Tracks: {tracks}")
            if tags > 0:
                print(f"    🏷️ Tags: {tags}")
            
            # Show MP3 availability
            if show.get('tracks'):
                mp3_count = sum(1 for t in show['tracks'] if t.get('mp3_url'))
                print(f"    🔗 MP3s available: {mp3_count}/{tracks}")
            print()
            
            count += 1
    
    # Test audio status breakdown
    print("🔊 Audio Status Breakdown:")
    audio_stats = {}
    for show in shows:
        status = show.get('audio_status', 'unknown')
        audio_stats[status] = audio_stats.get(status, 0) + 1
    
    for status, count in sorted(audio_stats.items()):
        icon = {"complete": "🎵", "partial": "⚠️", "missing": "❌", "unknown": "❓"}.get(status, "❓")
        percentage = count/len(shows)*100
        print(f"  {icon} {status.title()}: {count:,} ({percentage:.1f}%)")
    
    # Test tour information  
    print("\n🎪 Tour Information:")
    tours = set()
    for show in shows:
        if show.get('tour_name'):
            tours.add(show['tour_name'])
    
    print(f"  Total unique tours: {len(tours)}")
    if tours:
        print("  Sample tours:")
        for tour in sorted(tours)[:10]:
            print(f"    • {tour}")
        if len(tours) > 10:
            print(f"    ... and {len(tours) - 10} more")
    
    print("\n✅ Enhanced features test completed!")

if __name__ == "__main__":
    asyncio.run(test_enrichment())