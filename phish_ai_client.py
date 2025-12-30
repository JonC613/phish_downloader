"""
Phish AI Client

Unified client for semantic search and AI-powered queries over Phish show data.
Supports local (Ollama/LM Studio) and cloud (Bedrock) backends.

Phase 1: Semantic search using ChromaDB embeddings
Phase 2: Will add LLM integration for RAG-powered answers
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
CHROMA_PERSIST_DIR = Path("chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "phish_shows"


class AIProvider(Enum):
    """Supported AI providers for LLM queries."""
    NONE = "none"           # Semantic search only, no LLM
    OLLAMA = "ollama"       # Local Ollama
    LMSTUDIO = "lmstudio"   # Local LM Studio (OpenAI-compatible)
    BEDROCK = "bedrock"     # AWS Bedrock


class PhishAIClient:
    """
    AI client for semantic search and RAG over Phish show data.
    
    Phase 1: Semantic search with ChromaDB (implemented)
    Phase 2: RAG with LLM integration (to be implemented)
    """
    
    def __init__(self, provider: AIProvider = AIProvider.NONE):
        """
        Initialize the AI client.
        
        Args:
            provider: AI provider for LLM queries (Phase 2)
        """
        self.provider = provider
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Initialize ChromaDB
        if not CHROMA_PERSIST_DIR.exists():
            raise FileNotFoundError(
                f"ChromaDB not found at {CHROMA_PERSIST_DIR}. "
                "Run 'python embedding_generator.py' first to generate embeddings."
            )
        
        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PERSIST_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.chroma_client.get_collection(COLLECTION_NAME)
        logger.info(f"Connected to collection with {self.collection.count()} shows")
        
        # LLM client will be initialized in Phase 2
        self.llm_client = None
    
    def semantic_search(
        self,
        query: str,
        n_results: int = 10,
        year: Optional[int] = None,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        audio_status: Optional[str] = None,
        tour_name: Optional[str] = None,
        state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search over Phish shows.
        
        Args:
            query: Natural language search query
            n_results: Maximum number of results
            year: Filter to specific year
            year_start: Filter to years >= this
            year_end: Filter to years <= this  
            audio_status: Filter by audio status (complete/partial/missing)
            tour_name: Filter by tour name (partial match)
            state: Filter by state abbreviation
        
        Returns:
            List of matching shows with metadata and relevance scores
        """
        # Build where clause for filtering
        where_clauses = []
        
        if year:
            where_clauses.append({"year": {"$eq": year}})
        if year_start:
            where_clauses.append({"year": {"$gte": year_start}})
        if year_end:
            where_clauses.append({"year": {"$lte": year_end}})
        if audio_status:
            where_clauses.append({"audio_status": {"$eq": audio_status}})
        if state:
            where_clauses.append({"state": {"$eq": state.upper()}})
        
        where = None
        if len(where_clauses) == 1:
            where = where_clauses[0]
        elif len(where_clauses) > 1:
            where = {"$and": where_clauses}
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i, show_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else None
                
                # Calculate similarity score (1 - distance for cosine)
                similarity = 1 - distance if distance is not None else None
                
                formatted_results.append({
                    'show_id': show_id,
                    'date': metadata.get('date', ''),
                    'venue': metadata.get('venue_name', ''),
                    'city': metadata.get('city', ''),
                    'state': metadata.get('state', ''),
                    'tour': metadata.get('tour_name', ''),
                    'audio_status': metadata.get('audio_status', 'unknown'),
                    'song_count': metadata.get('song_count', 0),
                    'similarity_score': similarity,
                    'relevance_rank': i + 1,
                    'preview': results['documents'][0][i][:300] if results['documents'] else ''
                })
        
        return formatted_results
    
    def find_similar_shows(
        self,
        show_date: str,
        n_results: int = 10,
        exclude_same_tour: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Find shows similar to a given show.
        
        Args:
            show_date: Date of the reference show (YYYY-MM-DD format)
            n_results: Number of similar shows to return
            exclude_same_tour: If True, exclude shows from the same tour
        
        Returns:
            List of similar shows with similarity scores
        """
        # Find the show in the collection
        all_results = self.collection.get(
            include=["embeddings", "metadatas"]
        )
        
        # Find the matching show
        target_idx = None
        target_tour = None
        for i, meta in enumerate(all_results['metadatas']):
            if meta.get('date') == show_date:
                target_idx = i
                target_tour = meta.get('tour_name')
                break
        
        if target_idx is None:
            return []
        
        # Get the embedding for the target show
        target_embedding = all_results['embeddings'][target_idx]
        
        # Search for similar shows
        where = None
        if exclude_same_tour and target_tour:
            where = {"tour_name": {"$ne": target_tour}}
        
        results = self.collection.query(
            query_embeddings=[target_embedding],
            n_results=n_results + 1,  # Extra to potentially exclude self
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results, excluding the target show
        formatted_results = []
        for i, show_id in enumerate(results['ids'][0]):
            metadata = results['metadatas'][0][i]
            if metadata.get('date') == show_date:
                continue  # Skip the target show itself
            
            distance = results['distances'][0][i]
            similarity = 1 - distance
            
            formatted_results.append({
                'show_id': show_id,
                'date': metadata.get('date', ''),
                'venue': metadata.get('venue_name', ''),
                'city': metadata.get('city', ''),
                'state': metadata.get('state', ''),
                'tour': metadata.get('tour_name', ''),
                'audio_status': metadata.get('audio_status', 'unknown'),
                'similarity_score': similarity,
                'similarity_percent': f"{similarity * 100:.1f}%"
            })
            
            if len(formatted_results) >= n_results:
                break
        
        return formatted_results
    
    def search_by_song(
        self,
        song_title: str,
        n_results: int = 20,
        audio_status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find notable performances of a specific song using semantic search.
        
        This finds shows where the song appears in context with notable descriptions,
        not just any performance of the song.
        
        Args:
            song_title: Name of the song to search for
            n_results: Maximum number of results
            audio_status: Filter by audio status
        
        Returns:
            List of shows featuring notable performances of the song
        """
        # Create a query that emphasizes the song
        query = f"Notable {song_title} performance with extended jamming and improvisation"
        
        return self.semantic_search(
            query=query,
            n_results=n_results,
            audio_status=audio_status
        )
    
    def get_recommendations(
        self,
        preferences: str,
        n_results: int = 10,
        require_audio: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get show recommendations based on preferences.
        
        Args:
            preferences: Natural language description of what user wants
                e.g., "high energy shows with long jams and rare songs"
            n_results: Number of recommendations
            require_audio: Only recommend shows with complete audio
        
        Returns:
            List of recommended shows
        """
        audio_filter = "complete" if require_audio else None
        return self.semantic_search(
            query=preferences,
            n_results=n_results,
            audio_status=audio_filter
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database."""
        count = self.collection.count()
        
        if count == 0:
            return {'total_embedded': 0}
        
        # Get all metadata (ChromaDB returns all if no limit specified)
        sample = self.collection.get(
            include=["metadatas"]
        )
        
        years = set()
        audio_counts = {}
        states = set()
        tours = set()
        
        for meta in sample['metadatas']:
            if meta.get('year'):
                years.add(meta['year'])
            
            status = meta.get('audio_status', 'unknown')
            audio_counts[status] = audio_counts.get(status, 0) + 1
            
            if meta.get('state'):
                states.add(meta['state'])
            
            if meta.get('tour_name'):
                tours.add(meta['tour_name'])
        
        return {
            'total_embedded': count,
            'year_range': f"{min(years)} - {max(years)}" if years else "N/A",
            'unique_states': len(states),
            'unique_tours': len(tours),
            'audio_distribution': audio_counts,
            'provider': self.provider.value
        }


# Convenience function for quick searches
def quick_search(query: str, n: int = 5) -> List[Dict[str, Any]]:
    """Quick semantic search without full client initialization."""
    client = PhishAIClient()
    return client.semantic_search(query, n_results=n)


if __name__ == "__main__":
    # Test the client
    print("🧪 Testing Phish AI Client")
    print("=" * 50)
    
    try:
        client = PhishAIClient()
        
        # Get stats
        stats = client.get_stats()
        print(f"\n📊 Database Stats:")
        print(f"   Total shows embedded: {stats['total_embedded']}")
        print(f"   Year range: {stats['year_range']}")
        print(f"   Audio distribution: {stats['audio_distribution']}")
        
        # Test semantic search
        print("\n🔍 Test Search: 'exploratory type 2 jam'")
        results = client.semantic_search("exploratory type 2 jam", n_results=5)
        for r in results:
            print(f"   {r['date']} - {r['venue']} ({r['similarity_score']:.2%})")
        
        print("\n✅ AI Client working!")
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("   Run 'python embedding_generator.py' first!")
