"""
Comprehensive test suite for Phase 1 AI features.
Tests semantic search, similarity, filters, and edge cases.
"""

import sys
from pathlib import Path
from phish_ai_client import PhishAIClient, AIProvider
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name: str):
        self.passed += 1
        logger.info(f"✅ PASS: {test_name}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append((test_name, error))
        logger.error(f"❌ FAIL: {test_name}")
        logger.error(f"   Error: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total Tests: {total}")
        logger.info(f"✅ Passed: {self.passed}")
        logger.info(f"❌ Failed: {self.failed}")
        logger.info(f"Success Rate: {(self.passed/total*100):.1f}%")
        
        if self.errors:
            logger.info(f"\n{'='*60}")
            logger.info("FAILED TESTS:")
            logger.info(f"{'='*60}")
            for test_name, error in self.errors:
                logger.info(f"\n{test_name}:")
                logger.info(f"  {error}")
        
        return self.failed == 0


def test_initialization(results: TestResults):
    """Test AI client initialization."""
    logger.info("\n" + "="*60)
    logger.info("TEST CATEGORY: Initialization")
    logger.info("="*60)
    
    # Test 1: Basic initialization
    try:
        client = PhishAIClient()
        if client.collection.count() > 0:
            results.add_pass("Initialize AI client")
        else:
            results.add_fail("Initialize AI client", "Collection is empty")
    except Exception as e:
        results.add_fail("Initialize AI client", str(e))
    
    # Test 2: Check ChromaDB directory exists
    try:
        chroma_dir = Path("chroma_db")
        if chroma_dir.exists():
            results.add_pass("ChromaDB directory exists")
        else:
            results.add_fail("ChromaDB directory exists", "Directory not found")
    except Exception as e:
        results.add_fail("ChromaDB directory exists", str(e))
    
    # Test 3: Verify collection count
    try:
        client = PhishAIClient()
        count = client.collection.count()
        expected = 2200
        if count == expected:
            results.add_pass(f"Collection has {expected} shows")
        else:
            results.add_fail(f"Collection has {expected} shows", 
                           f"Found {count} shows instead")
    except Exception as e:
        results.add_fail("Collection has correct count", str(e))


def test_semantic_search(results: TestResults):
    """Test semantic search functionality."""
    logger.info("\n" + "="*60)
    logger.info("TEST CATEGORY: Semantic Search")
    logger.info("="*60)
    
    client = PhishAIClient()
    
    # Test 4: Basic search returns results
    try:
        results_list = client.semantic_search("type 2 jam", n_results=5)
        if len(results_list) > 0:
            results.add_pass("Basic semantic search returns results")
        else:
            results.add_fail("Basic semantic search returns results", "No results returned")
    except Exception as e:
        results.add_fail("Basic semantic search returns results", str(e))
    
    # Test 5: Search with year filter
    try:
        year_results = client.semantic_search("great show", n_results=5, year=1997)
        if len(year_results) > 0:
            # Verify all results are from 1997
            all_1997 = all(r.get('year') == 1997 for r in year_results)
            if all_1997:
                results.add_pass("Year filter works correctly")
            else:
                results.add_fail("Year filter works correctly", 
                               "Results contain shows from other years")
        else:
            results.add_fail("Year filter works correctly", "No results returned")
    except Exception as e:
        results.add_fail("Year filter works correctly", str(e))
    
    # Test 6: Search with year range
    try:
        range_results = client.semantic_search(
            "exploratory", n_results=10, year_start=1995, year_end=2000
        )
        if len(range_results) > 0:
            years = [r.get('year', 0) for r in range_results]
            in_range = all(1995 <= y <= 2000 for y in years if y > 0)
            if in_range:
                results.add_pass("Year range filter works")
            else:
                results.add_fail("Year range filter works", 
                               f"Found years outside range: {years}")
        else:
            results.add_fail("Year range filter works", "No results returned")
    except Exception as e:
        results.add_fail("Year range filter works", str(e))
    
    # Test 7: Search with audio status filter
    try:
        audio_results = client.semantic_search(
            "energetic show", n_results=5, audio_status="complete"
        )
        if len(audio_results) > 0:
            all_complete = all(r.get('audio_status') == 'complete' 
                             for r in audio_results)
            if all_complete:
                results.add_pass("Audio status filter works")
            else:
                results.add_fail("Audio status filter works", 
                               "Results contain non-complete audio")
        else:
            results.add_fail("Audio status filter works", "No results returned")
    except Exception as e:
        results.add_fail("Audio status filter works", str(e))
    
    # Test 8: Empty query handling
    try:
        empty_results = client.semantic_search("", n_results=5)
        # Should still return results (even if less relevant)
        results.add_pass("Empty query handled gracefully")
    except Exception as e:
        results.add_fail("Empty query handled gracefully", str(e))
    
    # Test 9: Very long query
    try:
        long_query = "exploratory ambient type 2 jamming with great energy " * 10
        long_results = client.semantic_search(long_query, n_results=3)
        if len(long_results) > 0:
            results.add_pass("Long query handled")
        else:
            results.add_fail("Long query handled", "No results returned")
    except Exception as e:
        results.add_fail("Long query handled", str(e))
    
    # Test 10: Special characters in query
    try:
        special_results = client.semantic_search("rock & roll!", n_results=3)
        results.add_pass("Special characters in query handled")
    except Exception as e:
        results.add_fail("Special characters in query handled", str(e))


def test_similar_shows(results: TestResults):
    """Test find similar shows functionality."""
    logger.info("\n" + "="*60)
    logger.info("TEST CATEGORY: Similar Shows")
    logger.info("="*60)
    
    client = PhishAIClient()
    
    # Test 11: Find similar shows for valid date
    try:
        similar = client.find_similar_shows("1997-12-31", n_results=5)
        if len(similar) > 0:
            # Should not include the target show itself
            contains_self = any(s.get('date') == '1997-12-31' for s in similar)
            if not contains_self:
                results.add_pass("Similar shows returns valid results")
            else:
                results.add_fail("Similar shows returns valid results", 
                               "Results include target show")
        else:
            results.add_fail("Similar shows returns valid results", "No results returned")
    except Exception as e:
        results.add_fail("Similar shows returns valid results", str(e))
    
    # Test 12: Similar shows with invalid date
    try:
        similar = client.find_similar_shows("9999-99-99", n_results=5)
        if len(similar) == 0:
            results.add_pass("Invalid date returns empty results")
        else:
            results.add_fail("Invalid date returns empty results", 
                           "Should return empty list")
    except Exception as e:
        results.add_fail("Invalid date returns empty results", str(e))
    
    # Test 13: Similar shows with exclude_same_tour
    try:
        with_tour = client.find_similar_shows(
            "1997-12-31", n_results=10, exclude_same_tour=True
        )
        if len(with_tour) > 0:
            # Check that no results are from "New Years Run 1997"
            tours = [s.get('tour', '') for s in with_tour]
            has_same_tour = any('1997' in tour and 'New Year' in tour 
                              for tour in tours)
            if not has_same_tour:
                results.add_pass("Exclude same tour works")
            else:
                results.add_fail("Exclude same tour works", 
                               f"Found same tour in results: {tours}")
        else:
            results.add_fail("Exclude same tour works", "No results returned")
    except Exception as e:
        results.add_fail("Exclude same tour works", str(e))


def test_song_search(results: TestResults):
    """Test song-based search functionality."""
    logger.info("\n" + "="*60)
    logger.info("TEST CATEGORY: Song-Based Search")
    logger.info("="*60)
    
    client = PhishAIClient()
    
    # Test 14: Search by popular song
    try:
        song_results = client.search_by_song("Tweezer", n_results=5)
        if len(song_results) > 0:
            results.add_pass("Song search returns results")
        else:
            results.add_fail("Song search returns results", "No results returned")
    except Exception as e:
        results.add_fail("Song search returns results", str(e))
    
    # Test 15: Search by less common song
    try:
        rare_results = client.search_by_song("Icculus", n_results=3)
        # Should return results even if fewer than requested
        results.add_pass("Rare song search handled")
    except Exception as e:
        results.add_fail("Rare song search handled", str(e))


def test_recommendations(results: TestResults):
    """Test recommendation functionality."""
    logger.info("\n" + "="*60)
    logger.info("TEST CATEGORY: Recommendations")
    logger.info("="*60)
    
    client = PhishAIClient()
    
    # Test 16: Basic recommendations
    try:
        recs = client.get_recommendations(
            "high energy jamming", n_results=5, require_audio=False
        )
        if len(recs) > 0:
            results.add_pass("Basic recommendations work")
        else:
            results.add_fail("Basic recommendations work", "No results returned")
    except Exception as e:
        results.add_fail("Basic recommendations work", str(e))
    
    # Test 17: Recommendations with audio requirement
    try:
        audio_recs = client.get_recommendations(
            "mellow acoustic", n_results=5, require_audio=True
        )
        if len(audio_recs) > 0:
            all_complete = all(r.get('audio_status') == 'complete' 
                             for r in audio_recs)
            if all_complete:
                results.add_pass("Audio requirement in recommendations works")
            else:
                results.add_fail("Audio requirement in recommendations works",
                               "Found non-complete audio in results")
        else:
            results.add_fail("Audio requirement in recommendations works", 
                           "No results returned")
    except Exception as e:
        results.add_fail("Audio requirement in recommendations works", str(e))


def test_statistics(results: TestResults):
    """Test statistics functionality."""
    logger.info("\n" + "="*60)
    logger.info("TEST CATEGORY: Statistics")
    logger.info("="*60)
    
    client = PhishAIClient()
    
    # Test 18: Get stats
    try:
        stats = client.get_stats()
        required_keys = ['total_embedded', 'year_range', 'audio_distribution']
        has_keys = all(key in stats for key in required_keys)
        if has_keys and stats['total_embedded'] > 0:
            results.add_pass("Statistics retrieval works")
        else:
            results.add_fail("Statistics retrieval works", 
                           f"Missing keys or invalid data: {stats}")
    except Exception as e:
        results.add_fail("Statistics retrieval works", str(e))
    
    # Test 19: Verify year range format
    try:
        stats = client.get_stats()
        year_range = stats.get('year_range', '')
        if '-' in year_range:
            start, end = year_range.split(' - ')
            if int(start) <= int(end):
                results.add_pass("Year range format is correct")
            else:
                results.add_fail("Year range format is correct", 
                               f"Invalid range: {year_range}")
        else:
            results.add_fail("Year range format is correct", 
                           f"Invalid format: {year_range}")
    except Exception as e:
        results.add_fail("Year range format is correct", str(e))


def test_data_quality(results: TestResults):
    """Test data quality and completeness."""
    logger.info("\n" + "="*60)
    logger.info("TEST CATEGORY: Data Quality")
    logger.info("="*60)
    
    client = PhishAIClient()
    
    # Test 20: All shows have required metadata
    try:
        sample_results = client.semantic_search("show", n_results=50)
        required_fields = ['date', 'venue', 'city']
        
        missing_data = []
        for show in sample_results:
            for field in required_fields:
                if not show.get(field):
                    missing_data.append(f"{show.get('show_id', 'unknown')}: {field}")
        
        if len(missing_data) == 0:
            results.add_pass("All shows have required metadata")
        else:
            results.add_fail("All shows have required metadata", 
                           f"Missing data: {missing_data[:5]}")
    except Exception as e:
        results.add_fail("All shows have required metadata", str(e))
    
    # Test 21: Similarity scores are valid
    try:
        similar = client.find_similar_shows("1997-12-31", n_results=10)
        scores = [s.get('similarity_score', -1) for s in similar]
        valid_scores = all(0 <= score <= 1 for score in scores)
        
        if valid_scores:
            results.add_pass("Similarity scores in valid range (0-1)")
        else:
            results.add_fail("Similarity scores in valid range (0-1)", 
                           f"Invalid scores: {scores}")
    except Exception as e:
        results.add_fail("Similarity scores in valid range (0-1)", str(e))


def test_performance(results: TestResults):
    """Test performance characteristics."""
    logger.info("\n" + "="*60)
    logger.info("TEST CATEGORY: Performance")
    logger.info("="*60)
    
    import time
    client = PhishAIClient()
    
    # Test 22: Search completes in reasonable time
    try:
        start = time.time()
        client.semantic_search("jamming", n_results=10)
        duration = time.time() - start
        
        if duration < 2.0:  # Should complete in under 2 seconds
            results.add_pass(f"Search performance acceptable ({duration:.2f}s)")
        else:
            results.add_fail("Search performance acceptable", 
                           f"Took {duration:.2f}s (expected < 2s)")
    except Exception as e:
        results.add_fail("Search performance acceptable", str(e))
    
    # Test 23: Multiple rapid searches don't break
    try:
        for i in range(5):
            client.semantic_search(f"test query {i}", n_results=3)
        results.add_pass("Rapid consecutive searches work")
    except Exception as e:
        results.add_fail("Rapid consecutive searches work", str(e))


def test_persistence(results: TestResults):
    """Test ChromaDB persistence."""
    logger.info("\n" + "="*60)
    logger.info("TEST CATEGORY: Persistence")
    logger.info("="*60)
    
    # Test 24: Can reconnect to existing collection
    try:
        client1 = PhishAIClient()
        count1 = client1.collection.count()
        
        # Create new client instance
        client2 = PhishAIClient()
        count2 = client2.collection.count()
        
        if count1 == count2:
            results.add_pass("ChromaDB persistence works")
        else:
            results.add_fail("ChromaDB persistence works", 
                           f"Counts differ: {count1} vs {count2}")
    except Exception as e:
        results.add_fail("ChromaDB persistence works", str(e))


def main():
    """Run all tests."""
    logger.info("🧪 PHISH AI FEATURES - COMPREHENSIVE TEST SUITE")
    logger.info("="*60)
    
    # Check prerequisites
    enriched_dir = Path("enriched_shows")
    chroma_dir = Path("chroma_db")
    
    if not enriched_dir.exists():
        logger.error("❌ enriched_shows directory not found!")
        logger.error("   Run the phish.in syncer first")
        sys.exit(1)
    
    if not chroma_dir.exists():
        logger.error("❌ chroma_db directory not found!")
        logger.error("   Run: python embedding_generator.py")
        sys.exit(1)
    
    results = TestResults()
    
    # Run all test categories
    try:
        test_initialization(results)
        test_semantic_search(results)
        test_similar_shows(results)
        test_song_search(results)
        test_recommendations(results)
        test_statistics(results)
        test_data_quality(results)
        test_performance(results)
        test_persistence(results)
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        logger.error(f"\n\n❌ Unexpected error during testing: {e}")
    
    # Print summary
    success = results.summary()
    
    if success:
        logger.info("\n🎉 All tests passed! Phase 1 is production-ready.")
        sys.exit(0)
    else:
        logger.info("\n⚠️  Some tests failed. Review errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
