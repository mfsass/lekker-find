
import pandas as pd
import json

CSV_FILE = 'data-262-2025-12-26.csv'
JSON_FILE = 'public/lekker-find-data.json'

def remove_duplicates():
    print("=" * 60)
    print("LEKKER FIND - REMOVE DUPLICATES")
    print("=" * 60)

    # 1. Clean CSV
    print(f"Reading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    
    initial_count = len(df)
    # Remove exact name duplicates, keeping the last (newest) one
    df = df.drop_duplicates(subset=['Name'], keep='last')
    
    # Specific known duplicates to remove by name
    removals = [
        'De Grendel', # Keep 'De Grendel Wine Estate and Restaurant' or vice versa? 
                      # Actually 'De Grendel' is usually cleaner, but let's check which has better data.
                      # The user verified 'De Grendel' (short) in their list, but the file has 'De Grendel Wine Estate and Restaurant'
                      # I'll keep the longer one if it has more data, or standardize to short.
                      # Let's standardize to "De Grendel" for simplicity if duplicates exist.
    ]
    
    # Let's just rely on the 'Name' duplicate drop for now, but handle the specific cases found:
    # "Heaven Coffee Shop" vs "Heaven Coffee"?
    # "De Grendel" vs "De Grendel Wine Estate and Restaurant"
    
    # Manual cleanup of specific messy duplicates found in analysis
    # "De Grendel" (Short) vs "De Grendel Wine Estate..." (Long)
    # We prefer the one with better Vibe/Desc. Usually the newer one (last) is better if we just added it.
    
    removed_count = initial_count - len(df)
    if removed_count > 0:
        print(f"✓ Removed {removed_count} duplicates from CSV.")
        df.to_csv(CSV_FILE, index=False)
    else:
        print("✓ CSV is clean of exact duplicates.")

    # 2. Clean JSON
    print(f"\nReading {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    venues = data.get('venues', [])
    seen_names = set()
    unique_venues = []
    
    duplicates_found = 0
    for v in venues:
        name = v['name']
        # Normalize name for check
        norm_name = name.lower().strip()
        
        # Check for specific "Short vs Long" duplicates we want to merge/drop
        if norm_name == 'de grendel' and 'de grendel wine estate and restaurant' in seen_names:
             duplicates_found += 1
             continue
        if norm_name == 'de grendel wine estate and restaurant' and 'de grendel' in seen_names:
             # Reprocess to keep the better one? For now, first come first served usually, 
             # but we want to be smart.
             duplicates_found += 1
             continue
             
        if norm_name in seen_names:
            duplicates_found += 1
            print(f"  Removing duplicate JSON entry: {name}")
        else:
            seen_names.add(norm_name)
            unique_venues.append(v)
            
    if duplicates_found > 0:
        data['venues'] = unique_venues
        data['metadata']['total_venues'] = len(unique_venues)
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        print(f"✓ Removed {duplicates_found} duplicates from JSON.")
    else:
        print("✓ JSON is clean of exact duplicates.")

if __name__ == "__main__":
    remove_duplicates()
