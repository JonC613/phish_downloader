# Phish Shows MCP Server

An MCP (Model Context Protocol) server that provides AI assistants with access to the Phish shows database.

## Features

The server exposes 4 tools for querying Phish concert data:

### 1. `search_shows`
Search for shows by various criteria:
- **year** - Filter by specific year (e.g., 1997)
- **venue** - Search venue names (partial match)
- **city** - Filter by city
- **state** - Filter by state/province
- **tour** - Search by tour name
- **limit** - Max results (default: 50)

**Example queries:**
- "Find all shows from 1997"
- "What shows did Phish play at Madison Square Garden?"
- "List shows in Vermont"

### 2. `get_show_details`
Get complete information for a specific show including full setlist, notes, and venue details.

**Parameters:**
- **date** - Show date in YYYY-MM-DD format (required)

**Example:**
- "Show me the setlist for 12/31/1995"
- "What did Phish play on 1997-11-22?"

### 3. `search_songs`
Find all performances of a specific song across all shows.

**Parameters:**
- **song_title** - Song name to search (partial match)
- **limit** - Max results (default: 100)

**Example queries:**
- "How many times has Phish played 'You Enjoy Myself'?"
- "Find all performances of 'Tweezer'"
- "When did they play 'Harry Hood'?"

### 4. `get_statistics`
Get overall database statistics including total shows, date ranges, unique venues, and songs.

**Example:**
- "Give me stats on the Phish database"
- "How many shows are in the database?"

## Installation

1. Install MCP SDK:
```bash
pip install mcp
```

2. Configure in your MCP settings (e.g., Claude Desktop):

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "phish-shows": {
      "command": "python",
      "args": [
        "c:\\dev\\phish_downloader\\mcp_server.py"
      ]
    }
  }
}
```

3. Restart Claude Desktop

## Usage

Once configured, you can ask Claude questions like:

- "What shows did Phish play in 1997?"
- "Show me the setlist for New Year's Eve 1995"
- "How many times have they played 'Bathtub Gin'?"
- "What venues has Phish played in Colorado?"
- "Give me statistics on the Phish database"

## Data Source

The MCP server reads from the `normalized_shows/` directory containing JSON files for each show. Make sure you've run the downloader and formatter first:

```bash
# Download shows
python -m phishnet_downloader --year 2023

# Format shows
python -c "from phish_json_formatter import format_dir; from pathlib import Path; format_dir(Path('raw_shows'), Path('normalized_shows'))"
```

## Testing

Test the server directly:

```bash
# Run the server
python mcp_server.py

# Or test individual functions
python -c "from mcp_server import load_all_shows; print(len(load_all_shows()))"
```

## Future Enhancements

- Add PostgreSQL database support
- Implement song statistics (most played, etc.)
- Add venue comparison tools
- Support for setlist analysis
- Tour statistics and analysis
