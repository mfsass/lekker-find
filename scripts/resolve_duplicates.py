
import json
import pandas as pd

JSON_FILE = 'public/lekker-find-data.json'
CSV_FILE = 'data-262-2025-12-26.csv'

def resolve_duplicates():
    print("=" * 60)
    print("LEKKER FIND - RESOLVE DUPLICATES")
    print("=" * 60)
    
    # 1. Define Resolution Rules
    # Key: Name to REMOVE
    # Value: Name to KEEP (or None if just remove)
    
    resolutions = {
        'Newlands Forest Hiking Trail': 'Newlands Forest',
        'Heaven Coffee Shop': 'Heaven Coffee',
        'India Venster Hiking Trail': 'India Venster Trail',
        'Shimansky Diamonds': 'Shimansky Diamond Exp.',
        'Saunders Rocks': 'Saunders Rock',
        'Ground Art Caffe': 'Ground Art Caffé',
        'Chinchilla': 'Chinchilla Rooftop',
        'House of Machines': 'The House of Machines',
        'Silvermine Reservoir': 'Silvermine', # Consolidate
        'The Rock': None, # "Fish on the Rocks" is the place. "The Rock" is likely noise or wrong name.
        'Gigi Rooftop Bar': 'Gigi Rooftop',
        'Tandem Paragliding': None, # Generic name, remove in favor of specific "Fly Cape Town" or "Parapax" 
                                   # wait, these are specific providers. "Tandem Paragliding" is vague. Remove.
        'Galileo Open Air Cinema': 'The Galileo Open Air Cinema, Kirstenbosch (Weekdays)', # Or simpler
        'Truth Coffee': 'Truth Coffee Roasting',
        'Chapman’s Peak': 'Chapman’s Peak Drive', # Drive is the venue usually
        'PIER Restaurant': 'Pier',             # Or vice versa. Pier is simple.
        'Fyn Restaurant': 'FYN',               # Brand is FYN
        'Robben Island Museum': 'Robben Island', # Simpler
        'La Colombe Restaurant': 'La Colombe',
        'De Grendel Wine Estate and Restaurant': 'De Grendel',
        'De Grendel Wine Estate': 'De Grendel', # if exists
    }
    
    # Items to explicitly IGNORE (False Positives)
    # Both names are valid different venues
    ignore_pairs = [
        'Spier Segway Tour', 'Pier',
        'Bo-Kaap Kombuis', 'Bo-Kaap',
        'Bo-Kaap Cooking Class', 'Bo-Kaap',
        'Bo-Kaap Museum', 'Bo-Kaap',
        'Cape Point Vineyards', 'Cape Point',
        'Old Cape Point Lighthouse', 'Cape Point',
        'Constantia Nek', 'Constantia Glen',
        'Constantia Nek', 'Constantia Zipline',
        'Muizenberg Surfing', 'Muizenberg'
    ]

    print(f"Loading {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    venues = data.get('venues', [])
    initial_count = len(venues)
    
    kept_venues = []
    removed_names = []
    
    # Create a set of names we plan to keep to verify targets exist
    # (Simplified logic: First pass filter)
    
    for v in venues:
        name = v['name']
        
        # Check if this name is slated for removal
        if name in resolutions:
            target = resolutions[name]
            if target:
                print(f"  Removing '{name}' -> Merging into '{target}'")
            else:
                print(f"  Removing '{name}' (Generic/Duplicate)")
            removed_names.append(name)
        else:
            kept_venues.append(v)
            
    # Also clean CSV
    print(f"\nCleaning {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    df_initial = len(df)
    
    # Remove rows where Name is in removed_names
    df = df[~df['Name'].isin(removed_names)]
    
    print(f"Removed {df_initial - len(df)} rows from CSV.")
    df.to_csv(CSV_FILE, index=False)
    
    # Save JSON
    if len(removed_names) > 0:
        data['venues'] = kept_venues
        data['metadata']['total_venues'] = len(kept_venues)
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        print(f"\n✓ Removed {len(removed_names)} venues from JSON.")
    else:
        print("\n✓ No duplicates resolved (names didn't match validation list).")

if __name__ == "__main__":
    resolve_duplicates()
