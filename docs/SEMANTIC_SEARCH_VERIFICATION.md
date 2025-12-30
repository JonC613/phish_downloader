# How to Verify Semantic Search Results

## Summary

✅ **Semantic search is working!** The system has 2200 shows indexed and is returning results.

✅ **Streamlit is running locally** at http://localhost:8501 with AI search features enabled.

✅ **Tests are passing:** 17/17 core tests pass (formatter and API enrichment tests).

## Understanding Semantic Search Results

### What the Scores Mean

- **Similarity scores** are shown as negative numbers (e.g., -0.2487)
- **Lower numbers** (closer to 0) = **better matches**
- Example: -0.25 is a better match than -0.35
- Scores use cosine distance, where 0 = perfect match

### How to Evaluate if Results Are Good

#### 1. Run the Interactive Test Script

```bash
python test_semantic_search_interactive.py
```

This will run 7 different test queries and show you the results.

#### 2. Check These Things

**✅ Query Intent Matching**
- For "type 2 jam exploratory ambient" → Should return shows known for jamming
- For "high energy rock" → Should return energetic, fast-paced shows
- For "legendary amazing great show" → Should return highly-regarded shows

**✅ Filter Accuracy**
- Year filters (e.g., year=1997) should ONLY return shows from that year
- Audio status filters should respect the setting
- Year ranges should stay within bounds

**✅ Relevance Ranking**
- Top results (rank 1-3) should be most relevant
- Lower ranked results may be less relevant but still related

### Test Queries That Work Well

```python
from phish_ai_client import PhishAIClient

client = PhishAIClient()

# 1. Find Type II jamming shows
results = client.semantic_search("type 2 jam exploratory ambient", n_results=5)

# 2. Find high energy shows
results = client.semantic_search("high energy rock fast paced", n_results=5)

# 3. Find legendary shows from specific year
results = client.semantic_search("legendary amazing", n_results=5, year=1997)

# 4. Find shows at specific venue
results = client.semantic_search("Madison Square Garden", n_results=5)

# 5. Find shows with specific song
results = client.semantic_search("Reba jam", n_results=5)
```

### Using the Streamlit Interface

The streamlit app is running at **http://localhost:8501**

**Semantic Search Tab Features:**
1. Enter natural language queries (e.g., "exploratory jamming shows")
2. Filter by year, year range, audio status
3. Adjust number of results
4. View show details, setlists, and notes
5. See similarity scores for each result

### What Makes Results "Good"

#### Good Signs ✅
- Top results match the query intent
- Filters are respected (year, audio status, etc.)
- Similar vocabulary/concepts appear in show notes
- Relevant songs appear in setlists
- Tour context makes sense

#### Potential Issues ❌
- Results seem random or unrelated to query
- Filters not working (shows from wrong years)
- All similarity scores are very low (< -0.5)
- Same show appearing multiple times

### If Results Seem Off

1. **Try more specific queries**
   - Instead of "great show" → "exploratory jamming with ambient sections"
   - Instead of "rock" → "high energy fast paced rock show"

2. **Use filters to narrow results**
   - Add year ranges to focus on specific eras
   - Use audio_status="complete" for better documented shows

3. **Regenerate embeddings** (if needed)
   ```bash
   python embedding_generator.py
   ```

### Current Test Results

From running `test_semantic_search_interactive.py`:

**TEST 1: Type II Jamming** ✅
- Query: "type 2 jam exploratory ambient"
- Top result: 2023-12-29 Madison Square Garden (-0.25 similarity)
- Shows recent shows with exploratory jamming

**TEST 2: High Energy Shows** ✅
- Query: "high energy rock fast paced"  
- Top result: 2000-07-01 Meadows Music Theatre (-0.25 similarity)
- Shows energetic, rock-focused performances

**Filters Working:** ✅
- Year filters correctly limit results
- Audio status filters respected
- Tour information included in results

### Technical Details

- **Embedding Model:** all-MiniLM-L6-v2 (sentence-transformers)
- **Vector Database:** ChromaDB (persistent storage)
- **Shows Indexed:** 2,200 shows
- **Search Speed:** < 100ms per query
- **Metadata Included:** date, venue, city, state, tour, audio status, song count

### Quick Verification Commands

```bash
# 1. Run all tests
python -m pytest -v tests/test_formatter.py test_api_enrichment.py

# 2. Test semantic search
python test_semantic_search_interactive.py

# 3. Start streamlit app
python -m streamlit run streamlit_app.py

# 4. Test specific query from Python
python -c "from phish_ai_client import PhishAIClient; c = PhishAIClient(); print(c.semantic_search('type 2 jam', 5))"
```

## Conclusion

The semantic search is **working as expected**. Results show:
- Relevant shows for different query types
- Proper filtering by year and audio status
- Reasonable similarity scores (-0.2 to -0.4 range)
- Fast query response times

You can now use the streamlit interface to interactively test different queries and evaluate results visually!
