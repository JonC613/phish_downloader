# Phish Show Database & AI Search

A comprehensive database and AI-powered search system for Phish concert data, featuring semantic search, embeddings, and an interactive Streamlit interface.

## 🎯 Overview

This project creates the most complete Phish show database by combining data from multiple sources:
- **phish.net API**: Complete setlist and show information
- **phish.in API**: Audio availability, MP3 URLs, and enhanced metadata  
- **Normalized processing**: Standardized data format for consistency
- **Semantic Search**: AI-powered search using vector embeddings
- **MCP Server**: AI assistant integration with enhanced search capabilities

## 📁 Repository Structure

```
phish_downloader/
├── docs/                    # Documentation files
│   ├── QUICKSTART.md
│   ├── SEMANTIC_SEARCH_VERIFICATION.md
│   └── ...
├── scripts/                 # Utility scripts
│   ├── batch_download.py
│   ├── enrich_with_phish_in.py
│   └── ...
├── tests/                   # Test files
│   ├── test_formatter.py
│   ├── test_semantic_search_interactive.py
│   └── ...
├── test_data/              # Test JSON files
├── enriched_shows/         # Enriched show data (2,200 shows)
├── normalized_shows/       # Normalized show data
├── raw_shows/              # Raw show data from APIs
├── chroma_db/              # Vector database for semantic search
│
├── phish_ai_client.py      # AI/semantic search client
├── phishnet_downloader.py  # PhishNet API client
├── phish_in_api_client.py  # Phish.in API client
├── phish_json_formatter.py # JSON normalization
├── embedding_generator.py  # Generate vector embeddings
├── streamlit_app.py        # Web UI (local data)
├── streamlit_app_postgres.py # Web UI (PostgreSQL)
├── mcp_server.py           # MCP server for Claude
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 📊 Current Database Status

- **2,202 Total Shows**: Complete Phish discography (1983-2025)
- **2,200 Enriched Shows**: 99.9% enhanced with phish.in audio metadata
- **1,691 Shows with Complete Audio**: 76.8% have full recordings available
- **123 Tours Identified**: Complete tour information and context

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   phish.net     │    │ JSON Formatter   │    │  phish.in API   │
│   Downloads     │───▶│  Normalizer      │───▶│   Enricher      │
│  (raw_shows)    │    │(normalized_shows)│    │(enriched_shows) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                  │
                                  ▼
                       ┌─────────────────┐
                       │ Enhanced MCP    │
                       │     Server      │
                       └─────────────────┘
                                  │
                                  ▼
                       ┌─────────────────┐
                       │ Claude Desktop  │
                       │  Integration    │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment recommended

### Installation

```bash
# Clone and setup
git clone <repository>
cd phish_downloader

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### Download Complete Dataset

```bash
# Download all shows from phish.net (takes ~30 minutes)
python -m phishnet_downloader --all

# Format raw data into normalized structure
python -c "from phish_json_formatter import format_dir; from pathlib import Path; format_dir(Path('raw_shows'), Path('normalized_shows'))"

# Enrich with phish.in audio metadata (takes ~3-4 hours)
python phish_in_syncer.py
```

### Start MCP Server

```bash
# Test the enhanced MCP server
python test_enriched_features.py

# Run MCP server
python mcp_server_enhanced.py
```

## 📦 Core Components

### 1. Phish.net Downloader (`phishnet_downloader.py`)
- Downloads complete show data from phish.net API
- Supports year-by-year or complete dataset download
- Automatic rate limiting and error handling
- Creates `raw_shows/` directory with JSON files

```bash
# Download specific years
python -m phishnet_downloader --year 2023 --year 2024

# Download everything  
python -m phishnet_downloader --all
```

### 2. JSON Formatter (`phish_json_formatter.py`)
- Normalizes raw phish.net data into consistent schema
- Handles field mapping and data validation
- Generates stable show IDs and provenance tracking
- Creates `normalized_shows/` directory

### 3. Phish.in API Client (`phish_in_api_client.py`)
- HTTP client for phish.in API v2 with rate limiting
- Fetches audio metadata, MP3 URLs, and tour information
- Handles 404 errors gracefully for missing shows
- Provides comprehensive show enhancement data

### 4. Phish.in Syncer (`phish_in_syncer.py`)
- Enriches normalized shows with phish.in API data
- Processes all shows chronologically with checkpoints
- Adds audio status, duration, MP3 URLs, tour names, tags
- Creates `enriched_shows/` directory with enhanced metadata

