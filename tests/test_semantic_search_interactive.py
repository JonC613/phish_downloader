#!/usr/bin/env python3
"""
Interactive test script for semantic search.
Helps verify that semantic search is giving desired results.
"""

from phish_ai_client import PhishAIClient
from pathlib import Path
import json

def print_result(show: dict, rank: int):
    """Pretty print a search result."""
    # Handle both dict and string (for debugging)
    if isinstance(show, str):
        print(f"\n{rank}. {show}")
        return
    
    date = show.get('date', 'Unknown')
    venue = show.get('venue', 'Unknown Venue')
    city = show.get('city', 'Unknown')
    state = show.get('state', 'Unknown')
    
    print(f"\n{rank}. {date} - {venue}")
    print(f"   Location: {city}, {state}")
    
    # Show similarity score
    if 'similarity_score' in show:
        print(f"   Similarity: {show['similarity_score']:.4f}")
    
    # Show relevance rank
    if 'relevance_rank' in show:
        print(f"   Rank: {show['relevance_rank']}")
    
    # Show tour info
    if 'tour' in show and show['tour']:
        print(f"   Tour: {show['tour']}")
    
    # Show song count
    if 'song_count' in show and show['song_count']:
        print(f"   Songs: {show['song_count']}")
    
    # Show preview
    if 'preview' in show and show['preview']:
        preview = show['preview'][:200] + "..." if len(show['preview']) > 200 else show['preview']
        print(f"   Preview: {preview}")
    
    # Show audio status
    if 'audio_status' in show:
        print(f"   Audio: {show['audio_status']}")

def test_query(client: PhishAIClient, query: str, n_results: int = 5, **filters):
    """Test a single query and display results."""
    print("\n" + "="*80)
    print(f"QUERY: '{query}'")
    if filters:
        print(f"FILTERS: {filters}")
    print("="*80)
    
    try:
        results = client.semantic_search(query, n_results=n_results, **filters)
        
        if not results:
            print("❌ No results found")
            return False
        
        print(f"\n✅ Found {len(results)} results:")
        
        for i, show in enumerate(results, 1):
            print_result(show, i)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run interactive semantic search tests."""
    print("\n" + "="*80)
    print("SEMANTIC SEARCH VERIFICATION")
    print("="*80)
    
    # Check if embeddings exist
    if not Path("chroma_db").exists():
        print("\n❌ ERROR: ChromaDB not found!")
        print("Run this first to generate embeddings:")
        print("  python embedding_generator.py")
        return
    
    print("\nInitializing AI client...")
    try:
        client = PhishAIClient()
        print(f"✅ Connected to ChromaDB with {client.collection.count()} shows")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Test 1: Type II Jamming (Classic Phish search)
    print("\n" + "="*80)
    print("TEST 1: Type II Jamming")
    print("="*80)
    print("Should return shows known for exploratory, ambient jamming")
    test_query(client, "type 2 jam exploratory ambient", n_results=5)
    
    # Test 2: High Energy Rock Shows
    print("\n" + "="*80)
    print("TEST 2: High Energy Shows")
    print("="*80)
    print("Should return energetic, rocking shows")
    test_query(client, "high energy rock fast paced", n_results=5)
    
    # Test 3: Famous Shows in a specific year
    print("\n" + "="*80)
    print("TEST 3: Great Shows from 1997")
    print("="*80)
    print("Should return highly-regarded shows from peak Phish era")
    test_query(client, "legendary amazing great show", n_results=5, year=1997)
    
    # Test 4: Venue-based search
    print("\n" + "="*80)
    print("TEST 4: Madison Square Garden Shows")
    print("="*80)
    print("Should return MSG shows (venue in metadata)")
    test_query(client, "Madison Square Garden New York", n_results=5)
    
    # Test 5: Specific song search
    print("\n" + "="*80)
    print("TEST 5: Shows with Reba")
    print("="*80)
    print("Should return shows that played Reba")
    test_query(client, "Reba jam composed section", n_results=5)
    
    # Test 6: Year range filter
    print("\n" + "="*80)
    print("TEST 6: Late 90s Exploratory Shows")
    print("="*80)
    print("Should return exploratory shows from 1995-2000")
    test_query(client, "exploratory improvisation", n_results=5, 
               year_start=1995, year_end=2000)
    
    # Test 7: Audio availability
    print("\n" + "="*80)
    print("TEST 7: Complete Audio Shows")
    print("="*80)
    print("Should only return shows with complete audio")
    test_query(client, "great jamming", n_results=5, audio_status="complete")
    
    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80)
    print("\nHow to interpret results:")
    print("• Relevance scores closer to 0 are better matches")
    print("• Check if results match the query intent")
    print("• Filters should be respected (year, audio status, etc.)")
    print("• Look for shows in notes/setlists that relate to query")
    print("\nIf results seem random or unrelated:")
    print("1. Embeddings may need regeneration")
    print("2. Query may be too vague - try more specific terms")
    print("3. ChromaDB may need reindexing")
    
    print("\nTo regenerate embeddings:")
    print("  python embedding_generator.py")

if __name__ == "__main__":
    main()
