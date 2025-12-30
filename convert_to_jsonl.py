"""
Convert normalized show JSON files to JSONL format for AWS SageMaker.
Creates a single JSONL file with flattened show data suitable for training.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


def flatten_show(show: dict) -> dict:
    """
    Flatten a normalized show into a single-line JSON object suitable for SageMaker.
    
    Args:
        show: Normalized show dictionary
    
    Returns:
        Flattened dictionary with selected fields
    """
    show_info = show.get("show", {})
    venue = show_info.get("venue", {})
    setlist = show.get("setlist", [])
    notes = show.get("notes", {})
    
    # Extract setlist details
    all_songs = []
    set_names = []
    set_song_counts = {}
    
    for set_info in setlist:
        set_name = set_info.get("set", "")
        songs = set_info.get("songs", [])
        set_names.append(set_name)
        set_song_counts[f"songs_in_set_{set_name}"] = len(songs)
        
        for song in songs:
            song_title = song.get("title", "")
            song_notes = song.get("notes", [])
            all_songs.append({
                "title": song_title,
                "set": set_name,
                "notes": song_notes
            })
    
    # Extract curated notes and prepare as text
    curated_notes = notes.get("curated", [])
    notes_text = " | ".join(curated_notes) if curated_notes else ""
    
    # Flatten structure
    flattened = {
        # Core show info
        "date": show_info.get("date", ""),
        "year": show_info.get("date", "").split("-")[0] if show_info.get("date") else "",
        "show_id": show_info.get("id", ""),
        
        # Venue info
        "venue_name": venue.get("name", ""),
        "city": venue.get("city", ""),
        "state": venue.get("state"),
        "country": venue.get("country", ""),
        "latitude": venue.get("lat"),
        "longitude": venue.get("lon"),
        
        # Tour info
        "tour": show_info.get("tour"),
        
        # Setlist info
        "total_songs": len(all_songs),
        "num_sets": len(set_names),
        "set_names": ",".join(set_names),
        
        # Song counts per set
        **set_song_counts,
        
        # Song list (as JSON string)
        "songs": json.dumps([s["title"] for s in all_songs]),
        "setlist_with_sets": json.dumps(all_songs),
        
        # Notes
        "notes": notes_text,
        "num_curated_notes": len(curated_notes),
        
        # Metadata
        "downloaded_at": show.get("provenance", {}).get("raw_input", {}).get("downloaded_at", ""),
        "api": show.get("provenance", {}).get("raw_input", {}).get("api", ""),
    }
    
    # Remove None values for cleaner output
    flattened = {k: v for k, v in flattened.items() if v is not None}
    
    return flattened


def convert_to_jsonl(input_dir: Path, output_file: Path) -> int:
    """
    Convert all normalized show JSON files to a single JSONL file.
    
    Args:
        input_dir: Directory containing normalized show JSON files
        output_file: Path to output JSONL file
    
    Returns:
        Number of shows converted
    """
    input_dir = Path(input_dir)
    output_file = Path(output_file)
    
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")
    
    # Load all shows
    json_files = sorted(input_dir.glob("*.json"))
    shows = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                show = json.load(f)
                shows.append(show)
        except Exception as e:
            print(f"[WARN] Error loading {json_file.name}: {e}")
    
    if not shows:
        print("[WARN] No shows found to convert")
        return 0
    
    # Write JSONL file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for show in shows:
            try:
                flattened = flatten_show(show)
                # Write one JSON object per line (JSONL format)
                f.write(json.dumps(flattened, ensure_ascii=False) + '\n')
            except Exception as e:
                print(f"[ERROR] Failed to convert show: {e}")
    
    # Get file size
    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    
    print(f"[OK] Converted {len(shows)} shows to JSONL")
    print(f"[OK] Output: {output_file}")
    print(f"[OK] File size: {file_size_mb:.2f} MB")
    
    return len(shows)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Convert normalized show JSON to JSONL format for SageMaker"
    )
    
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("normalized_shows"),
        help="Input directory with normalized show JSON files"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("phish_shows.jsonl"),
        help="Output JSONL file for SageMaker"
    )
    
    args = parser.parse_args()
    
    try:
        count = convert_to_jsonl(args.input, args.output)
        if count > 0:
            print(f"\n✓ Success: {count} shows ready for SageMaker")
            return 0
        else:
            return 1
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
