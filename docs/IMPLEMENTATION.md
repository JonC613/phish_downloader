# Implementation Summary: Phish JSON Formatter

## What Was Built

A complete Python module that converts raw Phish show JSON (from various APIs) into a normalized, stable schema.

### Core Files

1. **[phish_json_formatter.py](phish_json_formatter.py)** (~500 lines)
   - `normalize_show(raw: dict, input_filename: str) -> dict` - Main normalization function
   - `format_file(input_path: Path, output_path: Path) -> None` - Single file processor
   - `format_dir(input_dir: Path, output_dir: Path) -> None` - Batch directory processor
   - `validate_normalized(data: dict) -> None` - Schema validation
   - Field mapping helpers for flexible raw JSON parsing
   - Support for various raw JSON field name variations

2. **[__main__.py](__main__.py)** (~55 lines)
   - CLI entry point: `python -m phish_json_formatter --in <path> --out <path>`
   - Supports both single files and directory batch processing
   - Clear error messages and status feedback

3. **[tests/test_formatter.py](tests/test_formatter.py)** (~350 lines)
   - 16 comprehensive pytest tests covering all functionality
   - Tests organized into classes: TestNormalizeShow, TestValidation, TestFormatFile
   - Fixtures with realistic sample raw JSON
   - 100% pass rate with no warnings

### Features Implemented

✓ **Flexible field mapping** - Handles various raw JSON key names
✓ **Normalized schema v2.0** - Consistent structure with sorted keys
✓ **Show ID generation** - Prefers API ID, falls back to date-venue-city slug
✓ **Setlist preservation** - Maintains set structure, songs, transitions, notes
✓ **Validation** - Ensures required fields (date, venue, city) and proper formatting
✓ **Batch processing** - Recursively process entire directories
✓ **Clean output** - UTF-8, indent=2, sorted keys, trailing newline
✓ **Provenance tracking** - Records input filename, API source, generation timestamp
✓ **Comprehensive testing** - 16 tests covering normalization, validation, and file I/O
✓ **Error handling** - Clear validation errors and missing field messages
✓ **Windows compatible** - Fixed Unicode issues with print statements

### Normalized Schema Structure

```
show              ← metadata (id, date, tour, venue with coords)
├─ setlist        ← array of sets with songs (title, transition, notes)
├─ notes          ← curated bullets + fan comments with metadata
├─ facts          ← labeled facts with optional details and sources
├─ sources        ← array tracking data sources (type, url, timestamp)
└─ provenance     ← raw input filename, API, download timestamp, generation info
```

### Usage Examples

**Single file:**
```bash
python -m phish_json_formatter --in raw.json --out normalized.json
```

**Batch directory:**
```bash
python -m phish_json_formatter --in ./raw_shows --out ./normalized_shows
```

**Python API:**
```python
from phish_json_formatter import normalize_show, format_dir

# Single show
normalized = normalize_show(raw_data, "show.json")

# Batch
format_dir(Path("raw"), Path("normalized"))
```

### Test Results

```
16 passed in 0.14s

✓ Basic field normalization
✓ Setlist structure preservation  
✓ Notes and fan comments extraction
✓ Provenance tracking
✓ Missing required field validation (date, venue, city)
✓ Stable ID generation (API ID + fallback)
✓ JSON file writing with proper formatting
✓ Parent directory creation
✓ Trailing newline enforcement
✓ Error handling
```

### Sample Raw → Normalized Transformation

**Raw Input:**
```json
{
  "id": "api-12345",
  "date": "2024-01-01",
  "venueName": "Madison Square Garden",
  "city": "New York",
  "state": "NY",
  "lat": 40.7505,
  "lon": -73.9934,
  "tour": "Winter Tour 2024",
  "setlist": [
    {
      "name": "Set 1",
      "songs": [
        {"title": "Reprise", "transition": "->"}
      ]
    }
  ]
}
```

**Normalized Output:**
```json
{
  "schema_version": "2.0",
  "show": {
    "id": "api-12345",
    "date": "2024-01-01",
    "tour": "Winter Tour 2024",
    "venue": {
      "name": "Madison Square Garden",
      "city": "New York",
      "state": "NY",
      "country": "USA",
      "lat": 40.7505,
      "lon": -73.9934
    }
  },
  "setlist": [...],
  "notes": {"curated": [], "fan_comments": []},
  "facts": [],
  "sources": [],
  "provenance": {
    "raw_input": {"filename": "...", "api": "...", "downloaded_at": "..."},
    "generated_at": "2024-01-02T12:34:56+00:00",
    "generator": "phish-json-formatter"
  }
}
```

### Key Design Decisions

1. **Simple validation over Pydantic** - Clear, lightweight validation that works everywhere
2. **Field mapping helpers** - Separate extraction functions for each field, easy to extend
3. **Stable sorting** - Sorted keys in output ensure clean diffs when files change
4. **Provenance first-class** - Tracks data lineage without losing raw information
5. **Graceful omission** - Missing encore sets are omitted entirely (not empty arrays)
6. **Timezone aware** - Uses UTC with timezone info in timestamps

### Files in Workspace

```
phish_downloader/
├── __init__.py                    ← exports main API
├── __main__.py                    ← CLI entry point  
├── phish_json_formatter.py        ← core implementation (506 lines)
├── README.md                      ← user documentation
├── IMPLEMENTATION.md              ← this file
├── tests/
│   ├── __init__.py
│   └── test_formatter.py          ← 16 comprehensive tests
├── test_input.json                ← example raw show
├── test_output.json               ← example normalized show
├── test_raw_shows/                ← batch test directory
│   ├── show_2024_01_06.json
│   └── show_2024_01_07.json
└── test_normalized_shows/         ← batch output directory
    ├── show_2024_01_06.json
    └── show_2024_01_07.json
```

## Ready to Use

The formatter is production-ready and can immediately process:
- Single raw JSON files
- Entire directories recursively
- Various raw JSON schemas from different APIs
- Generate clean, normalized, stable JSON files
- Track provenance for data lineage

Run tests anytime with: `pytest tests/ -v`
