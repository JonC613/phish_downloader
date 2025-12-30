#!/usr/bin/env python3
"""
Test syncer for phish.in API integration.
Processes a small subset to validate enrichment.
"""

import json
import logging
from pathlib import Path
from phish_in_syncer import enrich_show, ensure_output_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use test data directories
NORMALIZED_SHOWS_DIR = Path(__file__).parent.parent / "test_normalized_shows"
ENRICHED_SHOWS_DIR = Path(__file__).parent.parent / "test_api_downloads"

def test_recent_shows(max_shows: int = 10):
    """Test enrichment on recent shows (2020+)."""
    ensure_output_dir()
    
    # Get recent shows - try 2020+, fall back to any shows
    json_files = sorted(NORMALIZED_SHOWS_DIR.glob("202*.json"))[:max_shows]
    if not json_files:
        json_files = sorted(NORMALIZED_SHOWS_DIR.glob("*.json"))[:max_shows]
    
    if not json_files:
        # Skip test if no test data available
        import pytest
        pytest.skip("No normalized show files found in test data")
        return {"total": 0, "enriched": 0, "failed": 0, "skipped": 0}
    
    logger.info(f"🧪 Testing enrichment on {len(json_files)} shows...")
    
    stats = {"total": 0, "enriched": 0, "failed": 0, "skipped": 0}
    
    for idx, json_file in enumerate(json_files, 1):
        stats["total"] += 1
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                local_show = json.load(f)
            
            show_date = local_show.get("show", {}).get("date")
            logger.info(f"[{idx}/{len(json_files)}] 🔄 Testing {show_date} - {json_file.name}")
            
            # Test enrichment
            enriched = enrich_show(local_show)
            
            # Check if enrichment worked
            if enriched.get("show", {}).get("audio_status"):
                logger.info(f"✅ Enriched {show_date} - Audio: {enriched['show']['audio_status']}")
                
                # Save enriched version
                output_file = ENRICHED_SHOWS_DIR / json_file.name
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(enriched, f, indent=2, ensure_ascii=False)
                
                stats["enriched"] += 1
            else:
                logger.warning(f"⚠️ No enrichment for {show_date}")
                stats["failed"] += 1
                
        except Exception as e:
            logger.error(f"❌ Error processing {json_file.name}: {e}")
            stats["failed"] += 1
    
    # Print summary
    success_rate = (stats['enriched']/stats['total']*100) if stats['total'] > 0 else 0
    print(f"""
🎪 Test Results Summary:
=====================
Total: {stats['total']}
✅ Enriched: {stats['enriched']}
❌ Failed: {stats['failed']}
⏭️ Skipped: {stats['skipped']}
Success Rate: {success_rate:.1f}%
""")
    
    return stats

if __name__ == "__main__":
    test_recent_shows(max_shows=10)