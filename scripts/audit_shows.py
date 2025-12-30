"""
Audit all Phish shows from 1983-2025.
Verifies that raw_shows directory matches all shows available through phish.net API.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from phishnet_downloader import PhishNetDownloader

def get_api_shows_count(year: int) -> int:
    """Get count of shows available from API for a year."""
    downloader = PhishNetDownloader()
    try:
        shows = downloader.get_shows_by_year(year)
        return len(shows)
    except:
        return 0

def get_local_shows_count(year: int) -> int:
    """Count shows in raw_shows directory for a year."""
    raw_dir = Path("raw_shows")
    if not raw_dir.exists():
        return 0
    count = len(list(raw_dir.glob(f"{year}-*.json")))
    return count

def audit_all_years():
    """Audit shows for all years 1983-2025."""
    print(f"\n{'='*70}")
    print("PHISH SHOWS AUDIT: 1983-2025")
    print(f"{'='*70}\n")
    
    api_total = 0
    local_total = 0
    missing_shows = defaultdict(list)
    
    print(f"{'Year':<8} {'API':<8} {'Local':<8} {'Status':<20}")
    print(f"{'-'*70}")
    
    for year in range(1983, 2026):
        api_count = get_api_shows_count(year)
        local_count = get_local_shows_count(year)
        
        api_total += api_count
        local_total += local_count
        
        if api_count == local_count:
            status = "COMPLETE"
        elif local_count > api_count:
            status = f"OVER (+{local_count - api_count})"
        else:
            status = f"MISSING ({api_count - local_count})"
            missing_shows[year] = api_count - local_count
        
        print(f"{year:<8} {api_count:<8} {local_count:<8} {status:<20}")
    
    print(f"{'-'*70}")
    print(f"{'TOTAL':<8} {api_total:<8} {local_total:<8}", end="")
    
    if api_total == local_total:
        print(" COMPLETE")
    else:
        print(f" MISSING ({api_total - local_total})")
    
    print(f"\n{'='*70}")
    
    if missing_shows:
        print("\nMISSING SHOWS BY YEAR:")
        print(f"{'-'*70}")
        for year in sorted(missing_shows.keys()):
            count = missing_shows[year]
            print(f"  {year}: Missing {count} show(s)")
        
        print(f"\n{'-'*70}")
        print(f"Total missing shows: {sum(missing_shows.values())}")
        print(f"\nAutomatic downloading of missing shows...")
        download_missing_shows(missing_shows)
    else:
        print("\n✓ All shows accounted for!")
    
    print(f"\n{'='*70}\n")
    
    return {
        'api_total': api_total,
        'local_total': local_total,
        'missing_by_year': dict(missing_shows),
        'total_missing': sum(missing_shows.values())
    }

def download_missing_shows(missing_shows: dict):
    """Download all missing shows."""
    downloader = PhishNetDownloader()
    total_downloaded = 0
    
    print(f"\n{'='*70}")
    print("DOWNLOADING MISSING SHOWS")
    print(f"{'='*70}\n")
    
    for year in sorted(missing_shows.keys()):
        print(f"Downloading {year}...")
        try:
            files = downloader.download_year(year, overwrite=False)
            total_downloaded += len(files)
            print(f"  [OK] Downloaded {len(files)} shows\n")
        except KeyboardInterrupt:
            print(f"  [INTERRUPTED] Stopping downloads")
            break
        except Exception as e:
            print(f"  [ERROR] Failed to download {year}: {e}\n")
    
    print(f"\n{'='*70}")
    print(f"Total downloaded: {total_downloaded}")
    print(f"{'='*70}\n")
    
    return total_downloaded

def generate_audit_report():
    """Generate and save audit report."""
    results = audit_all_years()
    
    report = f"""
# PHISH SHOWS AUDIT REPORT
Generated: {__import__('datetime').datetime.now().isoformat()}

## Summary
- **Total shows available on phish.net API (1983-2025)**: {results['api_total']}
- **Total shows downloaded locally**: {results['local_total']}
- **Status**: {"✓ COMPLETE" if results['total_missing'] == 0 else f"✗ MISSING ({results['total_missing']} shows)"}

## Missing Shows by Year
{json.dumps(results['missing_by_year'], indent=2) if results['missing_by_year'] else "None - All shows downloaded!"}

## Next Steps
Run the following to complete the audit:
```
python -c "from phish_json_formatter import format_dir; from pathlib import Path; format_dir(Path('raw_shows'), Path('normalized_shows'))"
```
"""
    
    with open('AUDIT_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("Audit report saved to AUDIT_REPORT.md")

if __name__ == "__main__":
    generate_audit_report()
