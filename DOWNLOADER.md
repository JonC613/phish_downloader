# Phish Show Downloader

Downloads raw Phish show data from phish.net API v5 with setlist information.

## Installation

```bash
python -m pip install requests python-dotenv
```

## Configuration

Create a `.env` file in your project directory with your Phish.net API key:

```env
PHISHNET_API_KEY=YOUR_API_KEY_HERE
```

Get your API key from: https://phish.net/api

## Usage

### Command Line

Download all shows from a year:
```bash
python -m phishnet_downloader --year 1999
```

Download with a limit:
```bash
python -m phishnet_downloader --year 1999 --limit 10
```

Download to a custom directory:
```bash
python -m phishnet_downloader --year 1999 --output ./my_shows
```

Overwrite existing files:
```bash
python -m phishnet_downloader --year 1999 --overwrite
```

Download by date range:
```bash
python -m phishnet_downloader --start-date 1999-07-01 --end-date 1999-07-31
```

### Python API

```python
from phishnet_downloader import PhishNetDownloader
from pathlib import Path

# Create downloader
downloader = PhishNetDownloader(output_dir=Path("shows"))

# Download a year
files = downloader.download_year(1999)

# Download with limit
files = downloader.download_year(1999, overwrite=False)

# Download a date range
files = downloader.download_date_range("1999-07-01", "1999-07-31")

# Full control
files = downloader.download_shows(year=1999, limit=50, overwrite=True)
```

## Output Format

Downloaded files are saved as JSON with the following structure:

```json
{
  "showdate": "1999-07-24",
  "venue": "Great Woods Center for the Performing Arts",
  "city": "Mansfield",
  "state": "MA",
  "country": "USA",
  "tour_name": "Summer 1999 Tour",
  "setlist_notes": null,
  "sets": {
    "1": [
      {"song": "Divided Sky", "transition": false, "jam": false},
      {"song": "Maze", "transition": false}
    ],
    "2": [
      {"song": "Tweezer", "transition": true},
      {"song": "Jam", "transition": false}
    ],
    "e": [
      {"song": "Tweezer Reprise", "transition": false}
    ]
  },
  "downloaded_at": "2025-12-28T12:34:56Z",
  "api": "phish.net"
}
```

## Workflow: Download → Normalize → Process

```bash
# Step 1: Download raw shows from API
python -m phishnet_downloader --year 1999 --output ./raw_shows

# Step 2: Format/normalize the shows
python -m phish_json_formatter --in ./raw_shows --out ./normalized_shows

# Step 3: Process normalized data
# (use normalized_shows/ for your application)
```

Or in Python:

```python
from phishnet_downloader import PhishNetDownloader
from phish_json_formatter import format_dir
from pathlib import Path

# Download
downloader = PhishNetDownloader(output_dir=Path("raw_shows"))
downloader.download_year(1999)

# Normalize
format_dir(Path("raw_shows"), Path("normalized_shows"))

# Process normalized shows...
```

## Features

- Downloads show data with complete setlist information
- Organizes by year or date range
- Respects API rate limits (1 second between requests)
- Skips existing files unless --overwrite is used
- Saves comprehensive show metadata
- Compatible with phish_json_formatter for normalization

## Rate Limiting

The downloader automatically rate-limits requests to the API (1 second between requests). This can be customized:

```python
downloader = PhishNetDownloader(rate_limit_delay=0.5)  # 500ms between requests
```

## Error Handling

- Missing API key: Raises ValueError
- Network errors: Printed as warnings, skips that show
- Missing setlist data: Skipped (older shows may not have setlists)
- Invalid date formats: Returns empty list

## Examples

### Download the first 100 shows from 1999

```bash
python -m phishnet_downloader --year 1999 --limit 100
```

### Download a specific tour (July-August 1999)

```bash
python -m phishnet_downloader --start-date 1999-07-01 --end-date 1999-08-31
```

### Full pipeline: Download, normalize, and process

```python
from phishnet_downloader import PhishNetDownloader
from phish_json_formatter import format_dir, validate_normalized
from pathlib import Path
import json

# 1. Download
downloader = PhishNetDownloader(output_dir=Path("raw"))
downloader.download_year(1999)

# 2. Normalize
format_dir(Path("raw"), Path("normalized"))

# 3. Process
for show_file in Path("normalized").glob("*.json"):
    with open(show_file) as f:
        show = json.load(f)
    
    # Validate
    validate_normalized(show)
    
    # Process show data...
    print(f"{show['show']['date']} @ {show['show']['venue']['name']}")
```
