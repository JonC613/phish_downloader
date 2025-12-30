"""
Streamlit app to browse Phish shows from PostgreSQL database.
"""

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import List, Dict
from datetime import datetime
import json


# Configure page
st.set_page_config(
    page_title="Phish Shows Browser",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
[data-testid="stSidebar"] {
    width: 450px !important;
}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_db_connection():
    """Get cached database connection."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        st.error("DATABASE_URL environment variable not set")
        st.stop()
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        st.error(f"Failed to connect to database: {e}")
        st.stop()


def get_years(conn) -> List[str]:
    """Get all available years from database."""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT year FROM shows ORDER BY year DESC")
    years = [str(row[0]) for row in cursor.fetchall()]
    cursor.close()
    return years


def get_shows_by_year(conn, year: int, limit: int = 50, offset: int = 0) -> tuple:
    """Get shows for a given year with pagination."""
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as cnt FROM shows WHERE year = %s", (year,))
        count_row = cursor.fetchone()
        total_count = count_row['cnt'] if count_row else 0
        
        # Get paginated results
        cursor.execute("""
            SELECT id, date, venue_name, venue_city, venue_state, 
                   tour_name, total_songs, num_sets, setlist_notes
            FROM shows
            WHERE year = %s
            ORDER BY date DESC
            LIMIT %s OFFSET %s
        """, (year, limit, offset))
        
        shows = []
        for row in cursor.fetchall():
            shows.append(dict(row))
        
        cursor.close()
        return shows, total_count
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return [], 0


def get_show_details(conn, show_id: str) -> Dict:
    """Get complete show details including songs and notes."""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get show info
    cursor.execute("SELECT * FROM shows WHERE id = %s", (show_id,))
    show = dict(cursor.fetchone())
    
    # Get songs organized by set
    cursor.execute("""
        SELECT set_number, position, title, transition, notes
        FROM songs
        WHERE show_id = %s
        ORDER BY set_number, position
    """, (show_id,))
    
    setlist = {}
    for row in cursor.fetchall():
        set_num = row['set_number']
        if set_num not in setlist:
            setlist[set_num] = []
        setlist[set_num].append(dict(row))
    
    show['setlist'] = setlist
    
    # Get notes
    cursor.execute("""
        SELECT note_type, content
        FROM notes
        WHERE show_id = %s
        ORDER BY created_at
    """, (show_id,))
    
    show['notes'] = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    return show


def display_show(conn, show_id: str, show_summary: Dict):
    """Display show details."""
    show = get_show_details(conn, show_id)
    
    # Hero section
    col1, col2 = st.columns([1, 2])
    
    with col1:
        date_display = str(show_summary['date'])
        st.markdown(f"### 📅 {date_display}")
    
    with col2:
        location = f"{show_summary['venue_name']}"
        if show_summary['venue_city']:
            location += f", {show_summary['venue_city']}"
        if show_summary['venue_state']:
            location += f", {show_summary['venue_state']}"
        st.markdown(f"### 📍 {location}")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Convert date to string if it's a date object
    date_str = str(show_summary['date'])
    year = date_str.split("-")[0]
    with col1:
        st.metric("Year", year)
    
    with col2:
        tour = show_summary['tour_name'] or "—"
        st.metric("Tour", tour)
    
    with col3:
        st.metric("Sets", show_summary['num_sets'])
    
    with col4:
        st.metric("Songs", show_summary['total_songs'])
    
    # Setlist
    st.markdown("---")
    st.markdown("## 🎸 Setlist")
    
    if show['setlist']:
        for set_num in sorted(show['setlist'].keys()):
            songs = show['setlist'][set_num]
            st.markdown(f"**Set {set_num}** — {len(songs)} songs")
            
            song_lines = []
            for song in songs:
                song_text = f"{song['position']}. {song['title']}"
                if song['transition']:
                    song_text += f" → {song['transition']}"
                if song['notes']:
                    song_text += f" *{', '.join(song['notes'])}*"
                song_lines.append(song_text)
            
            st.markdown("\n".join(song_lines))
            st.markdown("")
    else:
        st.info("No setlist information available")
    
    # Notes and metadata
    st.markdown("---")
    st.markdown("## 📋 Additional Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        curated_notes = [n for n in show['notes'] if n['note_type'] == 'curated']
        if curated_notes:
            st.markdown("### 📝 Show Notes")
            for note in curated_notes:
                st.markdown(f"• {note['content']}")
        else:
            st.info("No notes for this show")
    
    with col2:
        if show_summary['setlist_notes']:
            st.markdown("### 📚 Setlist Notes")
            st.markdown(show_summary['setlist_notes'])
        else:
            st.info("No setlist notes available")


def main():
    """Main Streamlit app."""
    conn = get_db_connection()
    
    # Header
    st.markdown('<p class="header-title">🎵 Phish Shows Database</p>', unsafe_allow_html=True)
    st.markdown('<p class="header-subtitle">Browse all recorded Phish shows from PostgreSQL</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Browser Settings")
        
        # Get years
        years = get_years(conn)
        
        if not years:
            st.error("No shows found in database")
            return
        
        # Stats
        st.markdown("---")
        st.markdown("### 📊 Collection Stats")
        
        col1, col2 = st.columns(2)
        with col1:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM shows")
            total_shows = cursor.fetchone()[0]
            cursor.close()
            st.metric("Total Shows", total_shows)
        
        with col2:
            st.metric("Years Covered", len(years))
        
        # Show selection
        st.markdown("---")
        st.markdown("### 🔍 Find a Show")
        
        selected_year = st.selectbox("Select Year", years, help="Filter shows by year")
        
        # Initialize pagination state
        if f'page_{selected_year}' not in st.session_state:
            st.session_state[f'page_{selected_year}'] = 0
        
        # Get shows for selected year with pagination
        page = st.session_state[f'page_{selected_year}']
        shows, total_count = get_shows_by_year(conn, int(selected_year), limit=50, offset=page * 50)
        
        if shows:
            # Display current shows as a list
            st.markdown(f"### 📅 Shows in {selected_year} ({total_count} total)")
            
            selected_idx = st.selectbox(
                "Select Show",
                range(len(shows)),
                format_func=lambda i: f"{shows[i]['date']} • {shows[i]['venue_name'][:40]}"
            )
            
            selected_show = shows[selected_idx]
            
            # Pagination controls
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if page > 0:
                    if st.button("← Previous"):
                        st.session_state[f'page_{selected_year}'] -= 1
                        st.rerun()
            
            with col2:
                if page < (total_count - 1) // 50:
                    if st.button("Next →"):
                        st.session_state[f'page_{selected_year}'] += 1
                        st.rerun()
            
            st.markdown("---")
            st.caption(f"Showing {len(shows)} of {total_count} shows from {selected_year}")
        else:
            st.warning("No shows in selected year")
            selected_show = None
    
    # Main content - only load details when a specific show is selected
    if 'selected_show' in locals() and selected_show:
        display_show(conn, selected_show['id'], selected_show)
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM shows")
        total = cursor.fetchone()[0]
        cursor.close()
        st.caption(f"📊 {total} total shows in database")
    
    with col2:
        st.caption("🎸 Phish Shows Browser")

    
    with col3:
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    main()
