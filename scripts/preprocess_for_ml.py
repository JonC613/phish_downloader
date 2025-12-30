"""
Preprocessing script for Phish shows data for ML/SageMaker.
Adds feature engineering, normalization, and data preparation.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import re


def preprocess_jsonl(jsonl_file: Path, output_file: Path = None) -> pd.DataFrame:
    """
    Load JSONL file and preprocess data for ML.
    
    Args:
        jsonl_file: Path to JSONL file
        output_file: Optional path to save processed CSV for SageMaker
    
    Returns:
        Preprocessed DataFrame
    """
    # Load JSONL
    records = []
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    
    df = pd.DataFrame(records)
    print(f"[OK] Loaded {len(df)} records from {jsonl_file.name}")
    
    # ===================================================================
    # FEATURE ENGINEERING
    # ===================================================================
    
    # 1. Temporal Features
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.dayofweek  # 0=Monday, 6=Sunday
    df['month'] = df['date'].dt.month
    df['day_of_month'] = df['date'].dt.day
    df['quarter'] = df['date'].dt.quarter
    
    # Day name
    day_names = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 
                 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    df['day_name'] = df['day_of_week'].map(day_names)
    
    # Is weekend
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    # Season
    def get_season(month):
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:
            return 'Fall'
    
    df['season'] = df['month'].apply(get_season)
    
    # 2. Venue Features
    # Normalize venue name (lowercase, remove special chars)
    df['venue_normalized'] = df['venue_name'].str.lower().str.replace(r'[^a-z0-9]', '', regex=True)
    
    # Count shows per venue
    venue_counts = df['venue_normalized'].value_counts()
    df['venue_frequency'] = df['venue_normalized'].map(venue_counts)
    
    # Geographic features
    df['has_coordinates'] = ((df['latitude'].notna()) & (df['longitude'].notna())).astype(int)
    
    # 3. Setlist Complexity Features
    # Parse songs list
    df['songs_list'] = df['songs'].apply(lambda x: json.loads(x) if isinstance(x, str) else [])
    
    # Song diversity (unique songs)
    df['unique_songs'] = df['songs_list'].apply(lambda x: len(set(x)) if x else 0)
    df['song_diversity_ratio'] = df['unique_songs'] / (df['total_songs'] + 1)  # +1 to avoid division by zero
    
    # Jam ratio (songs with "Jam" in name)
    df['jam_count'] = df['songs_list'].apply(
        lambda x: sum(1 for song in x if 'jam' in song.lower()) if x else 0
    )
    df['jam_ratio'] = df['jam_count'] / (df['total_songs'] + 1)
    
    # Average set size
    df['avg_songs_per_set'] = df['total_songs'] / (df['num_sets'] + 1)
    
    # 4. Notes Features
    # Text length
    df['notes_length'] = df['notes'].fillna('').str.len()
    df['has_notes'] = (df['notes_length'] > 0).astype(int)
    
    # Extract tease mentions
    def count_teases(text):
        if pd.isna(text) or not text:
            return 0
        return len(re.findall(r'tease[ds]?', text, re.IGNORECASE))
    
    df['tease_count'] = df['notes'].apply(count_teases)
    
    # Extract first-time mentions
    def count_first_times(text):
        if pd.isna(text) or not text:
            return 0
        return len(re.findall(r'first time|debut|premiere', text, re.IGNORECASE))
    
    df['first_time_count'] = df['notes'].apply(count_first_times)
    
    # 5. Tour Features
    df['is_part_of_tour'] = (~df['tour'].isin(['Not Part of a Tour', '', None])).astype(int)
    df['tour_normalized'] = df['tour'].fillna('unknown').str.lower()
    
    # 6. Location Features (encode common locations)
    major_cities = {
        'New York': ['new york', 'forest hills'],
        'San Francisco': ['san francisco', 'oakland'],
        'Los Angeles': ['los angeles', 'hollywood', 'pasadena'],
        'Boulder': ['boulder'],
        'Chicago': ['chicago'],
        'Boston': ['boston'],
        'Philadelphia': ['philadelphia'],
        'Las Vegas': ['las vegas'],
        'Miami': ['miami'],
        'Austin': ['austin']
    }
    
    def categorize_city(city):
        if pd.isna(city):
            return 'Other'
        city_lower = str(city).lower()
        for major_city, aliases in major_cities.items():
            if any(alias in city_lower for alias in aliases):
                return major_city
        return 'Other'
    
    df['major_city'] = df['city'].apply(categorize_city)
    
    # ===================================================================
    # NORMALIZATION & SCALING
    # ===================================================================
    
    # Numerical features to normalize (0-1 scale)
    numerical_features = [
        'total_songs', 'num_sets', 'avg_songs_per_set',
        'unique_songs', 'song_diversity_ratio', 'jam_ratio',
        'notes_length', 'tease_count', 'first_time_count',
        'venue_frequency'
    ]
    
    scaler = MinMaxScaler()
    df_numeric = df[numerical_features].fillna(0)
    df_scaled = scaler.fit_transform(df_numeric)
    
    for i, col in enumerate(numerical_features):
        df[f'{col}_normalized'] = df_scaled[:, i]
    
    print("[OK] Added temporal features")
    print("[OK] Added venue features")
    print("[OK] Added setlist complexity features")
    print("[OK] Added notes analysis features")
    print("[OK] Added normalized features")
    
    # ===================================================================
    # SELECT FEATURES FOR SAGEMAKER
    # ===================================================================
    
    # Core features for export
    feature_cols = [
        # IDs and dates
        'date', 'year', 'show_id',
        
        # Temporal features
        'day_of_week', 'day_name', 'month', 'quarter', 'season', 'is_weekend',
        
        # Venue features
        'venue_name', 'city', 'state', 'country', 'major_city',
        'venue_frequency', 'has_coordinates',
        
        # Setlist features
        'total_songs', 'num_sets', 'avg_songs_per_set',
        'unique_songs', 'song_diversity_ratio', 'jam_ratio', 'jam_count',
        
        # Notes features
        'has_notes', 'notes_length', 'tease_count', 'first_time_count',
        
        # Tour features
        'is_part_of_tour',
        
        # Normalized versions (for ML models)
        'total_songs_normalized', 'num_sets_normalized',
        'avg_songs_per_set_normalized', 'unique_songs_normalized',
        'song_diversity_ratio_normalized', 'jam_ratio_normalized',
        'notes_length_normalized', 'tease_count_normalized',
        'first_time_count_normalized', 'venue_frequency_normalized'
    ]
    
    df_export = df[feature_cols].copy()
    
    # Handle missing values
    df_export = df_export.fillna(0)
    
    # Save to CSV for SageMaker (better for tabular data)
    if output_file is None:
        output_file = Path('phish_shows_preprocessed.csv')
    
    df_export.to_csv(output_file, index=False)
    print(f"[OK] Saved preprocessed data to {output_file}")
    
    # Also save as JSONL for reference
    jsonl_output = output_file.with_suffix('.jsonl')
    with open(jsonl_output, 'w', encoding='utf-8') as f:
        for _, row in df_export.iterrows():
            f.write(json.dumps(row.to_dict(), default=str) + '\n')
    print(f"[OK] Saved as JSONL to {jsonl_output}")
    
    # Print summary statistics
    print("\n" + "="*60)
    print("DATA SUMMARY")
    print("="*60)
    print(f"Total records: {len(df_export)}")
    print(f"Features: {len(feature_cols)}")
    print(f"\nDate range: {df['date'].min()} to {df['date'].max()}")
    print(f"Unique venues: {df['venue_normalized'].nunique()}")
    print(f"Unique cities: {df['city'].nunique()}")
    print(f"Unique countries: {df['country'].nunique()}")
    
    print(f"\nSetlist stats:")
    print(f"  Average songs per show: {df['total_songs'].mean():.1f}")
    print(f"  Average sets per show: {df['num_sets'].mean():.1f}")
    print(f"  Unique songs across all shows: {df['unique_songs'].sum()}")
    
    print(f"\nNotes stats:")
    print(f"  Shows with notes: {df['has_notes'].sum()} ({100*df['has_notes'].mean():.1f}%)")
    print(f"  Average tease mentions: {df['tease_count'].mean():.1f}")
    print(f"  Shows with first-time songs: {(df['first_time_count'] > 0).sum()}")
    
    print(f"\nOutput files:")
    print(f"  CSV: {output_file}")
    print(f"  JSONL: {jsonl_output}")
    
    return df_export


def create_feature_importance_guide():
    """Create a guide explaining all features for ML models."""
    guide = """
