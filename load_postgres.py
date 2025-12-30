"""
Load normalized Phish shows from JSON files into PostgreSQL database.
"""

import json
import os
from pathlib import Path
from typing import Dict, List
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import uuid
import sys
import time


def get_db_connection(database_url: str):
    """Get database connection with retry logic."""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(database_url)
            print("✓ Connected to PostgreSQL")
            return conn
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Connection failed, retrying in {retry_delay}s... ({attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                print(f"✗ Failed to connect after {max_retries} attempts")
                raise


def load_shows_from_directory(directory: Path) -> List[Dict]:
    """Load all normalized show JSON files from directory."""
    shows = []
    json_files = sorted(directory.glob("*.json"))
    
    print(f"Found {len(json_files)} JSON files to load")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                show = json.load(f)
                shows.append(show)
        except Exception as e:
            print(f"Warning: Error loading {json_file.name}: {e}")
    
    return shows


def insert_shows_into_db(conn, shows: List[Dict]):
    """Insert all shows and related data into PostgreSQL."""
    cursor = conn.cursor()
    
    shows_inserted = 0
    songs_inserted = 0
    notes_inserted = 0
    
    try:
        for show_data in shows:
            try:
                show_info = show_data.get("show", {})
                venue = show_info.get("venue", {})
                show_date = show_info.get("date")
                
                if not show_date:
                    print(f"Skipping show without date")
                    continue
                
                # Extract year from date
                year = int(show_date.split("-")[0])
                
                # Generate UUID for show
                show_id = str(uuid.uuid4())
                
                # Get setlist info
                setlist = show_data.get("setlist", [])
                total_songs = sum(len(s.get("songs", [])) for s in setlist)
                num_sets = len(setlist)
                
                # Get setlist notes
                notes_obj = show_data.get("notes", {})
                setlist_notes = notes_obj.get("setlist_notes")
                
                # Insert show
                cursor.execute("""
                    INSERT INTO shows 
                    (id, date, year, venue_name, venue_city, venue_state, venue_country, 
                     tour_name, total_songs, num_sets, setlist_notes, raw_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (date, venue_name) DO NOTHING
                """, (
                    show_id,
                    show_date,
                    year,
                    venue.get("name", "Unknown"),
                    venue.get("city", ""),
                    venue.get("state", ""),
                    venue.get("country", ""),
                    show_info.get("tour", ""),
                    total_songs,
                    num_sets,
                    setlist_notes,
                    json.dumps(show_data)
                ))
                
                shows_inserted += 1
                
                # Insert songs
                for set_info in setlist:
                    set_num = set_info.get("set", "")
                    for position, song in enumerate(set_info.get("songs", []), 1):
                        cursor.execute("""
                            INSERT INTO songs 
                            (show_id, set_number, position, title, transition, notes)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            show_id,
                            set_num,
                            position,
                            song.get("title", ""),
                            song.get("transition"),
                            song.get("notes", [])
                        ))
                        songs_inserted += 1
                
                # Insert notes
                curated_notes = notes_obj.get("curated", [])
                for note_text in curated_notes:
                    cursor.execute("""
                        INSERT INTO notes (show_id, note_type, content)
                        VALUES (%s, %s, %s)
                    """, (show_id, "curated", note_text))
                    notes_inserted += 1
                
                if shows_inserted % 100 == 0:
                    print(f"  Processed {shows_inserted} shows...")
                    conn.commit()
                
            except psycopg2.IntegrityError:
                # Show already exists (duplicate)
                conn.rollback()
                continue
            except Exception as e:
                print(f"Error inserting show: {e}")
                conn.rollback()
                continue
        
        # Final commit
        conn.commit()
        
        print(f"\n✓ Successfully loaded:")
        print(f"  • {shows_inserted} shows")
        print(f"  • {songs_inserted} songs")
        print(f"  • {notes_inserted} notes")
        
    finally:
        cursor.close()


def get_database_stats(conn):
    """Get and display database statistics."""
    cursor = conn.cursor()
    
    try:
        # Get show counts
        cursor.execute("SELECT COUNT(*) FROM shows")
        show_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT year) FROM shows")
        year_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM songs")
        song_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(date), MAX(date) FROM shows")
        date_range = cursor.fetchone()
        
        print("\n📊 Database Statistics:")
        print(f"  • Total shows: {show_count}")
        print(f"  • Years covered: {year_count}")
        print(f"  • Total songs: {song_count}")
        if date_range[0] and date_range[1]:
            print(f"  • Date range: {date_range[0]} to {date_range[1]}")
    
    finally:
        cursor.close()


def main():
    """Main loader function."""
    # Get configuration from environment
    database_url = os.getenv("DATABASE_URL")
    normalized_shows_dir = os.getenv("NORMALIZED_SHOWS_DIR", "normalized_shows")
    
    if not database_url:
        print("✗ DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print("🎵 Phish Shows PostgreSQL Loader")
    print("=" * 50)
    
    # Connect to database
    conn = get_db_connection(database_url)
    
    try:
        # Load shows from JSON files
        shows_dir = Path(normalized_shows_dir)
        if not shows_dir.exists():
            print(f"✗ Directory not found: {shows_dir}")
            sys.exit(1)
        
        shows = load_shows_from_directory(shows_dir)
        
        if not shows:
            print("✗ No shows found to load")
            sys.exit(1)
        
        print(f"Loading {len(shows)} shows into database...")
        
        # Insert into database
        insert_shows_into_db(conn, shows)
        
        # Display statistics
        get_database_stats(conn)
        
        print("\n✓ Database loading complete!")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
