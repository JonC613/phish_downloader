#!/usr/bin/env python3
"""Test enrichment on famous shows"""
import json
from pathlib import Path
from test_api_enrichment import enrich_show

# Test some famous shows
test_dates = ['1995-12-31', '1997-11-17', '1999-12-31', '1990-04-22', '1993-07-31']

for date in test_dates:
    try:
        files = list(Path('normalized_shows').glob(f'{date}_*.json'))
        if not files:
            print(f"{date}: File not found")
            continue
            
        json_file = files[0]
        print(f"Testing {date} ({json_file.name})...")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            show = json.load(f)
        
        enriched = enrich_show(show)
        
        if enriched.get('show', {}).get('audio_status'):
            audio = enriched['show']['audio_status']
            tour = enriched['show'].get('tour_name', 'Unknown')
            tags = enriched['show'].get('tags', [])
            tracks = len(enriched.get('tracks', []))
            
            print(f"  ✅ Audio: {audio}")
            print(f"  🎵 Tour: {tour}")
            print(f"  🏷️ Tags: {tags}")
            print(f"  🎵 Tracks: {tracks}")
            
            # Save enriched version
            output = Path('enriched_shows') / json_file.name
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(enriched, f, indent=2, ensure_ascii=False)
        else:
            print(f"  ❌ No API data available")
    except Exception as e:
        print(f"  Error: {e}")
    print()