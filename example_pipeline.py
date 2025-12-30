#!/usr/bin/env python3
"""
End-to-end example: Download Phish shows and process them.

This script demonstrates the complete workflow:
1. Download raw show data from phish.net API
2. Normalize to consistent schema
3. Process the normalized data
"""

from pathlib import Path
import json

from phishnet_downloader import PhishNetDownloader
from phish_json_formatter import format_dir, validate_normalized


def main():
    """Download and process Phish shows."""
    
    # Configuration
    year = 1999
    raw_dir = Path("data/raw_shows")
    normalized_dir = Path("data/normalized_shows")
    
    print("=" * 70)
    print("PHISH SHOW DOWNLOADER & FORMATTER PIPELINE")
    print("=" * 70)
    
    # =========================================================================
    # STEP 1: Download Raw Show Data from Phish.net API
    # =========================================================================
    
    print(f"\n[STEP 1] Downloading shows from {year}...\n")
    
    downloader = PhishNetDownloader(output_dir=raw_dir)
    
    # Download shows (limit to 5 for this example)
    raw_files = downloader.download_shows(
        year=year,
        limit=5,  # Use limit=None to download all
        overwrite=False  # Skip if already downloaded
    )
    
    if not raw_files:
        print(f"No new shows downloaded for {year}")
        return
    
    # =========================================================================
    # STEP 2: Normalize Raw Shows to Standard Schema
    # =========================================================================
    
    print(f"\n[STEP 2] Normalizing {len(raw_files)} shows...\n")
    
    format_dir(raw_dir, normalized_dir)
    
    # =========================================================================
    # STEP 3: Process Normalized Shows
    # =========================================================================
    
    print(f"\n[STEP 3] Processing normalized shows...\n")
    
    normalized_files = list(normalized_dir.glob("*.json"))
    
    # Statistics
    total_songs = 0
    shows_with_encore = 0
    
    for show_file in sorted(normalized_files):
        with open(show_file) as f:
            show = json.load(f)
        
        # Validate
        validate_normalized(show)
        
        # Extract data
        show_id = show["show"]["id"]
        date = show["show"]["date"]
        venue = show["show"]["venue"]["name"]
        city = show["show"]["venue"]["city"]
        tour = show["show"]["tour"]
        setlist = show.get("setlist", [])
        
        # Count songs
        num_songs = sum(len(s["songs"]) for s in setlist)
        total_songs += num_songs
        
        # Check for encore
        if any(s["name"] == "Encore" for s in setlist):
            shows_with_encore += 1
        
        # Print show summary
        print(f"  {date} @ {venue}, {city}")
        print(f"    Tour: {tour}")
        print(f"    Songs: {num_songs} (Sets: {len(setlist)})")
        print()
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Year processed: {year}")
    print(f"Total shows: {len(normalized_files)}")
    print(f"Total songs: {total_songs}")
    print(f"Shows with encore: {shows_with_encore}")
    print(f"Raw shows: {raw_dir}")
    print(f"Normalized shows: {normalized_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
