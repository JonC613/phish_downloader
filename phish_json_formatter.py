"""
Phish show JSON formatter: Converts raw API JSON to normalized schema.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# Field Mapping: Flexible extraction from raw JSON
# ============================================================================

def _extract_date(raw: dict) -> Optional[str]:
    """Extract show date (YYYY-MM-DD format)."""
    candidates = ["date", "showDate", "show_date", "event_date", "eventDate", "showdate"]
    for key in candidates:
        if key in raw and raw[key]:
            value = raw[key]
            if isinstance(value, str):
                # Try to parse and reformat as YYYY-MM-DD
                if len(value) == 10 and value[4] == "-" and value[7] == "-":
                    return value
            return str(value)[:10]  # Fallback: take first 10 chars
    return None


def _extract_venue_name(raw: dict) -> Optional[str]:
    """Extract venue name."""
    candidates = ["venue", "venueName", "venue_name", "location"]
    for key in candidates:
        if key in raw and raw[key]:
            return str(raw[key]).strip()
    return None


def _extract_city(raw: dict) -> Optional[str]:
    """Extract city."""
    candidates = ["city", "venue_city", "venueCity"]
    for key in candidates:
        if key in raw and raw[key]:
            return str(raw[key]).strip()
    return None


def _extract_state(raw: dict) -> Optional[str]:
    """Extract state/province."""
    candidates = ["state", "province", "venue_state", "venueState"]
    for key in candidates:
        if key in raw and raw[key]:
            return str(raw[key]).strip()
    return None


def _extract_country(raw: dict) -> Optional[str]:
    """Extract country."""
    candidates = ["country", "venue_country", "venueCountry"]
    for key in candidates:
        if key in raw and raw[key]:
            return str(raw[key]).strip()
    return "USA"  # Default to USA for Phish


def _extract_coordinates(raw: dict) -> tuple[Optional[float], Optional[float]]:
    """Extract latitude and longitude."""
    lat = None
    lon = None
    
    for key in ["lat", "latitude", "venue_lat", "venueLat"]:
        if key in raw and raw[key] is not None:
            try:
                lat = float(raw[key])
            except (ValueError, TypeError):
                pass
            break
    
    for key in ["lon", "longitude", "lng", "venue_lon", "venueLon"]:
        if key in raw and raw[key] is not None:
            try:
                lon = float(raw[key])
            except (ValueError, TypeError):
                pass
            break
    
    return lat, lon


def _extract_tour(raw: dict) -> Optional[str]:
    """Extract tour name."""
    candidates = ["tour", "tour_name", "tourName"]
    for key in candidates:
        if key in raw and raw[key]:
            return str(raw[key]).strip()
    return None


def _extract_show_id(raw: dict, fallback: str) -> str:
    """Extract show ID, prefer API id, else use fallback."""
    candidates = ["id", "show_id", "showId", "api_id", "apiId"]
    for key in candidates:
        if key in raw and raw[key]:
            return str(raw[key]).strip()
    return fallback


def _extract_setlist(raw: dict) -> List[Dict[str, Any]]:
    """Extract setlist structure."""
    setlist = []
    
    # Look for setlist in various keys
    setlist_data = None
    for key in ["setlist", "sets", "song_sets", "songSets"]:
        if key in raw:
            setlist_data = raw[key]
            break
    
    if not setlist_data:
        return setlist
    
    if isinstance(setlist_data, list):
        for set_item in setlist_data:
            set_dict = _normalize_set(set_item)
            if set_dict:
                setlist.append(set_dict)
    elif isinstance(setlist_data, dict):
        for set_name, songs in setlist_data.items():
            set_dict = _normalize_set_dict(set_name, songs)
            if set_dict:
                setlist.append(set_dict)
    
    return setlist


def _normalize_set(set_item: Any) -> Optional[Dict[str, Any]]:
    """Normalize a single set (dict or list format)."""
    if isinstance(set_item, dict):
        name = set_item.get("name") or set_item.get("setName") or "Set"
        songs_data = set_item.get("songs") or set_item.get("tracks") or []
    elif isinstance(set_item, list):
        # Assume list of songs
        name = "Set"
        songs_data = set_item
    else:
        return None
    
    songs = []
    if isinstance(songs_data, list):
        for song_item in songs_data:
            song = _normalize_song(song_item)
            if song:
                songs.append(song)
    
    return {"set": name, "songs": songs} if songs else None


def _normalize_set_dict(set_name: str, songs_data: Any) -> Optional[Dict[str, Any]]:
    """Normalize set from dict format."""
    if not isinstance(songs_data, list):
        songs_data = []
    
    songs = []
    for song_item in songs_data:
        song = _normalize_song(song_item)
        if song:
            songs.append(song)
    
    return {"set": set_name, "songs": songs} if songs else None


def _normalize_song(song_item: Any) -> Optional[Dict[str, Any]]:
    """Normalize a single song."""
    if isinstance(song_item, str):
        # Just a title
        title = song_item.strip()
    elif isinstance(song_item, dict):
        title = song_item.get("title") or song_item.get("name") or song_item.get("song")
        if not title:
            return None
        title = str(title).strip()
    else:
        return None
    
    # Extract transition (look for "->", ">", or explicit field)
    transition = None
    if isinstance(song_item, dict):
        if "transition" in song_item:
            t = song_item.get("transition")
            if t in ("->", ">", "jam"):
                transition = "->"
        elif song_item.get("jam_to_next") or song_item.get("jamToNext"):
            transition = "->"
    
    # Extract notes
    notes = []
    if isinstance(song_item, dict):
        for key in ["notes", "note", "comment"]:
            if key in song_item and song_item[key]:
                n = song_item[key]
                if isinstance(n, list):
                    notes.extend(str(x).strip() for x in n if x)
                else:
                    notes.append(str(n).strip())
    
    return {
        "title": title,
        "transition": transition,
        "notes": notes
    }


def _extract_notes(raw: dict) -> Dict[str, Any]:
    """Extract curated notes and fan comments."""
    notes = {
        "curated": [],
        "fan_comments": []
    }
    
    # Curated notes
    for key in ["notes", "curated_notes", "curatedNotes", "facts", "setlist_notes"]:
        if key in raw and raw[key]:
            items = raw[key]
            if isinstance(items, list):
                notes["curated"].extend(str(x).strip() for x in items if x)
            elif isinstance(items, str):
                # Strip HTML tags if present (setlist_notes often contains HTML)
                text = str(items).strip()
                # Remove HTML tags: <p>, </p>, <em>, </em>, etc.
                import re as html_re
                import html as html_module
                text = html_re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
                text = html_module.unescape(text)  # Decode HTML entities
                text = html_re.sub(r'\r\n', ' ', text)  # Remove line breaks
                text = html_re.sub(r'\s+', ' ', text)  # Collapse whitespace
                text = text.strip()
                if text:
                    notes["curated"].append(text)
    
    # Fan comments
    for key in ["fan_comments", "fanComments", "comments", "reviews"]:
        if key in raw and raw[key]:
            items = raw[key]
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        fan_comment = {
                            "source": item.get("source") or "unknown",
                            "author": item.get("author") or item.get("name"),
                            "date": item.get("date"),
                            "text": item.get("text") or item.get("comment") or "",
                            "url": item.get("url")
                        }
                        notes["fan_comments"].append(fan_comment)
    
    return notes


def _extract_facts(raw: dict) -> List[Dict[str, Any]]:
    """Extract facts."""
    facts = []
    
    for key in ["facts", "trivia", "notable_moments"]:
        if key in raw and raw[key]:
            items = raw[key]
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        facts.append({
                            "label": item.get("label") or item.get("title") or "",
                            "detail": item.get("detail") or item.get("description"),
                            "source_url": item.get("source_url") or item.get("sourceUrl")
                        })
                    elif isinstance(item, str):
                        facts.append({
                            "label": item.strip(),
                            "detail": None,
                            "source_url": None
                        })
    
    return facts


def _extract_sources(raw: dict, input_filename: str) -> List[Dict[str, Any]]:
    """Extract source information."""
    sources = []
    
    # Look for explicit sources
    if "sources" in raw and isinstance(raw["sources"], list):
        for src in raw["sources"]:
            if isinstance(src, dict):
                sources.append({
                    "type": src.get("type", "other"),
                    "url": src.get("url"),
                    "retrieved_at": src.get("retrieved_at") or src.get("retrievedAt")
                })
    
    # Look for API source
    if "api_url" in raw or "apiUrl" in raw:
        url = raw.get("api_url") or raw.get("apiUrl")
        sources.append({
            "type": "api",
            "url": url,
            "retrieved_at": raw.get("downloaded_at") or raw.get("downloadedAt") or datetime.now(timezone.utc).isoformat()
        })
    
    return sources


# ============================================================================
# Normalization
# ============================================================================

def normalize_show(raw: dict, input_filename: str) -> dict:
    """
    Convert raw show JSON to normalized schema.
    
    Args:
        raw: Raw show data dictionary
        input_filename: Name/path of input file (for provenance)
    
    Returns:
        Normalized show dictionary
    
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Extract core fields
    date = _extract_date(raw)
    venue_name = _extract_venue_name(raw)
    city = _extract_city(raw)
    state = _extract_state(raw)
    country = _extract_country(raw)
    lat, lon = _extract_coordinates(raw)
    tour = _extract_tour(raw)
    
    # Validate required fields
    if not date:
        raise ValueError("Missing required field: date")
    if not venue_name:
        raise ValueError("Missing required field: venue name")
    if not city:
        raise ValueError("Missing required field: city")
    
    # Generate stable ID
    fallback_id = f"{date}_{_slugify(venue_name)}_{_slugify(city + (state or ''))}"
    show_id = _extract_show_id(raw, fallback_id)
    
    # Extract sub-structures
    setlist = _extract_setlist(raw)
    notes = _extract_notes(raw)
    facts = _extract_facts(raw)
    sources = _extract_sources(raw, input_filename)
    
    # Detect API name from raw data
    api_name = raw.get("api", raw.get("source", "unknown"))
    
    # Build normalized document
    normalized = {
        "schema_version": "2.0",
        "show": {
            "id": show_id,
            "date": date,
            "tour": tour,
            "venue": {
                "name": venue_name,
                "city": city,
                "state": state,
                "country": country,
                "lat": lat,
                "lon": lon
            }
        },
        "setlist": setlist,
        "notes": notes,
        "facts": facts,
        "sources": sources,
        "provenance": {
            "raw_input": {
                "filename": str(input_filename),
                "api": api_name,
                "downloaded_at": raw.get("downloaded_at") or raw.get("downloadedAt")
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "phish-json-formatter"
        }
    }
    
    return normalized


def _slugify(text: str) -> str:
    """Convert text to slug."""
    if not text:
        return "unknown"
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text


def validate_normalized(data: dict) -> None:
    """
    Validate normalized document structure.
    
    Raises:
        ValueError: If validation fails
    """
    # Check top-level keys
    required_keys = ["schema_version", "show", "setlist", "notes", "facts", "sources", "provenance"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required top-level key: {key}")
    
    # Check show object
    show = data["show"]
    required_show_keys = ["id", "date", "venue"]
    for key in required_show_keys:
        if key not in show:
            raise ValueError(f"Missing required show field: {key}")
    
    # Validate date format
    if not _is_valid_date(show["date"]):
        raise ValueError(f"Invalid date format: {show['date']}")
    
    # Check venue object
    venue = show["venue"]
    if "name" not in venue or not venue["name"]:
        raise ValueError("Missing required venue.name")
    if "city" not in venue or not venue["city"]:
        raise ValueError("Missing required venue.city")
    
    # Check provenance
    if "provenance" not in data or "raw_input" not in data["provenance"]:
        raise ValueError("Missing provenance.raw_input")


def _is_valid_date(date_str: str) -> bool:
    """Check if date is in YYYY-MM-DD format."""
    if not isinstance(date_str, str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# ============================================================================
# File Operations
# ============================================================================

def format_file(input_path: Path, output_path: Path) -> None:
    """
    Format a single JSON file.
    
    Args:
        input_path: Path to raw JSON file
        output_path: Path for normalized JSON output
    
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If normalization fails
        json.JSONDecodeError: If JSON is invalid
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load raw JSON
    with open(input_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    
    # Normalize
    normalized = normalize_show(raw, input_path.name)
    
    # Validate
    validate_normalized(normalized)
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")  # Trailing newline


def format_dir(input_dir: Path, output_dir: Path) -> None:
    """
    Recursively format all JSON files in a directory.
    
    Args:
        input_dir: Input directory
        output_dir: Output directory
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input is not a directory: {input_dir}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all JSON files recursively
    json_files = list(input_dir.rglob("*.json"))
    
    for input_file in json_files:
        try:
            # Calculate relative output path
            rel_path = input_file.relative_to(input_dir)
            output_file = output_dir / rel_path
            
            format_file(input_file, output_file)
            print(f"[OK] {input_file.name} -> {output_file.name}")
        except Exception as e:
            print(f"[ERROR] {input_file.name}: {e}")
