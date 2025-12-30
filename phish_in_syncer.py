#!/usr/bin/env python3
"""
Syncer to enrich normalized JSON files with phish.in API data.

Adds:
- Audio status and MP3 URLs
- Tour information
- Tags (debuts, special events)
- Jam timestamps
- Venue coordinates
- Cover art URLs
- Taper notes
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from phish_in_api_client import (
    get_show,
    get_years,
    get_statistics,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NORMALIZED_SHOWS_DIR = Path(__file__).parent / "normalized_shows"
ENRICHED_SHOWS_DIR = Path(__file__).parent / "enriched_shows"


def ensure_output_dir():
    """Create enriched_shows directory if needed."""
    ENRICHED_SHOWS_DIR.mkdir(exist_ok=True)


def enrich_show(local_show: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich local show data with API data.
    
    Args:
        local_show: Show dict from normalized JSON
        
    Returns:
        Enhanced show dict with API data merged in
    """
    show_date = local_show.get("show", {}).get("date")
    
    if not show_date:
        logger.warning(f"No date found in show data")
        return local_show
    
    # Fetch from API
    api_show = get_show(show_date)
    
    if not api_show:
        logger.warning(f"API returned no data for {show_date}")
        return local_show
    
    # Merge data - API data enriches local data
    enriched = local_show.copy()
    show_data = enriched.get("show", {})
    
    # Add API-sourced fields
    show_data.update({
        "audio_status": api_show.get("audio_status"),
        "duration_ms": api_show.get("duration"),
        "cover_art_urls": api_show.get("cover_art_urls"),
        "album_cover_url": api_show.get("album_cover_url"),
        "album_zip_url": api_show.get("album_zip_url"),
        "tour_name": api_show.get("tour_name"),
        "admin_notes": api_show.get("admin_notes"),
        "taper_notes": api_show.get("taper_notes"),
        "likes_count": api_show.get("likes_count"),
        "tags": api_show.get("tags", []),  # Notable shows, debuts, etc.
        "previous_show_date": api_show.get("previous_show_date"),
        "next_show_date": api_show.get("next_show_date"),
    })
    
    # Enhance venue with coordinates
    if "venue" in api_show:
        venue_data = api_show["venue"]
        show_data["venue"] = {
            **show_data.get("venue", {}),
            "latitude": venue_data.get("latitude"),
            "longitude": venue_data.get("longitude"),
            "shows_count": venue_data.get("shows_count"),
            "shows_with_audio_count": venue_data.get("shows_with_audio_count"),
        }
    
    # Replace setlist with API tracks (includes MP3 URLs)
    if "tracks" in api_show:
        enriched["tracks"] = []
        for track in api_show["tracks"]:
            enriched["tracks"].append({
                "id": track.get("id"),
                "slug": track.get("slug"),
                "title": track.get("title"),
                "position": track.get("position"),
                "set_name": track.get("set_name"),
                "duration_ms": track.get("duration"),
                "jam_starts_at_second": track.get("jam_starts_at_second"),
                "mp3_url": track.get("mp3_url"),
                "waveform_image_url": track.get("waveform_image_url"),
                "audio_status": track.get("audio_status"),
                "exclude_from_stats": track.get("exclude_from_stats"),
                "tags": track.get("tags", []),
                "songs": track.get("songs", []),
            })
    
    enriched["show"] = show_data
    return enriched


