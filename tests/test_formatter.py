"""Tests for normalize_show and format_file functions."""

import json
import tempfile
from pathlib import Path

import pytest

from phish_json_formatter import format_file, normalize_show, validate_normalized


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_raw_json() -> dict:
    """Minimal raw show JSON from API."""
    return {
        "id": "2023-12-30-madison-square-garden",
        "date": "2023-12-30",
        "showDate": None,  # Should prefer "date"
        "venueName": "Madison Square Garden",
        "venue": None,  # venueName takes precedence
        "city": "New York",
        "state": "NY",
        "country": "USA",
        "lat": 40.7505,
        "lon": -73.9934,
        "tour": "Winter Tour 2023",
        "api": "phish.net",
        "downloaded_at": "2023-12-31T00:00:00Z",
        "setlist": [
            {
                "name": "Set 1",
                "songs": [
                    {
                        "title": "Simple",
                        "transition": "->",
                        "notes": ["Unusual lyrics variation"]
                    },
                    {
                        "title": "Punch You in the Eye",
                        "transition": None,
                        "notes": []
                    }
                ]
            },
            {
                "name": "Set 2",
                "songs": [
                    {
                        "title": "Ghost",
                        "transition": "->",
                        "notes": []
                    }
                ]
            },
            {
                "name": "Encore",
                "songs": [
                    {
                        "title": "Tweezer Reprise",
                        "transition": None,
                        "notes": []
                    }
                ]
            }
        ],
        "notes": ["Great show"],
        "fan_comments": [
            {
                "source": "phish.net",
                "author": "fan123",
                "date": "2023-12-30",
                "text": "Amazing performance!",
                "url": "https://phish.net/comments/123"
            }
        ],
        "facts": [
            {
                "label": "First show at MSG of the tour",
                "detail": None,
                "source_url": None
            }
        ]
    }


@pytest.fixture
def expected_normalized_shape() -> dict:
    """Expected structure of normalized output (rough shape check)."""
    return {
        "schema_version": "2.0",
        "show": {
            "id": str,
            "date": str,
            "tour": (str, type(None)),
            "venue": {
                "name": str,
                "city": str,
                "state": (str, type(None)),
                "country": str,
                "lat": (float, type(None)),
                "lon": (float, type(None))
            }
        },
        "setlist": list,
        "notes": dict,
        "facts": list,
        "sources": list,
        "provenance": dict
    }


# ============================================================================
# Tests
# ============================================================================

class TestNormalizeShow:
    """Tests for normalize_show function."""

    def test_basic_normalization(self, sample_raw_json):
        """Test basic normalization of raw JSON."""
        result = normalize_show(sample_raw_json, "test_show.json")
        
        # Check schema version
        assert result["schema_version"] == "2.0"
        
        # Check show fields
        assert result["show"]["date"] == "2023-12-30"
        assert result["show"]["venue"]["name"] == "Madison Square Garden"
        assert result["show"]["venue"]["city"] == "New York"
        assert result["show"]["venue"]["state"] == "NY"
        assert result["show"]["tour"] == "Winter Tour 2023"
        assert result["show"]["venue"]["lat"] == 40.7505
        assert result["show"]["venue"]["lon"] == -73.9934
    
    def test_setlist_preservation(self, sample_raw_json):
        """Test that setlist structure is preserved."""
        result = normalize_show(sample_raw_json, "test_show.json")
        
        setlist = result["setlist"]
        assert len(setlist) == 3
        assert setlist[0]["set"] == "Set 1"
        assert len(setlist[0]["songs"]) == 2
        assert setlist[0]["songs"][0]["title"] == "Simple"
        assert setlist[0]["songs"][0]["transition"] == "->"
        
        assert setlist[2]["set"] == "Encore"
        assert setlist[2]["songs"][0]["title"] == "Tweezer Reprise"
    
    def test_notes_and_comments(self, sample_raw_json):
        """Test extraction of notes and fan comments."""
        result = normalize_show(sample_raw_json, "test_show.json")
        
        notes = result["notes"]
        assert "Great show" in notes["curated"]
        assert len(notes["fan_comments"]) == 1
        assert notes["fan_comments"][0]["author"] == "fan123"
        assert notes["fan_comments"][0]["text"] == "Amazing performance!"
    
    def test_provenance_tracking(self, sample_raw_json):
        """Test that provenance is correctly recorded."""
        result = normalize_show(sample_raw_json, "raw_2023-12-30.json")
        
        prov = result["provenance"]
        assert prov["raw_input"]["filename"] == "raw_2023-12-30.json"
        assert prov["raw_input"]["api"] == "phish.net"
        assert prov["generator"] == "phish-json-formatter"
        assert "generated_at" in prov
    
    def test_missing_date_raises_error(self, sample_raw_json):
        """Test that missing date raises ValueError."""
        del sample_raw_json["date"]
        
        with pytest.raises(ValueError, match="Missing required field: date"):
            normalize_show(sample_raw_json, "test_show.json")
    
    def test_missing_venue_raises_error(self, sample_raw_json):
        """Test that missing venue raises ValueError."""
        del sample_raw_json["venueName"]
        
        with pytest.raises(ValueError, match="Missing required field: venue name"):
            normalize_show(sample_raw_json, "test_show.json")
    
    def test_missing_city_raises_error(self, sample_raw_json):
        """Test that missing city raises ValueError."""
        del sample_raw_json["city"]
        
        with pytest.raises(ValueError, match="Missing required field: city"):
            normalize_show(sample_raw_json, "test_show.json")
    
    def test_stable_id_generation(self, sample_raw_json):
        """Test that ID uses API id when available."""
        result = normalize_show(sample_raw_json, "test_show.json")
        # Should use the "id" field from raw data
        assert result["show"]["id"] == "2023-12-30-madison-square-garden"
    
    def test_stable_id_fallback(self):
        """Test that stable ID is generated when no API id."""
        raw = {
            "date": "2023-12-30",
            "venueName": "The Fillmore",
            "city": "San Francisco",
            "state": "CA"
        }
        result = normalize_show(raw, "test_show.json")
        # Should have generated an ID from date, venue, city
        assert "2023-12-30" in result["show"]["id"]
        assert "fillmore" in result["show"]["id"].lower()


