#!/usr/bin/env python3
"""Update all JSON files to use 'set' instead of 'name' in setlist."""

import json
from pathlib import Path

json_dir = Path('test_formatted_api_shows')

for json_file in sorted(json_dir.glob('*.json')):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Replace 'name' with 'set' in setlist
    for set_item in data.get('setlist', []):
        if 'name' in set_item:
            set_item['set'] = set_item.pop('name')
    
    # Write back with sorted keys
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')
    
    print(f'✓ Updated {json_file.name}')

print(f'\nAll {len(list(json_dir.glob("*.json")))} files updated!')
