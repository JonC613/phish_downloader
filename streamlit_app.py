"""
Modern Streamlit app to browse and display Phish shows with AI-powered search.
"""

import streamlit as st
import json
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
import random
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('streamlit_app.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("Starting Phish Shows Streamlit App")
logger.info("=" * 80)

# Configure page with custom theme
try:
    st.set_page_config(
        page_title="Phish Shows Browser",
        page_icon="🎵",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    logger.info("Page config set successfully")
except Exception as e:
    logger.error(f"Error setting page config: {e}")
    raise


def get_ai_client():
    """Lazy load AI client to avoid import issues."""
    logger.debug("get_ai_client called")
    if 'ai_client' not in st.session_state:
        logger.info("Initializing AI client...")
        try:
            from phish_ai_client import PhishAIClient
            logger.info("PhishAIClient imported")
            st.session_state.ai_client = PhishAIClient()
            st.session_state.ai_available = True
            logger.info("AI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}", exc_info=True)
            st.session_state.ai_client = None
            st.session_state.ai_available = False
            st.session_state.ai_error = str(e)
    return st.session_state.ai_client


def is_ai_available():
    """Check if AI features are available."""
    logger.debug("is_ai_available called")
    if 'ai_available' not in st.session_state:
        logger.info("Checking AI availability...")
        try:
            from phish_ai_client import PhishAIClient
            st.session_state.ai_available = True
            logger.info("AI features available")
        except Exception as e:
            logger.warning(f"AI features not available: {e}")
            st.session_state.ai_available = False
    return st.session_state.ai_available


def load_shows(directory: Path) -> Dict[str, dict]:
    """Load all show JSON files from directory (normalized or enriched)."""
    shows = {}
    
    if not directory.exists():
        st.error(f"Directory not found: {directory}")
        return shows
    
    json_files = sorted(directory.glob("*.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                show = json.load(f)
                # Use date as key for sorting
                date = show.get("show", {}).get("date", "unknown")
                shows[date] = show
        except Exception as e:
            st.warning(f"Error loading {json_file.name}: {e}")
    
    return dict(sorted(shows.items(), reverse=True))


def load_show_by_date(date: str, directory: Path = None) -> Optional[dict]:
    """Load a specific show by date."""
    if directory is None:
        directory = Path("enriched_shows")
        if not directory.exists():
            directory = Path("normalized_shows")
    
    # Try to find the show file
    for json_file in directory.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                show = json.load(f)
                if show.get("show", {}).get("date") == date:
                    return show
        except Exception:
            continue
    
    return None


def display_show(show: dict, show_context: str = ""):
    """Display a show's complete information with modern styling."""
    show_info = show.get("show", {})
    venue = show_info.get("venue", {})
    show_date = show_info.get("date", "Unknown")
    
    # Show context badge if provided (e.g., similarity score)
    if show_context:
        st.markdown(f"**{show_context}**")
    
    # Extract year from date
    year = show_date.split("-")[0] if show_date and show_date != "Unknown" else "N/A"
    
    # Hero section with date and venue
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"### 📅 {show_date}")
    
    with col2:
        venue_name = venue.get("name", "Unknown Venue")
        city = venue.get("city", "")
        state = venue.get("state", "")
        location = f"{venue_name}"
        if city:
            location += f", {city}"
        if state:
            location += f", {state}"
        st.markdown(f"### 📍 {location}")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    setlist = show.get("setlist", [])
    total_songs = sum(len(s.get("songs", [])) for s in setlist)
    
    with col1:
        st.metric("Year", year, delta=None)
    
    with col2:
        tour = show_info.get("tour", "Touring")
        st.metric("Tour", tour if tour else "—", delta=None)
    
    with col3:
        st.metric("Sets", len(setlist), delta=None)
    
    with col4:
        st.metric("Songs", total_songs, delta=None)
    
    # Setlist section
    st.markdown("---")
    st.markdown("## 🎸 Setlist")
    
    if not setlist:
        st.info("No setlist information available")
        return
    
    # Build modernized setlist display
    for set_idx, set_info in enumerate(setlist, 1):
        set_name = set_info.get("set", "Unknown")
        songs = set_info.get("songs", [])
        
        if songs:
            # Set header
            st.markdown(f"**Set {set_name}** — {len(songs)} songs")
            
            # Build song list with modernized format
            song_lines = []
            for idx, song in enumerate(songs, 1):
                song_title = song.get("title", "Unknown")
                transition = song.get("transition")
                notes = song.get("notes", [])
                
                song_text = f"{idx}. {song_title}"
                if transition:
                    song_text += f" → {transition}"
                if notes:
                    song_text += f" *{', '.join(notes)}*"
                
                song_lines.append(song_text)
            
            # Display as formatted list
            st.markdown("\n".join(song_lines))
            
            if set_idx < len(setlist):
                st.markdown("")  # Spacing between sets
    
    # Notes and facts
    st.markdown("---")
    st.markdown("## 📋 Additional Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        notes = show.get("notes", {})
        curated = notes.get("curated", [])
        if curated:
            st.markdown("### 📝 Show Notes")
            for note in curated:
                st.markdown(f"• {note}")
        else:
            st.info("No notes for this show")
    
    with col2:
        facts = show.get("facts", [])
        if facts:
            st.markdown("### 📚 Interesting Facts")
            for fact in facts:
                st.markdown(f"• {fact}")
        else:
            st.info("No facts recorded")
    
    # Metadata expander
    st.markdown("---")
    with st.expander("🔍 Show Metadata"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Venue Details**")
            venue_data = {
                "Name": venue.get("name", "Unknown"),
                "City": venue.get("city", "Unknown"),
                "State": venue.get("state", "Unknown"),
                "Country": venue.get("country", "Unknown"),
            }
            for key, val in venue_data.items():
                if val:
                    st.caption(f"{key}: {val}")
        
        with col2:
            st.markdown("**Provenance**")
            provenance = show.get("provenance", {})
            if provenance:
                st.json(provenance)


def format_song(song: dict) -> str:
    """Format a song with transition and notes."""
    title = song.get("title", "Unknown")
    transition = song.get("transition")
    notes = song.get("notes", [])
    
    text = title
    if transition:
        text += f" → {transition}"
    if notes:
        text += f" ({', '.join(notes)})"
    
    return text


def render_semantic_search_tab():
    """Render the AI-powered semantic search interface."""
    if not is_ai_available():
        st.error("❌ AI features not available")
        st.info("Run: `python embedding_generator.py` to enable semantic search")
        if 'ai_error' in st.session_state:
            st.error(f"Error: {st.session_state.ai_error}")
        return
    
    st.markdown("## 🔍 Semantic Search")
    st.markdown("Search shows using natural language descriptions")
    
    # Initialize AI client
    with st.spinner("Loading AI model..."):
        client = get_ai_client()
    
    if client is None:
        st.error("Failed to load AI client")
        return
    
    # Search mode selector
    search_mode = st.radio(
        "Search Mode",
        ["🎭 Semantic (vibes, themes, energy)", "🎵 Song Search (specific songs)"],
        horizontal=True,
        help="Semantic: Find shows by description (e.g., 'exploratory jamming')\nSong: Find shows that played a specific song (e.g., 'Guyute')"
    )
    
    is_song_mode = "Song" in search_mode
    
    # Search input
    col1, col2 = st.columns([3, 1])
    with col1:
        if is_song_mode:
            query = st.text_input(
                "Song Name",
                placeholder="e.g., 'Tweezer', 'Reba', 'You Enjoy Myself'",
                help="Enter the name of the song to search for"
            )
        else:
            query = st.text_input(
                "Search Query",
                placeholder="e.g., 'exploratory type 2 jam', 'high energy first set', 'mellow acoustic'",
                help="Describe the type of show you're looking for"
            )
    
    with col2:
        n_results = st.number_input("Results", min_value=1, max_value=50, value=10)
    
    # Filters
    with st.expander("🎛️ Filters"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            year_filter = st.selectbox(
                "Year",
                ["All"] + list(range(2025, 1982, -1)),
                help="Filter by specific year"
            )
            year = None if year_filter == "All" else year_filter
        
        with col2:
            audio_filter = st.selectbox(
                "Audio Status",
                ["All", "complete", "partial", "missing"],
                help="Filter by audio availability"
            )
            audio_status = None if audio_filter == "All" else audio_filter
        
        with col3:
            year_range_start = st.number_input("Year Start", 1983, 2025, 1983)
            year_range_end = st.number_input("Year End", 1983, 2025, 2025)
    
    # Search button
    if st.button("🔍 Search", type="primary") or query:
        if not query:
            st.warning("Please enter a search query")
        else:
            with st.spinner("Searching shows..."):
                try:
                    # Use search mode selected by user
                    if is_song_mode:
                        st.info(f"🎵 Searching for shows with: **{query}**")
                        results = client.search_by_song(
                            song_title=query,
                            n_results=n_results,
                            year=year,
                            year_start=year_range_start if year_range_start > 1983 else None,
                            year_end=year_range_end if year_range_end < 2025 else None,
                            audio_status=audio_status
                        )
                    else:
                        results = client.semantic_search(
                            query=query,
                            n_results=n_results,
                            year=year,
                            year_start=year_range_start if year_range_start > 1983 else None,
                            year_end=year_range_end if year_range_end < 2025 else None,
                            audio_status=audio_status
                        )
                    
                    if results:
                        st.success(f"Found {len(results)} shows")
                        
                        # Display results
                        for i, result in enumerate(results, 1):
                            with st.expander(
                                f"{i}. {result['date']} - {result['venue']} ({result.get('city', '')}, {result.get('state', '')}) "
                                f"- Similarity: {result['similarity_score']:.1%}"
                            ):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Date", result['date'])
                                with col2:
                                    st.metric("Audio", result['audio_status'])
                                with col3:
                                    st.metric("Songs", result.get('song_count', 'N/A'))
                                
                                st.markdown("**Preview:**")
                                st.caption(result.get('preview', 'No preview available'))
                                
                                # Load and display full show
                                if st.button(f"View Full Show", key=f"view_{result['date']}"):
                                    show = load_show_by_date(result['date'])
                                    if show:
                                        st.markdown("---")
                                        display_show(show)
                    else:
                        st.info("No shows found matching your query. Try different keywords.")
                
                except Exception as e:
                    st.error(f"Search error: {e}")


def render_similar_shows_tab():
    """Render the similar shows finder interface."""
    if not is_ai_available():
        st.error("❌ AI features not available")
        if 'ai_error' in st.session_state:
            st.error(f"Error: {st.session_state.ai_error}")
        return
    
    st.markdown("## 🎯 Find Similar Shows")
    st.markdown("Discover shows with similar musical characteristics")
    
    # Initialize AI client
    with st.spinner("Loading AI model..."):
        client = get_ai_client()
    
    if client is None:
        st.error("Failed to load AI client")
        return
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        target_date = st.text_input(
            "Show Date",
            placeholder="YYYY-MM-DD (e.g., 1997-12-31)",
            help="Enter date of a show to find similar ones"
        )
    
    with col2:
        n_results = st.number_input("Results", min_value=1, max_value=20, value=10, key="similar_n")
    
    with col3:
        exclude_tour = st.checkbox("Exclude same tour", value=True)
    
    if st.button("🔍 Find Similar", type="primary") or target_date:
        if not target_date:
            st.warning("Please enter a show date")
        else:
            with st.spinner("Finding similar shows..."):
                try:
                    results = client.find_similar_shows(
                        show_date=target_date,
                        n_results=n_results,
                        exclude_same_tour=exclude_tour
                    )
                    
                    if results:
                        # Show reference show
                        st.markdown(f"### Similar to: **{target_date}**")
                        ref_show = load_show_by_date(target_date)
                        if ref_show:
                            venue = ref_show.get('show', {}).get('venue', {})
                            st.caption(f"📍 {venue.get('name', 'Unknown')} - {venue.get('city', '')}, {venue.get('state', '')}")
                        
                        st.markdown("---")
                        st.markdown("### 🎵 Similar Shows")
                        
                        for i, result in enumerate(results, 1):
                            similarity_pct = result.get('similarity_percent', '0%')
                            with st.expander(
                                f"{i}. {result['date']} - {result['venue']} - Similarity: {similarity_pct}"
                            ):
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Date", result['date'])
                                with col2:
                                    st.metric("Similarity", similarity_pct)
                                with col3:
                                    st.metric("Audio", result['audio_status'])
                                with col4:
                                    st.metric("Tour", result.get('tour', 'N/A')[:20])
                                
                                if st.button(f"View Show", key=f"similar_{result['date']}"):
                                    show = load_show_by_date(result['date'])
                                    if show:
                                        st.markdown("---")
                                        display_show(show)
                    else:
                        st.info("No similar shows found. Check the date format (YYYY-MM-DD)")
                
                except Exception as e:
                    st.error(f"Error: {e}")


def render_random_show_tab():
    """Render random show discovery interface."""
    st.markdown("## 🎲 Random Show Discovery")
    st.markdown("Discover random shows with optional filters")
    
    # Load all shows
    enriched_dir = Path("enriched_shows")
    normalized_dir = Path("normalized_shows")
    
    directory = enriched_dir if enriched_dir.exists() else normalized_dir
    shows = load_shows(directory)
    
    if not shows:
        st.error("No shows available")
        return
    
    # Filters
    with st.expander("🎛️ Filter Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            year_filter = st.selectbox(
                "Year",
                ["All"] + list(range(2025, 1982, -1)),
                key="random_year"
            )
        
        with col2:
            # Get unique tours
            all_tours = set()
            for show in shows.values():
                tour = show.get('show', {}).get('tour')
                if tour:
                    all_tours.add(tour)
            
            tour_filter = st.selectbox(
                "Tour",
                ["All"] + sorted(all_tours),
                key="random_tour"
            )
    
    # Filter shows
    filtered_shows = shows
    if year_filter != "All":
        filtered_shows = {d: s for d, s in shows.items() if d.startswith(str(year_filter))}
    
    if tour_filter != "All":
        filtered_shows = {
            d: s for d, s in filtered_shows.items()
            if s.get('show', {}).get('tour') == tour_filter
        }
    
    st.info(f"🎯 {len(filtered_shows)} shows match your filters")
    
    if st.button("🎲 Pick Random Show", type="primary"):
        if filtered_shows:
            random_date = random.choice(list(filtered_shows.keys()))
            random_show = filtered_shows[random_date]
            
            st.balloons()
            st.markdown("---")
            display_show(random_show, show_context="🎲 Random Selection")
        else:
            st.warning("No shows match your filters")


def render_browse_tab():
    """Render the traditional browse interface."""
    logger.debug("render_browse_tab started")
    
    # Sidebar with modern layout
    with st.sidebar:
        st.markdown("## ⚙️ Browser Settings")
        
        show_dir = st.text_input(
            "Shows Directory",
            value="enriched_shows" if Path("enriched_shows").exists() else "normalized_shows",
            help="Path to directory containing show JSON files"
        )
        
        directory = Path(show_dir)
        shows = load_shows(directory)
        
        if not shows:
            st.error("❌ No shows found in directory")
            st.markdown("""
            ### Getting Started
            Make sure to run the formatter:
            ```bash
            python -m phish_json_formatter
            ```
            """)
            return
        
        # Stats section
        st.markdown("---")
        st.markdown("### 📊 Collection Stats")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Shows", len(shows))
        with col2:
            years = set(date.split("-")[0] for date in shows.keys())
            st.metric("Years Covered", len(years))
        
        # Show selection
        st.markdown("---")
        st.markdown("### 🔍 Find a Show")
        
        show_dates = list(shows.keys())
        years = sorted(set(date.split("-")[0] for date in show_dates), reverse=True)
        
        selected_year = st.selectbox(
            "Select Year",
            years,
            help="Filter shows by year",
            key="browse_year"
        )
        
        # Filter shows by year
        year_shows = {d: s for d, s in shows.items() if d.startswith(selected_year)}
        
        if year_shows:
            selected_date = st.selectbox(
                "Select Show",
                list(year_shows.keys()),
                format_func=lambda d: f"{d} • {year_shows[d].get('show', {}).get('venue', {}).get('name', 'Unknown')[:30]}",
                key="browse_show"
            )
        else:
            st.warning("No shows in selected year")
            return
        
        # Summary
        st.markdown("---")
        st.caption(f"Showing {len(year_shows)} show{'s' if len(year_shows) != 1 else ''} from {selected_year}")
    
    # Main content area
    if selected_date in shows:
        selected_show = shows[selected_date]
        display_show(selected_show)


def main():
    """Main Streamlit app with modern design."""
    logger.info("main() function called")
    
    try:
        # Custom styling
        st.markdown("""
        <style>
        .header-title {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .header-subtitle {
            font-size: 1.1rem;
            color: #666;
            margin-bottom: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        logger.info("Rendering header...")
        # Header
        st.markdown('<p class="header-title">🎵 Phish Shows Database</p>', unsafe_allow_html=True)
        st.markdown('<p class="header-subtitle">Browse, search, and explore all recorded Phish shows with AI-powered semantic search</p>', unsafe_allow_html=True)
        
        logger.info("Creating tabs...")
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📚 Browse Shows",
            "🔍 Semantic Search",
            "🎯 Similar Shows",
            "🎲 Random Show"
        ])
        
        logger.info("Rendering tabs...")
        # Tab 1: Traditional browse (existing functionality)
        with tab1:
            logger.debug("Rendering browse tab")
            render_browse_tab()
    
        # Tab 2: AI-powered semantic search
        with tab2:
            logger.debug("Rendering semantic search tab")
            render_semantic_search_tab()
        
        # Tab 3: Find similar shows
        with tab3:
            logger.debug("Rendering similar shows tab")
            render_similar_shows_tab()
        
        # Tab 4: Random show discovery
        with tab4:
            logger.debug("Rendering random show tab")
            render_random_show_tab()
        
        logger.info("All tabs rendered successfully")
        
        # Footer
        st.markdown("---")
        footer_col1, footer_col2, footer_col3 = st.columns(3)
        
        with footer_col1:
            st.caption("🎸 Phish Shows Browser v2.0")
        
        with footer_col2:
            if is_ai_available():
                st.caption("✨ AI-Powered Search Enabled")
            else:
                st.caption("⚠️ AI Search Not Available")
        
        with footer_col3:
            st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        logger.info("Main function completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main(): {e}", exc_info=True)
        st.error(f"Application Error: {e}")
        st.error("Check streamlit_app.log for details")
        raise


if __name__ == "__main__":
    logger.info("Running app as main module")
    try:
        main()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        raise
