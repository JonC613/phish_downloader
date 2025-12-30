"""Download all remaining shows from 2011-2024."""
from phishnet_downloader import PhishNetDownloader

downloader = PhishNetDownloader()

years = list(range(2011, 2025))  # 2011-2024
print(f"Downloading shows for years: {years}\n")

total_downloaded = 0

for year in years:
    print(f"\nFetching {year}...")
    try:
        files = downloader.download_year(year)
        total_downloaded += len(files)
        print(f"[OK] Downloaded {len(files)} shows for {year}")
    except Exception as e:
        print(f"[ERROR] Failed to download {year}: {e}")

print(f"\n{'='*60}")
print(f"Total shows downloaded: {total_downloaded}")
print(f"{'='*60}")
