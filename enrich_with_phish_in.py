#!/usr/bin/env python3
"""
Enrich existing normalized show JSON files with data from phish.in API.

Adds:
- Audio status and MP3 URLs
- Tour information and tags
- Venue coordinates 
- Jam timestamps
- User engagement metrics
- Taper notes and quality info
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from phish_in_api_client import get_show, get_venue, get_tour

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def enrich_show_data(show_json: Dict[str, Any], phish_in_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich existing show JSON with phish.in API data.
    
    Args:
        show_json: Existing normalized show data
        phish_in_data: Data from phish.in API
        
    Returns:
        Enriched show data
    """
    enriched = show_json.copy()
    
    # Add phish.in section
    phish_in_section = {
        "source": "phish.in",
        "fetched_at": datetime.utcnow().isoformat() + "Z",
    }
    
    # Audio status
    if phish_in_data.get("audio_status"):
        phish_in_section["audio_status"] = phish_in_data["audio_status"]
    
    # Tags (debuts, special events, etc.)
    if phish_in_data.get("tags"):
        phish_in_section["tags"] = phish_in_data["tags"]
    
    # Tour information
    if phish_in_data.get("tour"):
        phish_in_section["tour"] = {
            "name": phish_in_data["tour"].get("name"),
            "slug": phish_in_data["tour"].get("slug"),
            "starts_on": phish_in_data["tour"].get("starts_on"),
            "ends_on": phish_in_data["tour"].get("ends_on"),
        }
    
    # Venue coordinates and additional info
    if phish_in_data.get("venue"):
        venue_data = phish_in_data["venue"]
        phish_in_section["venue"] = {
            "latitude": venue_data.get("latitude"),
            "longitude": venue_data.get("longitude"),
            "slug": venue_data.get("slug"),
            "location": venue_data.get("location"),
            "shows_count": venue_data.get("shows_count"),
        }
    
    # User engagement
    if phish_in_data.get("likes_count") is not None:
        phish_in_section["likes_count"] = phish_in_data["likes_count"]
    
    # Taper notes
    if phish_in_data.get("taper_notes"):
        phish_in_section["taper_notes"] = phish_in_data["taper_notes"]
    
    # Enrich tracks with MP3 URLs and jam info
    if phish_in_data.get("tracks") and "setlist" in enriched:
        track_lookup = {t["title"]: t for t in phish_in_data["tracks"]}
        
        for set_data in enriched["setlist"]:
            for song in set_data.get("songs", []):
                song_title = song.get("title", "")
                if song_title in track_lookup:
                    track = track_lookup[song_title]
                    
                    # Add MP3 URL
                    if track.get("mp3_url"):
                        song["mp3_url"] = track["mp3_url"]
                    
                    # Add jam info
                    if track.get("jam_starts_at_second"):
                        song["jam_starts_at_second"] = track["jam_starts_at_second"]
                    if track.get("jam_ends_at_second"):
                        song["jam_ends_at_second"] = track["jam_ends_at_second"]
                    
                    # Add track-level tags
                    if track.get("tags"):
                        song["track_tags"] = track["tags"]
                    
                    # Add duration if available
                    if track.get("duration"):
                        song["duration_seconds"] = track["duration"]
    
    # Add the enriched data section
    enriched["phish_in"] = phish_in_section
    
    # Update schema version and provenance
    enriched["schema_version"] = "2.1"  # Increment for API enrichment
    if "provenance" not in enriched:
        enriched["provenance"] = {}
    enriched["provenance"]["enriched_with_phish_in"] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "enricher": "enrich_with_phish_in.py"
    }
    
    return enriched


