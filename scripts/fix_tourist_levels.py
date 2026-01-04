
import pandas as pd

CSV_FILE = 'data-262-2025-12-26.csv'

def fix_tourist_levels():
    print(f"Reading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)

    # Define level updates based on user's curated "Gem" status
    # 1-3: Hidden / Secret / Local
    # 4-6: Known but not mass touristy
    # 7-10: Famous / Touristy
    
    level_updates = {
        # Truly Hidden (1-2)
        'The Wes Bistro': 1,
        'Meuse Farm': 1,
        'Good to Gather': 1, # Also 'Gather'
        'The Dressing Room': 2,
        'The Deli Social': 2,
        'Heaven Coffee': 2,
        
        # Hidden but Known / Cult (3-5)
        'Arkeste': 4, # Famous chef, hidden location
        'Homespun': 5, # Cult favorite
        'Urchin': 3, # Hidden in hotel
        'Melfort': 3, # Relaxed farm
        'Precious Hidden Valley': 4, 
        'Le Pickle': 4, # Local spot
        'La Motte Artisanal Bakery': 5, # Popular but niche
        'Yama Asian Eatery': 4,
        
        # Established / Famous (7-10)
        'Willaston Bar': 9, # Famous
        'De Grendel': 9, # Massive estate
        'Chorus': 8, # Major destination
        'Florentin': 7, # Lively, popular
        'Die Strandloper': 10, # Internationally famous
        'Tjing Tjing': 7, # Well known
        'Vrymansfontein': 7, # Stylish destination
        'The Vine Bistro': 6, 
    }

    print("\nApplying curated Tourist Level updates...")
    
    for key, level in level_updates.items():
        # Case insensitive partial match
        mask = df['Name'].str.lower().str.contains(key.lower(), regex=False)
        
        # Special handling for Tjing Tjing to differentiate if needed, 
        # but here both are popular so 7 is fine for base, maybe 8 for Momiji
        
        if not df[mask].empty:
            print(f"  Setting Level {level} for matches of '{key}'")
            df.loc[mask, 'Tourist_Level'] = level

    # Save
    df.to_csv(CSV_FILE, index=False)
    print("\n✓ CSV updated with curated Tourist Levels.")

if __name__ == "__main__":
    fix_tourist_levels()
