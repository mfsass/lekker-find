
import json
import pandas as pd
import sys
from pathlib import Path

# Config
CSV_FILE = 'data-262-2025-12-26.csv'
JSON_FILE = 'public/lekker-find-data.json'

def clean_data():
    print("=" * 60)
    print("LEKKER FIND - DATA CLEANUP")
    print("=" * 60)

    # 1. Update CSV with Missing Suburbs and Price/Vibe Fixes
    print(f"Reading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    
    # Define fixes for known NAN/Missing items
    fixes = {
        "Woolley’s Tidal Pool": {'Suburb': 'Kalk Bay', 'Price_Range': 'Free', 'Vibe': 'Nature, Ocean, Hidden'},
        "Judas’ Peak": {'Suburb': 'Hout Bay', 'Price_Range': 'Free', 'Vibe': 'Hiking, Views, Adventure'},
        "Elephant's Eye Cave": {'Suburb': 'Silvermine', 'Price_Range': 'R', 'Vibe': 'Hiking, Cave, Family'},
        "Myburgh's Waterfall Ravine": {'Suburb': 'Hout Bay', 'Price_Range': 'Free', 'Vibe': 'Hiking, Waterfall, Nature'},
        "Helderberg West Peak": {'Suburb': 'Somerset West', 'Price_Range': 'R', 'Vibe': 'Hiking, Views, Challenge'},
        "Chapman's Peak Drive Lookout Point": {'Suburb': 'Hout Bay', 'Price_Range': 'R', 'Vibe': 'Scenic, Sunset, Iconic'},
        "Newlands Forest Hiking Trail": {'Suburb': 'Newlands', 'Price_Range': 'Free', 'Vibe': 'Forest, Nature, Dog-friendly'},
        "Boomslang Canopy Trail (Kirstenbosch Tree Canopy Walkway)": {'Suburb': 'Newlands', 'Price_Range': 'R', 'Vibe': 'Garden, Views, Walk'},
        "Cecilia Ravine Waterfall": {'Suburb': 'Constantia', 'Price_Range': 'Free', 'Vibe': 'Hiking, Waterfall, Forest'},
        "Old Cape Point Lighthouse": {'Suburb': 'Cape Point', 'Price_Range': 'R', 'Vibe': 'Historic, Views, Windy'},
        "Tjing Tjing House": {'Suburb': 'City Centre', 'Price_Range': 'RRR', 'Vibe': 'Japanese, Rooftop, Cool'}
    }

    print("\nApplying specific fixes for NAN/Missing data...")
    for name, invalid_fields in fixes.items():
        mask = df['Name'] == name
        if not mask.any():
            print(f"⚠ Name not found in CSV: {name}")
            continue
            
        for field, value in invalid_fields.items():
            print(f"  Fixing {name} -> {field}: {value}")
            df.loc[mask, field] = value

    # 2. General NaN Cleanup in CSV
    # Fill empty Suburbs with 'Cape Town' default or better logic
    # Fill empty Prices with 'R' default
    
    # Suburbs
    missing_suburbs = df['Suburb'].isna() | (df['Suburb'] == '') | (df['Suburb'] == 'nan')
    if missing_suburbs.any():
        print(f"\nFound {missing_suburbs.sum()} remaining blank suburbs. Setting to 'Cape Town'.")
        df.loc[missing_suburbs, 'Suburb'] = 'Cape Town'
    
    # Prices
    missing_prices = df['Price_Range'].isna() | (df['Price_Range'] == '')
    if missing_prices.any():
        print(f"Found {missing_prices.sum()} remaining blank prices. Setting to 'R'.")
        df.loc[missing_prices, 'Price_Range'] = 'R'
        df.loc[missing_prices, 'Numerical_Price'] = 'R100-R200'

    # Save cleaned CSV
    df.to_csv(CSV_FILE, index=False)
    print("✓ CSV Saved.")

    # 3. Sync to JSON (Reuse logic or call script)
    # We will do a direct JSON patch here to ensure "nan" strings are gone
    
    print(f"\nPatching {JSON_FILE} to remove 'nan'...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    venues = data.get('venues', [])
    fixed_count = 0
    
    for venue in venues:
        # Fix Suburb "nan" string or null
        sub = venue.get('suburb')
        if not sub or str(sub).lower() == 'nan':
            # Look up in our fixes or DF
            name = venue.get('name')
            if name in fixes:
                 venue['suburb'] = fixes[name]['Suburb']
                 fixed_count += 1
            else:
                 # Last resort fallback
                 row = df[df['Name'] == name]
                 if not row.empty:
                     val = row.iloc[0]['Suburb']
                     if pd.notna(val):
                         venue['suburb'] = str(val)
                         fixed_count += 1
        
        # Ensure ratings are not 0 if possible (not requested but good practice)
        
    if fixed_count > 0:
        data['metadata']['updated_at'] = pd.Timestamp.now().isoformat()
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
             json.dump(data, f)
        print(f"✓ Patched {fixed_count} venues in JSON.")
    else:
        print("✓ JSON appears clean (or changes were already synced).")
        
if __name__ == "__main__":
    clean_data()
