"""
Phish Show Embedding Generator

Generates vector embeddings for all enriched shows and stores them in ChromaDB
for semantic search capabilities.

Usage:
    python embedding_generator.py          # Generate embeddings for all shows
    python embedding_generator.py --reset  # Reset database and regenerate all
"""

import json
import logging
from pathlib import Path
from typing import Optional
import argparse
from datetime import datetime

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
ENRICHED_SHOWS_DIR = Path("enriched_shows")
NORMALIZED_SHOWS_DIR = Path("normalized_shows")
CHROMA_PERSIST_DIR = Path("chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, good quality, 384 dimensions
COLLECTION_NAME = "phish_shows"


class PhishEmbeddingGenerator:
    """Generates and manages embeddings for Phish show data."""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # Initialize ChromaDB with persistent storage
        logger.info(f"Initializing ChromaDB at: {CHROMA_PERSIST_DIR}")
        CHROMA_PERSIST_DIR.mkdir(exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_PERSIST_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Phish show embeddings for semantic search"}
        )
        
        logger.info(f"Collection '{COLLECTION_NAME}' has {self.collection.count()} documents")
    
    def reset_collection(self):
        """Delete and recreate the collection."""
        logger.warning("Resetting collection - deleting all embeddings")
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Phish show embeddings for semantic search"}
        )
        logger.info("Collection reset complete")
    
    def load_show(self, file_path: Path) -> Optional[dict]:
        """Load a show from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None
    
    def create_show_text(self, show_data: dict) -> str:
        """
        Create a rich text representation of a show for embedding.
        This captures the essence of the show for semantic search.
        """
        parts = []
        
        # Show metadata
        show = show_data.get('show', {})
        date = show.get('date', 'Unknown date')
        venue = show.get('venue', {})
        venue_name = venue.get('name', 'Unknown venue')
        city = venue.get('city', '')
        state = venue.get('state', '')
        
        location = f"{city}, {state}" if state else city
        parts.append(f"Phish concert on {date} at {venue_name} in {location}")
        
        # Tour info
        tour_name = show.get('tour_name') or show.get('tour')
        if tour_name:
            parts.append(f"Part of {tour_name}")
        
        # Audio status
        audio_status = show.get('audio_status')
        if audio_status:
            parts.append(f"Audio status: {audio_status}")
        
        # Setlist - song titles
        setlist = show_data.get('setlist', [])
        all_songs = []
        for set_info in setlist:
            set_name = set_info.get('set', set_info.get('name', ''))
            songs = set_info.get('songs', [])
            set_songs = []
            for song in songs:
                title = song.get('title', '')
                if title:
                    set_songs.append(title)
                    all_songs.append(title)
            if set_songs:
                parts.append(f"{set_name}: {', '.join(set_songs)}")
        
        # Curated notes - most important for semantic search!
        notes = show_data.get('notes', {})
        curated_notes = notes.get('curated', [])
        if curated_notes:
            parts.append("Show notes: " + " ".join(curated_notes))
        
        # Track-level info (from phish.in enrichment)
        tracks = show_data.get('tracks', [])
        jam_tracks = []
        for track in tracks:
            if track.get('jam_starts_at_second'):
                jam_tracks.append(track.get('title', ''))
            tags = track.get('tags', [])
            if tags:
                for tag in tags:
                    if isinstance(tag, dict) and tag.get('name'):
                        parts.append(f"Tag: {tag['name']}")
        
        if jam_tracks:
            parts.append(f"Notable jams: {', '.join(jam_tracks)}")
        
        # Tags from show level
        show_tags = show.get('tags', [])
        for tag in show_tags:
            if isinstance(tag, dict) and tag.get('name'):
                tag_text = tag.get('name')
                if tag.get('description'):
                    tag_text += f" ({tag['description']})"
                parts.append(f"Recording: {tag_text}")
        
        # Taper notes (recording info)
        taper_notes = show.get('taper_notes')
        if taper_notes and len(taper_notes) < 500:  # Truncate very long taper notes
            parts.append(f"Recording notes: {taper_notes[:500]}")
        
        return "\n".join(parts)
    
    def create_show_metadata(self, show_data: dict, file_name: str) -> dict:
        """Extract metadata for filtering and retrieval."""
        show = show_data.get('show', {})
        venue = show.get('venue', {})
        
        # Extract year from date
        date = show.get('date', '')
        year = int(date[:4]) if date and len(date) >= 4 else 0
        
        # Count songs
        setlist = show_data.get('setlist', [])
        song_count = sum(len(s.get('songs', [])) for s in setlist)
        
        # Get all song titles for filtering
        all_songs = []
        for set_info in setlist:
            for song in set_info.get('songs', []):
                if song.get('title'):
                    all_songs.append(song['title'])
        
        # ChromaDB doesn't accept None values, so we use empty strings/0 as defaults
        return {
            "date": date or "",
            "year": year or 0,
            "venue_name": venue.get('name') or "",
            "city": venue.get('city') or "",
            "state": venue.get('state') or "",
            "country": venue.get('country') or "USA",
            "tour_name": show.get('tour_name') or show.get('tour') or "",
            "audio_status": show.get('audio_status') or "unknown",
            "song_count": song_count or 0,
            "file_name": file_name or "",
            "songs": ", ".join(all_songs[:50]) if all_songs else "",  # Limit for metadata storage
            "has_notes": len(show_data.get('notes', {}).get('curated', [])) > 0,
            "is_enriched": 'tracks' in show_data
        }
    
    def get_existing_ids(self) -> set:
        """Get IDs of already processed shows."""
        if self.collection.count() == 0:
            return set()
        
        # Get all IDs from collection
        results = self.collection.get()
        return set(results['ids']) if results['ids'] else set()
    
    def process_shows(self, reset: bool = False, batch_size: int = 100):
        """
        Process all shows and generate embeddings.
        
        Args:
            reset: If True, delete all existing embeddings and start fresh
            batch_size: Number of shows to process in each batch
        """
        if reset:
            self.reset_collection()
        
        # Get list of show files (prefer enriched, fall back to normalized)
        if ENRICHED_SHOWS_DIR.exists():
            show_files = list(ENRICHED_SHOWS_DIR.glob("*.json"))
            source_dir = ENRICHED_SHOWS_DIR
        else:
            show_files = list(NORMALIZED_SHOWS_DIR.glob("*.json"))
            source_dir = NORMALIZED_SHOWS_DIR
        
        logger.info(f"Found {len(show_files)} show files in {source_dir}")
        
        # Get already processed IDs for incremental updates
        existing_ids = self.get_existing_ids()
        logger.info(f"Already processed: {len(existing_ids)} shows")
        
        # Filter to only unprocessed shows
        shows_to_process = []
        for file_path in show_files:
            show_id = file_path.stem  # filename without extension
            if show_id not in existing_ids:
                shows_to_process.append(file_path)
        
        if not shows_to_process:
            logger.info("✅ All shows already processed!")
            return
        
        logger.info(f"Processing {len(shows_to_process)} new shows...")
        
        # Process in batches for efficiency
        batch_ids = []
        batch_texts = []
        batch_metadatas = []
        
        for file_path in tqdm(shows_to_process, desc="Processing shows"):
            show_data = self.load_show(file_path)
            if not show_data:
                continue
            
            show_id = file_path.stem
            show_text = self.create_show_text(show_data)
            show_metadata = self.create_show_metadata(show_data, file_path.name)
            
            batch_ids.append(show_id)
            batch_texts.append(show_text)
            batch_metadatas.append(show_metadata)
            
            # Process batch when full
            if len(batch_ids) >= batch_size:
                self._add_batch(batch_ids, batch_texts, batch_metadatas)
                batch_ids = []
                batch_texts = []
                batch_metadatas = []
        
        # Process remaining items
        if batch_ids:
            self._add_batch(batch_ids, batch_texts, batch_metadatas)
        
        logger.info(f"✅ Embedding generation complete! Total: {self.collection.count()} shows")
    
    def _add_batch(self, ids: list, texts: list, metadatas: list):
        """Add a batch of documents to the collection."""
        try:
            # Generate embeddings
            embeddings = self.model.encode(texts, show_progress_bar=False).tolist()
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
        except Exception as e:
            logger.error(f"Error adding batch: {e}")
    
    def search(self, query: str, n_results: int = 10, 
               year: Optional[int] = None,
               audio_status: Optional[str] = None) -> list:
        """
        Semantic search over shows.
        
        Args:
            query: Natural language query
            n_results: Number of results to return
            year: Filter by year (optional)
            audio_status: Filter by audio status (optional)
        
        Returns:
            List of search results with metadata and distances
        """
        # Build where clause for filtering
        where = None
        where_clauses = []
        
        if year:
            where_clauses.append({"year": year})
        if audio_status:
            where_clauses.append({"audio_status": audio_status})
        
        if len(where_clauses) == 1:
            where = where_clauses[0]
        elif len(where_clauses) > 1:
            where = {"$and": where_clauses}
        
        # Generate query embedding
        query_embedding = self.model.encode(query).tolist()
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted = []
        if results['ids'] and results['ids'][0]:
            for i, show_id in enumerate(results['ids'][0]):
                formatted.append({
                    'id': show_id,
                    'distance': results['distances'][0][i] if results['distances'] else None,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'text_preview': results['documents'][0][i][:500] if results['documents'] else ''
                })
        
        return formatted
    
    def find_similar_shows(self, show_date: str, n_results: int = 10) -> list:
        """
        Find shows similar to a given show.
        
        Args:
            show_date: Date of the show to find similar shows for (YYYY-MM-DD)
            n_results: Number of similar shows to return
        
        Returns:
            List of similar shows
        """
        # Get the show's embedding
        results = self.collection.get(
            ids=[f"{show_date}*"],
            include=["embeddings", "documents"]
        )
        
        if not results['ids']:
            # Try to find by partial match
            all_results = self.collection.get(include=["embeddings", "documents", "metadatas"])
            matching_idx = None
            for i, meta in enumerate(all_results['metadatas']):
                if meta.get('date', '').startswith(show_date):
                    matching_idx = i
                    break
            
            if matching_idx is None:
                return []
            
            query_embedding = all_results['embeddings'][matching_idx]
        else:
            query_embedding = results['embeddings'][0]
        
        # Search for similar shows (excluding the original)
        similar = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results + 1,  # Extra to exclude self
            include=["documents", "metadatas", "distances"]
        )
        
        # Format and exclude the original show
        formatted = []
        for i, show_id in enumerate(similar['ids'][0]):
            meta = similar['metadatas'][0][i]
            if meta.get('date') == show_date:
                continue
            formatted.append({
                'id': show_id,
                'distance': similar['distances'][0][i],
                'metadata': meta,
                'text_preview': similar['documents'][0][i][:500] if similar['documents'] else ''
            })
            if len(formatted) >= n_results:
                break
        
        return formatted
    
    def get_stats(self) -> dict:
        """Get statistics about the embedding database."""
        count = self.collection.count()
        
        # Sample to get metadata distribution
        if count > 0:
            sample = self.collection.get(
                limit=min(count, 1000),
                include=["metadatas"]
            )
            
            years = {}
            audio_statuses = {}
            enriched_count = 0
            
            for meta in sample['metadatas']:
                year = meta.get('year', 0)
                if year:
                    years[year] = years.get(year, 0) + 1
                
                status = meta.get('audio_status', 'unknown')
                audio_statuses[status] = audio_statuses.get(status, 0) + 1
                
                if meta.get('is_enriched'):
                    enriched_count += 1
            
            return {
                'total_shows': count,
                'years_covered': sorted(years.keys()),
                'year_distribution': years,
                'audio_status_distribution': audio_statuses,
                'enriched_percentage': (enriched_count / len(sample['metadatas'])) * 100
            }
        
        return {'total_shows': 0}


def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for Phish shows")
    parser.add_argument('--reset', action='store_true', help='Reset database and regenerate all embeddings')
    parser.add_argument('--search', type=str, help='Test search with a query')
    parser.add_argument('--similar', type=str, help='Find shows similar to date (YYYY-MM-DD)')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    args = parser.parse_args()
    
    generator = PhishEmbeddingGenerator()
    
    if args.stats:
        stats = generator.get_stats()
        print("\n📊 Embedding Database Statistics")
        print("=" * 50)
        print(f"Total shows embedded: {stats['total_shows']}")
        if stats['total_shows'] > 0:
            print(f"Years covered: {min(stats['years_covered'])} - {max(stats['years_covered'])}")
            print(f"Enriched shows: {stats['enriched_percentage']:.1f}%")
            print("\nAudio status distribution:")
            for status, count in stats['audio_status_distribution'].items():
                print(f"  {status}: {count}")
        return
    
    if args.search:
        print(f"\n🔍 Searching for: '{args.search}'")
        print("=" * 50)
        results = generator.search(args.search)
        for i, result in enumerate(results, 1):
            meta = result['metadata']
            print(f"\n{i}. {meta.get('date')} - {meta.get('venue_name')}")
            print(f"   📍 {meta.get('city')}, {meta.get('state')}")
            print(f"   🎪 {meta.get('tour_name') or 'No tour'}")
            print(f"   🔊 Audio: {meta.get('audio_status')}")
            print(f"   📏 Distance: {result['distance']:.4f}")
        return
    
    if args.similar:
        print(f"\n🎯 Finding shows similar to: {args.similar}")
        print("=" * 50)
        results = generator.find_similar_shows(args.similar)
        for i, result in enumerate(results, 1):
            meta = result['metadata']
            print(f"\n{i}. {meta.get('date')} - {meta.get('venue_name')}")
            print(f"   📍 {meta.get('city')}, {meta.get('state')}")
            print(f"   🔊 Audio: {meta.get('audio_status')}")
            print(f"   📏 Similarity: {1 - result['distance']:.2%}")
        return
    
    # Default: generate embeddings
    print("\n🚀 Starting embedding generation...")
    print("=" * 50)
    start_time = datetime.now()
    
    generator.process_shows(reset=args.reset)
    
    elapsed = datetime.now() - start_time
    print(f"\n⏱️ Completed in {elapsed}")
    
    # Show final stats
    stats = generator.get_stats()
    print(f"\n📊 Final Statistics:")
    print(f"   Total shows embedded: {stats['total_shows']}")


if __name__ == "__main__":
    main()
