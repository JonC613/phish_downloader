# Phish Show Download & Format Pipeline

Complete solution for downloading Phish shows from the API and normalizing them to a consistent schema.

## Overview

```
                    ┌─────────────────────────────────────┐
                    │   Phish.net API v5                 │
                    │ (phish.net/api/v5)                 │
                    └────────────────┬────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────┐
│ PhishNetDownloader                                          │
│ • Downloads by year or date range                          │
│ • Fetches full setlist for each show                       │
│ • Rate-limited (1 sec between requests)                    │
│ • Saves raw JSON files                                     │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ raw_shows/*.json
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Phish JSON Formatter                                         │
│ • Normalizes field names                                    │
│ • Validates required fields                                │
│ • Creates consistent schema (v2.0)                         │
│ • Tracks provenance                                         │
│ • Ensures sorted keys for clean diffs                      │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ normalized_shows/*.json
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Your Application                                             │
│ • Process normalized show data                             │
│ • Import into database                                      │
│ • Build API endpoints                                       │
│ • Generate reports                                          │
└──────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Download Shows from API

```bash
# Download all shows from 1999
python -m phishnet_downloader --year 1999 --output ./raw_shows

# Or download a date range
python -m phishnet_downloader --start-date 1999-07-01 --end-date 1999-08-31 --output ./raw_shows
```

### 2. Normalize to Standard Schema

```bash
# Format all raw shows
python -m phish_json_formatter --in ./raw_shows --out ./normalized_shows
```

### 3. Use the Data

All normalized shows now have consistent structure:

```json
{
  "schema_version": "2.0",
  "show": {
    "id": "1999-07-24_great-woods_mansfield",
    "date": "1999-07-24",
    "tour": "Summer 1999",
    "venue": {
      "name": "Great Woods Center for the Performing Arts",
      "city": "Mansfield",
      "state": "MA",
      "country": "USA",
      "lat": 42.0,
      "lon": -71.4
    }
  },
  "setlist": [
    {
      "name": "Set 1",
      "songs": [
        {"title": "Divided Sky", "transition": null, "notes": []},
        {"title": "Maze", "transition": null, "notes": []}
      ]
    },
    {
      "name": "Encore",
      "songs": [
        {"title": "Tweezer Reprise", "transition": null, "notes": []}
      ]
    }
  ],
  "notes": {"curated": [], "fan_comments": []},
  "facts": [],
  "sources": [],
  "provenance": {
    "raw_input": {"filename": "...", "api": "phish.net", "downloaded_at": "..."},
    "generated_at": "...",
    "generator": "phish-json-formatter"
  }
}
```

## Features

### PhishNetDownloader

- ✓ Download by year or date range
- ✓ Complete setlist information
- ✓ Automatic rate limiting
- ✓ Skip existing files option
- ✓ Batch processing with progress
- ✓ Clear error handling
- ✓ Metadata tracking (API, download time)

### Phish JSON Formatter

- ✓ Flexible field mapping for various API schemas
- ✓ Consistent, validated schema (v2.0)
- ✓ Setlist structure preservation
- ✓ Sorted keys for clean diffs
- ✓ UTF-8 encoding
- ✓ Trailing newlines
- ✓ Comprehensive validation
- ✓ Provenance tracking

## API Reference

### Download Shows

```python
from phishnet_downloader import PhishNetDownloader
from pathlib import Path

downloader = PhishNetDownloader(
    api_key="YOUR_KEY",  # or use PHISHNET_API_KEY from .env
    output_dir=Path("shows"),
    rate_limit_delay=1.0  # seconds between requests
)

# By year
files = downloader.download_year(1999)

# By year with limit
files = downloader.download_year(1999, overwrite=False)

# By date range
files = downloader.download_date_range("1999-07-01", "1999-08-31")

# Full control
files = downloader.download_shows(
    year=1999,
    limit=50,
    overwrite=False
)
```

### Format Shows

```python
from phish_json_formatter import (
    format_file,
    format_dir,
    normalize_show,
    validate_normalized
)
from pathlib import Path

# Single file
format_file(Path("raw.json"), Path("normalized.json"))

# Batch directory
format_dir(Path("raw_shows"), Path("normalized_shows"))

# Direct normalization
raw = {"showdate": "1999-07-24", "venue": "...", "city": "..."}
normalized = normalize_show(raw, "input.json")
validate_normalized(normalized)
```

## Files

```
phish_downloader/
├── phishnet_downloader.py      (300+ lines) - API downloader
├── phish_json_formatter.py     (500+ lines) - Normalizer
├── __init__.py                 - Module exports
├── __main__.py                 - CLI entry point
├── tests/
│   └── test_formatter.py       (350+ lines) - 16 comprehensive tests
├── README.md                   - User documentation
├── DOWNLOADER.md               - Downloader documentation
├── QUICKSTART.md               - Quick start guide
├── IMPLEMENTATION.md           - Technical implementation details
└── .env                        - Configuration (PHISHNET_API_KEY)
```

## Configuration

Create `.env` file:

```env
PHISHNET_API_KEY=YOUR_API_KEY_HERE
```

Get your free API key from: https://phish.net/api

## CLI Examples

```bash
# Download 1999
python -m phishnet_downloader --year 1999

# Download with limit
python -m phishnet_downloader --year 1999 --limit 10

# Download date range
python -m phishnet_downloader --start-date 1999-07-01 --end-date 1999-08-31

# Custom output directory
python -m phishnet_downloader --year 1999 --output ./my_shows

# Overwrite existing
python -m phishnet_downloader --year 1999 --overwrite

# Full pipeline
python -m phishnet_downloader --year 1999 --output ./raw
python -m phish_json_formatter --in ./raw --out ./normalized
```

## Testing

All 16 tests pass with 100% coverage of core functionality:

```bash
pytest tests/ -v
```

Tests cover:
- Basic field normalization
- Setlist structure preservation  
- Notes and comments extraction
- Provenance tracking
- Validation (required fields, date format)
- File I/O and error handling

## Limitations

- Setlist data only available for shows from ~1989 onwards (API limitation)
- Some very old shows may lack complete information
- Rate limiting: 1 second between requests (configurable)

## Performance

- Download ~1999 (150 shows): ~2-3 minutes
- Format ~1999 (150 shows): ~1-2 seconds
- Both stages: ~3-5 minutes total

## Next Steps

1. Configure `.env` with your API key
2. Download a small sample: `python -m phishnet_downloader --year 1983 --limit 5`
3. Format the shows: `python -m phish_json_formatter --in raw_shows --out normalized`
4. Process the normalized JSON in your application

## Support

- Phish.net API: https://phish.net/api
- Phish.net Support: https://phish.net/contact
- GitHub Issues: Use for bugs/feature requests
