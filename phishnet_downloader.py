"""
Phish.net API v5 downloader for show records.
Downloads raw show data from phish.net API v5 and saves as JSON files.

Uses PHISHNET_API_KEY from .env for authenticated requests.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import time

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
PHISHNET_API_KEY = os.getenv("PHISHNET_API_KEY")
PHISHNET_API_BASE = "https://api.phish.net/v5"
DEFAULT_OUTPUT_DIR = Path("raw_shows")
REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 1.0  # seconds between requests


class PhishNetDownloader:
    """Downloads show data from phish.net API v5."""

    def __init__(self, api_key: Optional[str] = None, output_dir: Optional[Path] = None, rate_limit_delay: float = 1.0):
        """
        Initialize the downloader.
        
        Args:
            api_key: Phish.net API key (defaults to PHISHNET_API_KEY env var)
            output_dir: Directory to save downloaded JSON files
            rate_limit_delay: Delay between API requests in seconds
        """
        self.api_key = api_key or PHISHNET_API_KEY
        if not self.api_key:
            raise ValueError("PHISHNET_API_KEY not found in environment")
        
        self.api_key = self.api_key.strip()
        self.output_dir = Path(output_dir or DEFAULT_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.last_request_time = 0
    
    def get_shows_by_year(self, year: int, limit: Optional[int] = None) -> list[dict]:
        """
        Get shows from a specific year.
        
        Args:
            year: Year to fetch (e.g., 1999)
            limit: Optional limit on number of shows to return
        
        Returns:
            List of show dictionaries
        """
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        
        url = f"{PHISHNET_API_BASE}/shows/showyear/{year}.json"
        params = {"apikey": self.api_key}
        
        print(f"Fetching shows for {year} from {url}")
        
        try:
            response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            self.last_request_time = time.time()
            
            data = response.json()
            shows = data.get("data", [])
            
            # Filter for Phish shows only (artistid = 1)
            shows = [s for s in shows if int(s.get("artistid", 0)) == 1]
            
            # Apply limit if specified
            if limit and limit > 0:
                shows = shows[:limit]
                print(f"[OK] Retrieved {len(shows)} Phish shows for {year} (limited to {limit})")
            else:
                print(f"[OK] Retrieved {len(shows)} Phish shows for {year}")
            
            return shows
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] API request failed: {e}")
            return []
    
    def get_shows_by_date_range(self, start_date: str, end_date: str) -> list[dict]:
        """
        Get shows within a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            List of show dictionaries
        """
        # For now, this is a helper that gets the year range
        # phish.net API v5 doesn't have a date range endpoint, so we'll fetch by year
        try:
            start_year = int(start_date.split("-")[0])
            end_year = int(end_date.split("-")[0])
        except (ValueError, IndexError):
            print(f"Invalid date format: {start_date} to {end_date}")
            return []
        
        all_shows = []
        for year in range(start_year, end_year + 1):
            shows = self.get_shows_by_year(year)
            # Filter by actual dates
            shows = [s for s in shows if start_date <= s.get("showdate", "") <= end_date]
            all_shows.extend(shows)
        
        return all_shows
    
    def get_show_by_id(self, show_id: str) -> Optional[dict]:
        """
        Get a single show by ID.
        
        Args:
            show_id: Show ID from phish.net
        
        Returns:
            Show dictionary or None if request fails
        """
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        
        url = f"{PHISHNET_API_BASE}/shows/{show_id}.json"
        params = {"apikey": self.api_key}
        
        try:
            response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            self.last_request_time = time.time()
            
            data = response.json()
            return data.get("data", data)
        except requests.exceptions.RequestException as e:
            print(f"[WARN] Failed to fetch show {show_id}: {e}")
            return None
    
    def get_show_by_date(self, show_date: str) -> Optional[dict]:
        """
        Get show details by date using the setlist endpoint.
        
        Args:
            show_date: Show date (YYYY-MM-DD)
        
        Returns:
            Show dictionary with setlist or None if request fails
        """
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        
        url = f"{PHISHNET_API_BASE}/setlists/showdate/{show_date}.json"
        params = {"apikey": self.api_key}
        
        print(f"  Fetching setlist for {show_date}")
        
        try:
            response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            self.last_request_time = time.time()
            
            setlist_data = response.json().get("data", [])
            
            if not setlist_data:
                print(f"  [WARN] No setlist data for {show_date}")
                return None
            
            # Initialize show data from first entry
            show_data = {
                "showdate": setlist_data[0].get("showdate"),
                "venue": setlist_data[0].get("venue"),
                "city": setlist_data[0].get("city"),
                "state": setlist_data[0].get("state"),
                "country": setlist_data[0].get("country"),
                "setlist_notes": setlist_data[0].get("setlistnotes"),
                "tour_name": setlist_data[0].get("tourname"),
                "sets": {}
            }
            
            # Process each song and organize by set
            for song in setlist_data:
                set_name = song.get("set", "")
                if set_name:
                    if set_name not in show_data["sets"]:
                        show_data["sets"][set_name] = []
                    
                    song_entry = {
                        "song": song.get("song", ""),
                        "transition": song.get("transition") == 1
                    }
                    
                    # Add additional song details if present
                    if song.get("isjam") == 1:
                        song_entry["jam"] = True
                    if song.get("footnote"):
                        song_entry["footnote"] = song.get("footnote")
                    
                    show_data["sets"][set_name].append(song_entry)
            
            return show_data if show_data.get("showdate") and show_data.get("venue") else None
            
        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] Failed to fetch setlist for {show_date}: {e}")
            return None
    
    def download_shows(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
        overwrite: bool = False
    ) -> list[Path]:
        """
        Download shows and save as JSON files.
        
        Args:
            year: Download shows from a specific year
            month: Not used (kept for compatibility)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Max shows to download
            overwrite: Overwrite existing files
        
        Returns:
            List of paths to downloaded files
        """
        # Get the list of shows based on filters
        shows = []
        if year:
            shows = self.get_shows_by_year(year, limit=limit)
        elif start_date and end_date:
            shows = self.get_shows_by_date_range(start_date, end_date)
            if limit:
                shows = shows[:limit]
        else:
            print("[ERROR] Please specify either --year or --start-date and --end-date")
            return []
        
        if not shows:
            print("[WARN] No shows retrieved from API")
            return []
        
        downloaded_files = []
        total_shows = len(shows)
        
        for idx, show in enumerate(shows, 1):
            show_date = show.get("showdate")
            venue = show.get("venue", "unknown")
            city = show.get("city", "unknown")
            
            if not show_date:
                print(f"[{idx}/{total_shows}] [SKIP] Missing showdate")
                continue
            
            # Generate filename
            venue_slug = self._slugify(venue)
            city_slug = self._slugify(city)
            filename = f"{show_date}_{venue_slug}_{city_slug}.json"
            filepath = self.output_dir / filename
            
            # Skip if exists and not overwrite
            if filepath.exists() and not overwrite:
                print(f"[{idx}/{total_shows}] [EXISTS] {filepath.name}")
                continue
            
            # Fetch full show details with setlist
            print(f"[{idx}/{total_shows}] Fetching {show_date} - {venue}, {city}")
            full_show = self.get_show_by_date(show_date)
            
            # If no setlist found, use basic show info from API
            if not full_show:
                print(f"  [WARN] No setlist data, using basic info")
                full_show = {
                    "showdate": show_date,
                    "venue": venue,
                    "city": city,
                    "state": show.get("state"),
                    "country": show.get("country"),
                    "tour_name": show.get("tourname"),
                    "sets": {},
                    "setlist_notes": None
                }
            
            # Add metadata
            full_show["downloaded_at"] = datetime.utcnow().isoformat() + "Z"
            full_show["api"] = "phish.net"
            
            # Save to file
            try:
                filepath.parent.mkdir(parents=True, exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(full_show, f, indent=2, ensure_ascii=False)
                
                print(f"[{idx}/{total_shows}] [OK] Saved {filepath.name}")
                downloaded_files.append(filepath)
                
            except Exception as e:
                print(f"[{idx}/{total_shows}] [ERROR] {filename}: {e}")
        
        print(f"\n[OK] Downloaded {len(downloaded_files)}/{total_shows} shows to {self.output_dir}")
        return downloaded_files
    
    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to slug."""
        if not text:
            return "unknown"
        import re
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', '-', text)
        text = text.strip('-')
        return text[:50]  # Limit length
    
    def download_year(self, year: int, overwrite: bool = False) -> list[Path]:
        """Download all shows from a year."""
        return self.download_shows(year=year, overwrite=overwrite)
    
    def download_date_range(
        self,
        start_date: str,
        end_date: str,
        overwrite: bool = False
    ) -> list[Path]:
        """Download shows within a date range."""
        return self.download_shows(
            start_date=start_date,
            end_date=end_date,
            overwrite=overwrite
        )


def main():
    """CLI entry point for downloading shows."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download shows from phish.net API v5"
    )
    
    parser.add_argument(
        "--year",
        type=int,
        help="Download shows from a specific year"
    )
    parser.add_argument(
        "--month",
        type=int,
        help="Download shows from a specific month (1-12)"
    )
    parser.add_argument(
        "--start-date",
        help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        help="End date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of shows"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files"
    )
    
    args = parser.parse_args()
    
    try:
        downloader = PhishNetDownloader(output_dir=args.output)
        downloader.download_shows(
            year=args.year,
            month=args.month,
            start_date=args.start_date,
            end_date=args.end_date,
            limit=args.limit,
            overwrite=args.overwrite
        )
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
