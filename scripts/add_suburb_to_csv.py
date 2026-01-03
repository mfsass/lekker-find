#!/usr/bin/env python3
"""
Add Suburb Column to CSV
=========================

Adds a 'Suburb' column to the CSV by extracting suburb data from
the JSON file (which gets it from Google Places during image fetch).

Usage:
    python scripts/add_suburb_to_csv.py
"""

import pandas as pd
import json

CSV_PATH = 'data-262-2025-12-26.csv'
JSON_PATH = 'public/lekker-find-data.json'


def add_suburb_column():
    """Add suburb column to CSV from JSON data."""
    print("=" * 70)
    print("ADD SUBURB COLUMN TO CSV")
    print("=" * 70)
    
    # Load JSON
    print(f"\n[1/3] Loading venue data from JSON...")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    venues = data.get('venues', [])
    print(f"  ✓ Loaded {len(venues)} venues from JSON")
    
    # Create suburb mapping
    suburb_map = {}
    suburbs_found = 0
    for venue in venues:
        name = venue.get('name')
        suburb = venue.get('suburb')
        if name and suburb:
            suburb_map[name] = suburb
            suburbs_found += 1
    
    print(f"  ✓ Found {suburbs_found} venues with suburb data")
    
    # Load CSV
    print(f"\n[2/3] Loading and updating CSV...")
    df = pd.read_csv(CSV_PATH)
    
    # Check if Suburb column exists
    if 'Suburb' in df.columns:
        print("  ⚠ Suburb column already exists, updating...")
    else:
        print("  ✓ Adding new Suburb column")
        df['Suburb'] = None
    
    # Update suburb data
    updated = 0
    for idx, row in df.iterrows():
        name = row['Name']
        if name in suburb_map:
            df.at[idx, 'Suburb'] = suburb_map[name]
            updated += 1
    
    print(f"  ✓ Updated {updated} rows with suburb data")
    
    # Save CSV
    print(f"\n[3/3] Saving updated CSV...")
    df.to_csv(CSV_PATH, index=False)
    print(f"  ✓ Saved to {CSV_PATH}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total venues:       {len(df)}")
    print(f"  With suburbs:       {updated}")
    print(f"  Without suburbs:    {len(df) - updated}")
    
    # Show sample
    print(f"\nSample venues with suburbs:")
    sample = df[df['Suburb'].notna()].head(5)
    for _, row in sample.iterrows():
        print(f"  - {row['Name']:35} → {row['Suburb']}")


if __name__ == "__main__":
    add_suburb_column()