# Feature Guide for Phish Shows ML Dataset

## Temporal Features
- **day_of_week**: 0=Monday, 6=Sunday (useful for pattern analysis)
- **is_weekend**: Binary indicator for weekend shows
- **season**: Winter/Spring/Summer/Fall (captures seasonal touring patterns)
- **month**, **quarter**: For time-based analysis

## Venue Features
- **venue_frequency**: How often this venue has hosted Phish (popularity metric)
- **major_city**: Categorized major cities (helps with location-based features)
- **has_coordinates**: Whether venue has geographic coordinates

## Setlist Complexity Features
- **total_songs**: Length of show
- **num_sets**: How many sets in the show
- **avg_songs_per_set**: Average set length
- **unique_songs**: Diversity metric (how many unique songs played)
- **song_diversity_ratio**: Normalized diversity (unique/total)
- **jam_ratio**: Proportion of jam-related songs
- **jam_count**: Number of jam songs

## Content Features
- **has_notes**: Whether show has setlist notes
- **tease_count**: How many teases mentioned in notes
- **first_time_count**: How many first-time plays/debuts

## Tour Features
- **is_part_of_tour**: Binary indicator if show is part of named tour

## Normalized Features (0-1 scale)
All numerical features have normalized versions (suffix: _normalized)
These are scaled to 0-1 range for ML algorithms

## Use Cases
- **Regression**: Predict total_songs, jam_ratio, setlist complexity
- **Classification**: Predict major_city, season, is_weekend
- **Clustering**: Group shows by similarity
- **Time Series**: Analyze patterns over date
"""
    
    with open('FEATURE_GUIDE.md', 'w') as f:
        f.write(guide)
    
    print("\n[OK] Created FEATURE_GUIDE.md")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Preprocess Phish shows JSONL for ML/SageMaker"
    )
    
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("phish_shows_2025.jsonl"),
        help="Input JSONL file"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV file (default: phish_shows_preprocessed.csv)"
    )
    
    args = parser.parse_args()
    
    try:
        df = preprocess_jsonl(args.input, args.output)
        create_feature_importance_guide()
        print("\n✓ Preprocessing complete!")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
