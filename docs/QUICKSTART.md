# Quick Start Guide

## Installation

```bash
cd phish_downloader
python -m pip install pytest  # for testing
```

## Try It Now

### 1. Format a Single Show

```bash
# Format the example file
python -m phish_json_formatter --in test_input.json --out my_normalized_show.json

# View the result
cat my_normalized_show.json
```

### 2. Batch Format Multiple Shows

```bash
# Format all shows in a directory
python -m phish_json_formatter --in test_raw_shows --out my_normalized_shows

# Check the results
ls my_normalized_shows/
```

### 3. Run the Tests

```bash
python -m pytest tests/ -v
```

Expected output: **16 passed** ✓

## API Usage

```python
from phish_json_formatter import normalize_show, format_file, format_dir
from pathlib import Path
import json

# Load raw JSON
with open("raw_show.json") as f:
    raw = json.load(f)

# Option A: Normalize in-memory
normalized = normalize_show(raw, "raw_show.json")
print(json.dumps(normalized, indent=2))

# Option B: Format a file
format_file(Path("raw_show.json"), Path("normalized_show.json"))

# Option C: Batch format a directory
format_dir(Path("raw_shows"), Path("normalized_shows"))
```

## What Gets Normalized

**Input:** Raw JSON with varying field names and structure  
**Output:** Clean, stable JSON with predictable schema

Keys that get extracted and normalized:
- Show metadata: date, venue name, city, state, country, lat/lon, tour
- Setlist: set names, song titles, transitions (→), notes per song
- Notes: curated bullets, fan comments with source/author/date/text
- Facts: labeled facts with optional details
- Sources: tracking data sources
- Provenance: filename, API, download timestamp, generation info

## File Format

All output JSON files have:
- UTF-8 encoding
- 2-space indentation
- Sorted keys (stable diffs)
- Trailing newline
- Version 2.0 schema

## Field Mapping

The formatter automatically detects these raw field names:

| Data | Raw Keys |
|------|----------|
| Date | date, showDate, show_date, event_date, eventDate |
| Venue | venue, venueName, venue_name, location |
| City | city, venue_city, venueCity |
| State | state, province, venue_state, venueState |
| Country | country, venue_country, venueCountry |
| Latitude | lat, latitude, venue_lat, venueLat |
| Longitude | lon, longitude, lng, venue_lon, venueLon |
| Tour | tour, tour_name, tourName |
| Setlist | setlist, sets, song_sets, songSets |

## Common Use Cases

### Case 1: Process API Downloads

```bash
# After downloading shows from API, normalize them
python -m phish_json_formatter --in ./api_downloads --out ./normalized
```

### Case 2: Prepare for Database Import

```python
import json
from pathlib import Path
from phish_json_formatter import format_dir

# Format all raw shows
format_dir(Path("raw"), Path("normalized"))

# Load into your database
for file in Path("normalized").rglob("*.json"):
    with open(file) as f:
        show_data = json.load(f)
    # db.insert(show_data)  # Your DB code here
```

### Case 3: Validate Incoming Data

```python
from phish_json_formatter import normalize_show, validate_normalized

try:
    normalized = normalize_show(raw_data, filename)
    validate_normalized(normalized)
    print("✓ Valid show data")
except ValueError as e:
    print(f"✗ Invalid data: {e}")
```

## Troubleshooting

### Missing required field errors

The formatter requires:
- **date**: In YYYY-MM-DD format (e.g., 2024-01-01)
- **venue name**: Venue's official name
- **city**: City where show happened

Make sure your raw JSON has these fields (or compatible variants).

### Character encoding issues

All output is UTF-8. If you see encoding errors, ensure your input is valid UTF-8 JSON.

### Dates in wrong format?

The formatter accepts dates as:
- ISO format: "2024-01-01" ✓
- Timestamp: "2024-01-01T00:00:00Z" ✓ (takes first 10 chars)

It always outputs: "YYYY-MM-DD"

## Next Steps

1. ✓ Run the tests: `pytest tests/ -v`
2. ✓ Format your own show files
3. ✓ Integrate into your workflow
4. ✓ Read [README.md](README.md) for full documentation
5. ✓ Check [IMPLEMENTATION.md](IMPLEMENTATION.md) for technical details

Happy formatting! 🎵