def sync_all_shows(dry_run: bool = False, start_year: int = None, end_year: int = None, max_shows: int = None) -> Dict[str, int]:
    """
    Sync all normalized shows with API data.
    
    Args:
        dry_run: If True, don't write files, just count
        start_year: Only process shows from this year onwards
        end_year: Only process shows up to this year
        max_shows: Maximum number of shows to process
        
    Returns:
        Stats dict with success/fail counts
    """
    ensure_output_dir()
    
    stats = {
        "total": 0,
        "enriched": 0,
        "failed": 0,
        "skipped": 0,
    }
    
    json_files = sorted(NORMALIZED_SHOWS_DIR.glob("*.json"))
    
    # Filter by year if specified
    if start_year or end_year:
        filtered_files = []
        for f in json_files:
            try:
                year = int(f.stem[:4])  # Extract year from filename
                if start_year and year < start_year:
                    continue
                if end_year and year > end_year:
                    continue
                filtered_files.append(f)
            except ValueError:
                continue  # Skip malformed filenames
        json_files = filtered_files
    
    # Limit number of files if specified
    if max_shows:
        json_files = json_files[:max_shows]
    
    logger.info(f"Processing {len(json_files)} shows...")
    
    for idx, json_file in enumerate(json_files, 1):
        stats["total"] += 1
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                local_show = json.load(f)
            
            # Skip if already enriched
            if "audio_status" in local_show.get("show", {}):
                logger.info(f"[{idx}/{len(json_files)}] ⏭️  {json_file.name} (already enriched)")
                stats["skipped"] += 1
                continue
            
            logger.info(f"[{idx}/{len(json_files)}] 🔄 Enriching {json_file.name}...")
            enriched = enrich_show(local_show)
            
            if not dry_run:
                output_file = ENRICHED_SHOWS_DIR / json_file.name
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(enriched, f, indent=2, ensure_ascii=False)
            
            stats["enriched"] += 1
            
            # Progress checkpoint every 50 shows
            if idx % 50 == 0:
                logger.info(f"✅ Checkpoint: {idx}/{len(json_files)} processed. Success: {stats['enriched']}, Failed: {stats['failed']}")
            
        except KeyboardInterrupt:
            logger.warning(f"⚠️ Interrupted at show {idx}. Processed {stats['enriched']} successfully.")
            break
        except Exception as e:
            logger.error(f"❌ Failed to process {json_file.name}: {e}")
            stats["failed"] += 1
    
    return stats


def get_enrichment_summary() -> Dict[str, Any]:
    """
    Summarize what enrichment adds.
    
    Returns:
        Summary of new data fields and their availability
    """
    return {
        "new_fields": {
            "audio_status": "complete/partial/missing",
            "duration_ms": "Total show duration in milliseconds",
            "cover_art_urls": "URLs for cover art variants",
            "album_cover_url": "Album cover URL (text overlayed)",
            "album_zip_url": "ZIP download URL for full show",
            "tour_name": "Tour this show belongs to",
            "admin_notes": "Administrator notes about the show",
            "taper_notes": "Recording quality notes from taper",
            "likes_count": "User engagement metric",
            "tags": "Special show tags (debuts, special events, etc.)",
            "previous_show_date": "Date of previous show (any audio)",
            "next_show_date": "Date of next show (any audio)",
        },
        "venue_enhancements": {
            "latitude": "Venue coordinates",
            "longitude": "Venue coordinates",
            "shows_count": "Total shows at this venue",
            "shows_with_audio_count": "Shows with recorded audio",
        },
        "track_enhancements": {
            "mp3_url": "Direct link to track MP3",
            "waveform_image_url": "Waveform visualization URL",
            "jam_starts_at_second": "When jam section starts",
            "track_tags": "Track-level tags (jam breaks, debut, etc.)",
        },
    }


if __name__ == "__main__":
    import sys
    
    print("Phish.in API Enrichment Syncer")
    print("=" * 50)
    print()
    
    summary = get_enrichment_summary()
    print("NEW DATA FIELDS:")
    for section, fields in summary.items():
        print(f"\n{section}:")
        for field, desc in fields.items():
            print(f"  * {field}: {desc}")
    
    print("\n" + "=" * 50)
    print()
    
    # Check for dry-run flag
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    
    if dry_run:
        print("Running in DRY RUN mode (no files will be written)")
        print()
    
    stats = sync_all_shows(dry_run=dry_run)
    
    print("\n" + "=" * 50)
    print("SYNC RESULTS:")
    print(f"  Total shows:   {stats['total']}")
    print(f"  Enriched:      {stats['enriched']}")
    print(f"  Already done:  {stats['skipped']}")
    print(f"  Failed:        {stats['failed']}")
    
    if stats['enriched'] > 0:
        enriched_dir = "enriched_shows"
        print(f"\n[OK] Enriched shows saved to: {enriched_dir}/")