def process_show_file(show_path: Path, output_path: Path = None) -> bool:
    """
    Process a single show file, enriching it with phish.in data.
    
    Args:
        show_path: Path to normalized show JSON file
        output_path: Optional different output path
        
    Returns:
        True if successful, False otherwise
    """
    if not show_path.exists():
        logger.error(f"Show file not found: {show_path}")
        return False
    
    try:
        # Load existing show data
        with open(show_path, "r", encoding="utf-8") as f:
            show_data = json.load(f)
        
        # Extract date from filename or show data
        if "show" in show_data and "date" in show_data["show"]:
            show_date = show_data["show"]["date"]
        else:
            # Try to extract from filename
            filename = show_path.stem
            if "_" in filename:
                show_date = filename.split("_")[0]  # YYYY-MM-DD format
            else:
                logger.error(f"Cannot extract date from {show_path}")
                return False
        
        logger.info(f"Enriching {show_date}...")
        
        # Fetch data from phish.in
        phish_in_data = get_show(show_date)
        if not phish_in_data:
            logger.warning(f"No phish.in data found for {show_date}")
            return False
        
        # Enrich the show data
        enriched_data = enrich_show_data(show_data, phish_in_data)
        
        # Write back to file (or different path)
        output_file = output_path if output_path else show_path
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(enriched_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Enriched {show_date}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to process {show_path}: {e}")
        return False


def enrich_all_shows(
    shows_dir: Path,
    output_dir: Path = None,
    start_year: int = None,
    end_year: int = None,
    max_shows: int = None,
    delay_seconds: float = 1.0,
) -> Dict[str, int]:
    """
    Enrich all show files in a directory.
    
    Args:
        shows_dir: Directory containing normalized show JSON files
        output_dir: Optional different output directory
        start_year: Only process shows from this year onwards
        end_year: Only process shows up to this year
        max_shows: Maximum number of shows to process (for testing)
        delay_seconds: Delay between API calls (rate limiting)
        
    Returns:
        Dict with success/failure counts
    """
    if not shows_dir.exists():
        logger.error(f"Shows directory not found: {shows_dir}")
        return {"success": 0, "failed": 0, "skipped": 0}
    
    if output_dir and not output_dir.exists():
        output_dir.mkdir(parents=True)
    
    show_files = list(shows_dir.glob("*.json"))
    
    # Filter by year if specified
    if start_year or end_year:
        filtered_files = []
        for f in show_files:
            try:
                # Extract year from filename YYYY-MM-DD
                year = int(f.stem.split("_")[0].split("-")[0])
                if start_year and year < start_year:
                    continue
                if end_year and year > end_year:
                    continue
                filtered_files.append(f)
            except (IndexError, ValueError):
                logger.warning(f"Cannot extract year from {f}")
                continue
        show_files = filtered_files
    
    # Limit for testing
    if max_shows:
        show_files = show_files[:max_shows]
    
    logger.info(f"Processing {len(show_files)} show files...")
    
    stats = {"success": 0, "failed": 0, "skipped": 0}
    
    for i, show_file in enumerate(show_files):
        # Check if already enriched
        try:
            with open(show_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "phish_in" in data:
                    logger.info(f"⏭️ Skipping {show_file.name} (already enriched)")
                    stats["skipped"] += 1
                    continue
        except Exception:
            pass
        
        # Determine output path
        if output_dir:
            output_path = output_dir / show_file.name
        else:
            output_path = None
        
        # Process the file
        if process_show_file(show_file, output_path):
            stats["success"] += 1
        else:
            stats["failed"] += 1
        
        # Rate limiting
        if i < len(show_files) - 1:  # Don't wait after last file
            time.sleep(delay_seconds)
    
    logger.info(f"🎉 Enrichment complete: {stats['success']} successful, {stats['failed']} failed, {stats['skipped']} skipped")
    return stats


def analyze_enriched_shows(shows_dir: Path) -> None:
    """
    Analyze enriched shows and print statistics.
    
    Args:
        shows_dir: Directory containing enriched show files
    """
    show_files = list(shows_dir.glob("*.json"))
    
    stats = {
        "total_shows": 0,
        "enriched_shows": 0,
        "with_audio": 0,
        "with_mp3_urls": 0,
        "with_tags": 0,
        "with_tour_info": 0,
        "with_coordinates": 0,
        "with_jams": 0,
    }
    
    audio_status_counts = {}
    tag_counts = {}
    tour_counts = {}
    
    for show_file in show_files:
        try:
            with open(show_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            stats["total_shows"] += 1
            
            if "phish_in" not in data:
                continue
                
            stats["enriched_shows"] += 1
            phish_in = data["phish_in"]
            
            # Audio status
            if phish_in.get("audio_status"):
                stats["with_audio"] += 1
                status = phish_in["audio_status"]
                audio_status_counts[status] = audio_status_counts.get(status, 0) + 1
            
            # MP3 URLs in tracks
            mp3_count = 0
            if "setlist" in data:
                for set_data in data["setlist"]:
                    for song in set_data.get("songs", []):
                        if song.get("mp3_url"):
                            mp3_count += 1
            if mp3_count > 0:
                stats["with_mp3_urls"] += 1
            
            # Tags
            if phish_in.get("tags"):
                stats["with_tags"] += 1
                for tag in phish_in["tags"]:
                    tag_name = tag.get("name", "Unknown")
                    tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1
            
            # Tour info
            if phish_in.get("tour", {}).get("name"):
                stats["with_tour_info"] += 1
                tour_name = phish_in["tour"]["name"]
                tour_counts[tour_name] = tour_counts.get(tour_name, 0) + 1
            
            # Coordinates
            if (phish_in.get("venue", {}).get("latitude") and 
                phish_in.get("venue", {}).get("longitude")):
                stats["with_coordinates"] += 1
            
            # Jam info
            jam_count = 0
            if "setlist" in data:
                for set_data in data["setlist"]:
                    for song in set_data.get("songs", []):
                        if song.get("jam_starts_at_second"):
                            jam_count += 1
            if jam_count > 0:
                stats["with_jams"] += 1
                
        except Exception as e:
            logger.error(f"Error analyzing {show_file}: {e}")
            continue
    
    # Print analysis
    print("\n🎪 PHISH.IN ENRICHMENT ANALYSIS")
    print("=" * 40)
    print(f"Total shows: {stats['total_shows']}")
    print(f"Enriched shows: {stats['enriched_shows']} ({stats['enriched_shows']/max(stats['total_shows'],1)*100:.1f}%)")
    print(f"With audio status: {stats['with_audio']}")
    print(f"With MP3 URLs: {stats['with_mp3_urls']}")
    print(f"With tags: {stats['with_tags']}")
    print(f"With tour info: {stats['with_tour_info']}")
    print(f"With coordinates: {stats['with_coordinates']}")
    print(f"With jam timestamps: {stats['with_jams']}")
    
    print("\n🎵 AUDIO STATUS BREAKDOWN:")
    for status, count in sorted(audio_status_counts.items()):
        print(f"  {status}: {count}")
    
    print("\n🏷️ TOP TAGS:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {tag}: {count}")
    
    print("\n🚌 TOP TOURS:")
    for tour, count in sorted(tour_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {tour}: {count}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enrich show files with phish.in API data")
    parser.add_argument("--shows-dir", type=Path, default=Path("normalized_shows"),
                        help="Directory containing normalized show JSON files")
    parser.add_argument("--output-dir", type=Path, help="Output directory (default: overwrite input)")
    parser.add_argument("--start-year", type=int, help="Start year for processing")
    parser.add_argument("--end-year", type=int, help="End year for processing") 
    parser.add_argument("--max-shows", type=int, help="Maximum shows to process (for testing)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between API calls (seconds)")
    parser.add_argument("--analyze-only", action="store_true", help="Only analyze existing enriched files")
    
    args = parser.parse_args()
    
    if args.analyze_only:
        analyze_enriched_shows(args.shows_dir)
    else:
        # Enrich shows
        stats = enrich_all_shows(
            shows_dir=args.shows_dir,
            output_dir=args.output_dir,
            start_year=args.start_year,
            end_year=args.end_year,
            max_shows=args.max_shows,
            delay_seconds=args.delay,
        )
        
        # Then analyze
        if stats["success"] > 0:
            print("\n" + "="*50)
            analyze_enriched_shows(args.output_dir or args.shows_dir)