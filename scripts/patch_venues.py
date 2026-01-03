#!/usr/bin/env python3
"""Quick patch to add rating/suburb from CSV to JSON for existing venues."""
import json
import pandas as pd
import math

# Load data
with open('public/lekker-find-data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

df = pd.read_csv('data-262-2025-12-26.csv')

# Create lookup from CSV
csv_lookup = {}
for _, row in df.iterrows():
    rating = row.get('Rating')
    suburb = row.get('Suburb')
    csv_lookup[row['Name']] = {
        'rating': float(rating) if pd.notna(rating) else None,
        'suburb': str(suburb) if pd.notna(suburb) else None
    }

# Update JSON venues
updated = 0
for venue in data['venues']:
    name = venue['name']
    if name in csv_lookup:
        csv_data = csv_lookup[name]
        
        # Only update if missing
        needs_update = False
        
        if venue.get('rating') is None and csv_data['rating'] is not None:
            venue['rating'] = csv_data['rating']
            needs_update = True
            
        if venue.get('suburb') is None and csv_data['suburb'] is not None:
            venue['suburb'] = csv_data['suburb']
            needs_update = True
            
        if needs_update:
            updated += 1
            print(f"  Updated: {name} (rating={csv_data['rating']}, suburb={csv_data['suburb']})")

# Save
with open('public/lekker-find-data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f)

print(f"\n✓ Patched {updated} venues with rating/suburb data")
