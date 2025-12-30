"""Batch download shows for multiple years."""
from phishnet_downloader import PhishNetDownloader
from pathlib import Path

downloader = PhishNetDownloader()

years = list(range(1999, 2006))  # 1999-2005
print(f"Downloading shows for years: {years}\n")

for year in years:
    print(f"\n{'='*60}")
    print(f"Downloading {year}")
    print(f"{'='*60}")
    try:
        downloader.download_year(year)
    except Exception as e:
        print(f"[ERROR] Failed to download {year}: {e}")

print(f"\n{'='*60}")
print("Download complete!")
print(f"{'='*60}")

# Count total files
raw_files = list(Path("raw_shows").glob("*.json"))
print(f"Total raw shows downloaded: {len(raw_files)}")
