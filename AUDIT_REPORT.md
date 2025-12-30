
# PHISH SHOWS AUDIT REPORT
Generated: 2025-12-29T19:12:16.433280

## Summary
- **Total shows available on phish.net API (1983-2025)**: 2209
- **Total shows downloaded locally**: 2202
- **Status**: ✗ MISSING (7 shows)

## Missing Shows by Year
{
  "1985": 3,
  "1999": 1,
  "2000": 2,
  "2014": 1
}

## Next Steps
Run the following to complete the audit:
```
python -c "from phish_json_formatter import format_dir; from pathlib import Path; format_dir(Path('raw_shows'), Path('normalized_shows'))"
```