class TestValidation:
    """Tests for validate_normalized function."""

    def test_valid_normalized(self, sample_raw_json):
        """Test that valid normalized doc passes validation."""
        normalized = normalize_show(sample_raw_json, "test_show.json")
        # Should not raise
        validate_normalized(normalized)
    
    def test_missing_schema_version(self, sample_raw_json):
        """Test validation fails without schema_version."""
        normalized = normalize_show(sample_raw_json, "test_show.json")
        del normalized["schema_version"]
        
        with pytest.raises(ValueError, match="Missing required top-level key"):
            validate_normalized(normalized)
    
    def test_invalid_date_format(self, sample_raw_json):
        """Test validation fails with invalid date format."""
        normalized = normalize_show(sample_raw_json, "test_show.json")
        normalized["show"]["date"] = "12/30/2023"  # Wrong format
        
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_normalized(normalized)


class TestFormatFile:
    """Tests for format_file function."""

    def test_format_file_writes_normalized_json(self, sample_raw_json):
        """Test that format_file writes valid normalized JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "raw.json"
            output_file = Path(tmpdir) / "normalized.json"
            
            # Write raw JSON
            with open(input_file, "w") as f:
                json.dump(sample_raw_json, f)
            
            # Format
            format_file(input_file, output_file)
            
            # Check output exists and is valid JSON
            assert output_file.exists()
            with open(output_file) as f:
                result = json.load(f)
            
            # Validate structure
            validate_normalized(result)
            assert result["schema_version"] == "2.0"
    
    def test_format_file_creates_parent_dirs(self, sample_raw_json):
        """Test that format_file creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "raw.json"
            output_file = Path(tmpdir) / "nested" / "deep" / "normalized.json"
            
            with open(input_file, "w") as f:
                json.dump(sample_raw_json, f)
            
            format_file(input_file, output_file)
            
            assert output_file.exists()
            assert output_file.parent.exists()
    
    def test_format_file_trailing_newline(self, sample_raw_json):
        """Test that output JSON has trailing newline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "raw.json"
            output_file = Path(tmpdir) / "normalized.json"
            
            with open(input_file, "w") as f:
                json.dump(sample_raw_json, f)
            
            format_file(input_file, output_file)
            
            # Read raw bytes to check for trailing newline
            with open(output_file, "rb") as f:
                content = f.read()
            
            assert content.endswith(b"\n")
    
    def test_format_file_missing_input(self):
        """Test that missing input file raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "nonexistent.json"
            output_file = Path(tmpdir) / "output.json"
            
            with pytest.raises(FileNotFoundError):
                format_file(input_file, output_file)

