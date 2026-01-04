import pandas as pd

CSV_FILE = 'data-262-2025-12-26.csv'

def clean_specific_duplicates():
    print(f"Reading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    initial_count = len(df)

    # 1. Handle Chapman's Peak Drive
    # We want "Chapman's Peak Drive" (or with curly quote).
    # Check if a "good" version exists
    has_good = not df[df['Name'].isin(["Chapman's Peak Drive", "Chapman’s Peak Drive"])].empty
    has_bad = not df[df['Name'] == "Chapmans Peak Drive"].empty
    
    if has_good and has_bad:
        print("Removing 'Chapmans Peak Drive' (keeping version with apostrophe)...")
        df = df[df['Name'] != "Chapmans Peak Drive"]
    
    # 2. Oranjezicht Market
    # Keep "Oranjezicht City Farm Market"
    has_short = not df[df['Name'] == "Oranjezicht Market"].empty
    has_long = not df[df['Name'] == "Oranjezicht City Farm Market"].empty
    
    if has_short and has_long:
         print("Removing 'Oranjezicht Market' (keeping full name)...")
         df = df[df['Name'] != "Oranjezicht Market"]

    # 3. Kirstenbosch Concerts
    # "Kirstenbosch Concerts" vs "Kirstenbosch Gardens Concert Stage"
    # User might prefer "Kirstenbosch Summer Sunset Concerts" or similar.
    # Let's keep the one with more reviews or better rating?
    # For now, I'll keep "Kirstenbosch Concerts" as it's punchier, unless "Concert Stage" describes the venue better.
    # Let's just warn for now or look at them.
    # df = df[df['Name'] != "Kirstenbosch Gardens Concert Stage"] # tentative
    
    # 4. Remove 'Chapman's Peak' if 'Chapman's Peak Drive' exists? 
    # 'Chapman's Peak' might refer to the mountain hike, 'Drive' is the road.
    # They are effectively different activities (Hiking vs Driving).
    # I will keep both if categories differ (Nature vs Activity/Scenic Drive).
    
    # Save if changes
    if len(df) < initial_count:
        print(f"Removed {initial_count - len(df)} duplicates.")
        df.to_csv(CSV_FILE, index=False)
    else:
        print("No specific duplicates found to remove.")

if __name__ == "__main__":
    clean_specific_duplicates()
