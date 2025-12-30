# Phish JSON Formatter

Converts raw Phish show JSON from various APIs into a normalized, stable schema with consistent field names, ordering, and formatting.

## Features

- **Flexible field mapping**: Automatically extracts date, venue, city, state, country, coordinates, tour, and setlist from various raw JSON formats
- **Normalized schema**: Converts to a consistent schema with predictable structure
- **Stable IDs**: Generates deterministic show IDs (prefer API ID, fallback to date-venue-city slug)
- **Setlist preservation**: Maintains set/song structure with transitions and notes
- **Batch processing**: Process single files or entire directories recursively
- **Validation**: Built-in validation ensures required fields and proper date formatting
- **Provenance tracking**: Records raw input filename, API source, and generation timestamp
- **Clean output**: Pretty-printed JSON with sorted keys, UTF-8 encoding, and trailing newline

## Installation

```bash
cd phish_downloader
python -m pip install -e .
# Or install in dev mode with pytest
python -m pip install -e ".[dev]"
```

## Usage

### Command Line

Format a single file:
```bash
python -m phish_json_formatter --in raw_show.json --out normalized_show.json
```

Format all JSON files in a directory (recursively):
```bash
python -m phish_json_formatter --in ./raw_shows --out ./normalized_shows
```

### Python API

```python
from phish_json_formatter import normalize_show, format_file, format_dir
from pathlib import Path

# Single show
raw_data = {"date": "2024-01-01", "venueName": "MSG", "city": "New York", ...}
normalized = normalize_show(raw_data, "input.json")

# Single file
format_file(Path("raw.json"), Path("normalized.json"))

# Directory (recursive)
format_dir(Path("raw_shows"), Path("normalized_shows"))
```

## Normalized Schema

```json
{
  "schema_version": "2.0",
  "show": {
    "id": "<stable_id>",
    "date": "YYYY-MM-DD",
    "tour": "<string or null>",
    "venue": {
      "name": "<venue>",
      "city": "<city>",
      "state": "<state or null>",
      "country": "<country>",
      "lat": <float or null>,
      "lon": <float or null>
    }
  },
  "setlist": [
    {
      "name": "<Set N or Encore>",
      "songs": [
        {
          "title": "<song>",
          "transition": "->" | null,
          "notes": ["<note1>", "<note2>"]
        }
      ]
    }
  ],
  "notes": {
    "curated": ["<bullet note>"],
    "fan_comments": [
      {
        "source": "<site>",
        "author": "<name or null>",
        "date": "<iso or null>",
        "text": "<comment>",
        "url": "<url or null>"
      }
    ]
  },
  "facts": [
    {
      "label": "<short fact>",
      "detail": "<optional longer>",
      "source_url": "<url or null>"
    }
  ],
  "sources": [
    {
      "type": "api|phishnet|phish.in|setlistfm|other",
      "url": "<url>",
      "retrieved_at": "<iso8601>"
    }
  ],
  "provenance": {
    "raw_input": {
      "filename": "<input file>",
      "api": "<api name>",
      "downloaded_at": "<iso8601 or null>"
    },
    "generated_at": "<iso8601>",
    "generator": "phish-json-formatter"
  }
}
```

## Field Mapping

The formatter automatically searches for common field names in the raw JSON:

| Normalized | Raw candidates |
|-----------|----------|
| `date` | `date`, `showDate`, `show_date`, `event_date`, `eventDate` |
| `venue.name` | `venue`, `venueName`, `venue_name`, `location` |
| `venue.city` | `city`, `venue_city`, `venueCity` |
| `venue.state` | `state`, `province`, `venue_state`, `venueState` |
| `venue.country` | `country`, `venue_country`, `venueCountry` (defaults to "USA") |
| `venue.lat` | `lat`, `latitude`, `venue_lat`, `venueLat` |
| `venue.lon` | `lon`, `longitude`, `lng`, `venue_lon`, `venueLon` |
| `tour` | `tour`, `tour_name`, `tourName` |
| `show.id` | `id`, `show_id`, `showId`, `api_id`, `apiId` |
| `setlist` | `setlist`, `sets`, `song_sets`, `songSets` |

## Running Tests

```bash
python -m pytest tests/ -v
```

All 16 tests pass:
- Normalization (basic fields, setlist, notes, provenance, ID generation)
- Validation (required fields, date format)
- File operations (writes JSON, creates directories, trailing newlines, error handling)

## Examples

See [test_formatter.py](tests/test_formatter.py) for complete examples with sample raw and normalized JSON.