### 5. Enhanced MCP Server (`mcp_server_enhanced.py`)
- Model Context Protocol server for AI assistant integration
- 6 tools supporting both normalized and enriched data
- Audio search, statistics, show details, and setlist queries
- Automatic fallback between enriched and normalized data

## 🎵 Enhanced Features

### Audio Information
- **Audio Status**: Complete, Partial, Missing, or Unknown
- **MP3 URLs**: Direct links to streamable recordings
- **Duration**: Total show length in minutes
- **Taper Notes**: Detailed recording information and lineage

### Tour & Venue Data  
- **Tour Names**: "Fall Tour 1997", "Big Cypress", etc.
- **Venue Coordinates**: Latitude/longitude for mapping
- **Show Context**: Previous/next show information

### Tags & Metadata
- **Recording Tags**: SBD, AUD, Matrix, etc.
- **Special Events**: Halloween, New Year's, festivals
- **Popularity**: Like counts and community engagement

## 🔧 MCP Server Tools

### Core Tools
1. **`get_statistics`**: Database overview with audio metrics
2. **`search_shows`**: Find shows by date, venue, tour, location
3. **`get_show_details`**: Complete show information
4. **`get_setlist`**: Detailed setlist with transitions and notes

### Enhanced Tools  
5. **`search_shows_by_audio`**: Filter by audio availability
6. **`get_show_audio_info`**: Detailed audio metadata with MP3 URLs

## 📂 Data Structure

### Raw Shows (phish.net format)
```json
{
  "showdate": "2024-12-31",
  "venue": "Madison Square Garden",
  "city": "New York",
  "state": "NY", 
  "sets": [...],
  "api": "phish.net"
}
```

### Normalized Shows (standardized format)
```json
{
  "schema_version": "2.0",
  "show": {
    "id": "2024-12-31",
    "date": "2024-12-31", 
    "venue": {...},
    "tour": "New Years Run 2024"
  },
  "setlist": [...],
  "notes": {...},
  "provenance": {...}
}
```

### Enriched Shows (phish.in enhanced)
```json
{
  "schema_version": "2.0",
  "show": {
    "id": "2024-12-31",
    "date": "2024-12-31",
    "venue": {...},
    "tour": "New Years Run 2024",
    "audio_status": "complete",
    "duration_ms": 12480000,
    "tour_name": "New Years Run 2024",
    "likes_count": 156,
    "tags": [{"name": "SBD", "description": "Soundboard recording"}],
    "taper_notes": "Detailed recording information..."
  },
  "tracks": [
    {
      "title": "Wilson",
      "mp3_url": "https://phish.in/audio/...",
      "duration_ms": 480000,
      "audio_status": "complete"
    }
  ],
  "setlist": [...],
  "notes": {...}
}
```

## 🌐 Additional Features

### Streamlit Web Interface
```bash
pip install streamlit
streamlit run streamlit_app.py
```
- Interactive show browser and search
- Audio status visualization 
- Tour and venue exploration

### Docker Support
```bash
docker-compose up -d
```
- Containerized MCP server deployment
- Persistent data volumes
- Production-ready configuration

## 🧪 Testing & Validation

```bash
# Test the enhanced features
python test_enriched_features.py

# Test famous shows
python test_famous_shows.py

# Validate MCP server
python test_mcp.py
```

## 📈 Data Pipeline Performance

- **Download Speed**: ~2,202 shows in 30 minutes
- **Processing Rate**: ~1 show per second for formatting  
- **Enrichment Rate**: ~1 show per 1.5 seconds with API rate limiting
- **Total Processing Time**: ~4 hours for complete pipeline

## 🔗 Claude Desktop Integration

Configure in Claude Desktop settings:
```json
{
  "mcpServers": {
    "phish": {
      "command": "python",
      "args": ["c:/dev/phish_downloader/mcp_server_enhanced.py"],
      "cwd": "c:/dev/phish_downloader"
    }
  }
}
```

## 📚 Documentation Files

- **[COMPLETE.md](COMPLETE.md)**: Detailed implementation notes
- **[ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)**: phish.in integration guide
- **[PIPELINE.md](PIPELINE.md)**: Data processing workflow
- **[STREAMLIT.md](STREAMLIT.md)**: Web interface documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch  
3. Make your changes
4. Run tests: `python -m pytest tests/ -v`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🎪 The Music Never Stopped

*This project is dedicated to preserving and sharing the complete Phish concert experience through comprehensive data integration and AI-powered exploration.*
