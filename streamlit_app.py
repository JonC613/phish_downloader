"""
Modern Streamlit app to browse and display Phish shows.
"""

import streamlit as st
import json
from pathlib import Path
from typing import Dict, List
import pandas as pd
from datetime import datetime


# Configure page with custom theme
st.set_page_config(
    page_title="Phish Shows Browser",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_shows(directory: Path) -> Dict[str, dict]:
    """Load all normalized show JSON files from directory."""
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


def display_show(show: dict):
    """Display a show's complete information with modern styling."""
    show_info = show.get("show", {})
    venue = show_info.get("venue", {})
    show_date = show_info.get("date", "Unknown")
    
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


def main():
    """Main Streamlit app with modern design."""
    
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
    
    # Header
    st.markdown('<p class="header-title">🎵 Phish Shows Database</p>', unsafe_allow_html=True)
    st.markdown('<p class="header-subtitle">Browse and explore all recorded Phish shows</p>', unsafe_allow_html=True)
    
    # Sidebar with modern layout
    with st.sidebar:
        st.markdown("## ⚙️ Browser Settings")
        
        show_dir = st.text_input(
            "Shows Directory",
            value="normalized_shows",
            help="Path to directory containing normalized show JSON files"
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
            help="Filter shows by year"
        )
        
        # Filter shows by year
        year_shows = {d: s for d, s in shows.items() if d.startswith(selected_year)}
        
        if year_shows:
            selected_date = st.selectbox(
                "Select Show",
                list(year_shows.keys()),
                format_func=lambda d: f"{d} • {year_shows[d].get('show', {}).get('venue', {}).get('name', 'Unknown')[:30]}"
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
    
    # Footer
    st.markdown("---")
    footer_col1, footer_col2, footer_col3 = st.columns(3)
    
    with footer_col1:
        st.caption(f"📊 {len(shows)} total shows in collection")
    
    with footer_col2:
        st.caption("🎸 Phish Shows Browser")
    
    with footer_col3:
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    main()
