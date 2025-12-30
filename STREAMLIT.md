# Streamlit App - Phish Shows Browser

Interactive web app to browse and display Phish shows organized by setlist and set.

## Features

✨ **Browse Shows**
- View shows from your collection
- Filter by year
- Select specific show dates
- Display complete setlist organized by set

📊 **Show Information**
- Date, venue, location
- Tour information
- Total song count
- Notes and facts
- Full song transitions

🎵 **Setlist Display**
- Expandable sets (Set 1, Set 2, Encore, etc.)
- Song titles with transitions
- Curated notes and facts
- Metadata and provenance

## Installation

Streamlit is included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Or install just Streamlit:

```bash
pip install streamlit
```

## Usage

### Quick Start

```bash
streamlit run streamlit_app.py
```

This opens the app at `http://localhost:8501`

### Configuration

In the sidebar, you can:
- Set the **Shows Directory** (default: `test_formatted_api_shows`)
- Select a **Year** to filter shows
- Choose a specific **Show Date**

### Input Data

The app requires normalized JSON files from the formatter:

```bash
# 1. Download shows
python -m phishnet_downloader --year 1999 --output ./raw_shows

# 2. Normalize to JSON
python -m phish_json_formatter --in ./raw_shows --out ./normalized_shows

# 3. Run app pointing to normalized directory
streamlit run streamlit_app.py
# Then set Shows Directory to: ./normalized_shows
```

Or use the test data included:

```bash
streamlit run streamlit_app.py
# (defaults to test_formatted_api_shows directory)
```

## App Layout

### Sidebar
- Configuration options
- Shows directory path
- Year filter
- Show date selector
- Show count

### Main Content
- **Header**: Date, Venue, Location, Tour, Year, Total Songs
- **Setlist**: Organized by set (expandable sections)
- **Notes**: Curated notes about the show
- **Facts**: Show facts and trivia
- **Metadata**: Download time and provenance info

## Features in Detail

### Show Selection
1. Select a year from dropdown (right sidebar)
2. Choose specific show date (includes venue name)
3. Full show details and setlist display

### Setlist Organization
Each set is expandable and shows:
- Set name (Set 1, Set 2, Encore, etc.)
- Number of songs
- Song titles with transitions
- Notes on individual songs

Example display:
```
🎵 Set 1 (13 songs)
1. Divided Sky
2. Rift
3. Theme from the Bottom → Julius
...
```

### Additional Info
- **Notes**: Show-specific curated notes
- **Facts**: Historical facts about the show
- **Metadata**: API info and generation timestamps

## Running Options

### Development Mode
```bash
streamlit run streamlit_app.py
```

### Production-like Mode (no upload widget)
```bash
streamlit run streamlit_app.py --client.showErrorDetails=false
```

### Custom Port
```bash
streamlit run streamlit_app.py --server.port 8502
```

### Custom Shows Directory
Use the sidebar input field to change the directory path.

## Example Workflow

1. **Download shows:**
   ```bash
   python -m phishnet_downloader --year 1983 --output ./1983_shows
   ```

2. **Normalize:**
   ```bash
   python -m phish_json_formatter --in ./1983_shows --out ./1983_normalized
   ```

3. **Run app:**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **View shows:**
   - Enter `1983_normalized` in the Shows Directory field
   - Select year `1983`
   - Pick a show date
   - Browse the setlist!

## Troubleshooting

### "Directory not found"
Check that the Shows Directory path is correct. Use relative paths (e.g., `test_formatted_api_shows`) or absolute paths (e.g., `C:\path\to\shows`)

### "No shows found"
Verify that normalized JSON files are in the directory. Files should be named like:
- `1999-07-24_great-woods_mansfield.json`
- `1983-12-02_harris-millis-cafeteria-university-of-vermont_burlington.json`

### App not loading
Ensure Streamlit is installed:
```bash
pip install streamlit
```

### Port already in use
Use a different port:
```bash
streamlit run streamlit_app.py --server.port 8502
```

## Technical Details

### Dependencies
- `streamlit` - Web app framework
- `pandas` - Data manipulation (optional, for future stats)
- `pathlib` - File path handling
- `json` - JSON parsing

### App Structure
- `load_shows()` - Load all JSON files from directory
- `display_show()` - Render show details and setlist
- `format_song()` - Format song with transitions and notes
- `main()` - Streamlit app UI and logic

### File Naming
The app infers show information from the JSON file contents. File names like `1999-07-24_*.json` are for organization; the actual data comes from the JSON.

## Features for Future Enhancement

Possible additions:
- Search/filter songs across all shows
- Show statistics (song frequencies, tour breakdowns)
- Compare shows (setlist similarities)
- Export to CSV/PDF
- Song database with all appearances
- Show ratings and notes
- Tour view (all shows in a tour)
- Interactive timeline

## Support

For issues or feature requests:
1. Check the troubleshooting section above
2. Verify your normalized JSON files are valid
3. Check that all required fields are present in the JSON

---

**Ready to browse Phish shows!** 🎵

```bash
streamlit run streamlit_app.py
```
