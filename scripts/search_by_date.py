#!/usr/bin/env python3
"""Quick search for shows on a specific date"""

import json
from pathlib import Path

shows = []
for json_file in Path('normalized_shows').glob('*.json'):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if 'show' in data and 'setlist' in data:
            show_data = data['show'].copy()
            show_data['setlist'] = data['setlist']
            shows.append(show_data)

# Filter for July 24 (7-24)
july_24_shows = [s for s in shows if s['date'][5:10] == '07-24']
print(f'Shows on July 24: {len(july_24_shows)}')
for show in sorted(july_24_shows, key=lambda s: s['date']):
    print(f"  {show['date']} - {show['venue']['name']}")
