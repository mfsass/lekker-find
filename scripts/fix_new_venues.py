
import pandas as pd
import re

CSV_FILE = 'data-262-2025-12-26.csv'

def fix_data():
    print(f"Reading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    
    # Define updates
    # Key = partial name or exact name
    # Value = (Suburb, Price_Tier, Numerical_Price, Vibe)
    # Use None if no change for that field
    updates = {
        'Tjing Tjing': ('City Centre', 'RR', 'R200-R400', 'Cool, Japanese, Rooftop'),
        'The Deli Social': ('Hout Bay', 'R', 'R100-R200', 'Bakery, Local, Deli'),
        'La Motte Artisanal Bakery': ('Franschhoek', 'R', 'R100-R200', 'Bakery, Garden, Historic'),
        'Heaven Coffee': ('City Centre', 'R', 'R50-R100', 'Coffee, Tranquil, Hidden'),
        'Yama Asian Eatery': ('Franschhoek', 'RR', 'R200-R400', 'Sushi, Asian, Tranquil'),
        'Vrymansfontein': ('Paarl', 'RR', 'R200-R400', 'Views, Wine, Stylish'),
        'Melfort': ('Stellenbosch', 'RR', 'R200-R400', 'Wine Farm, Food, Relaxed'),
        'Die Strandloper': ('Langebaan', 'RRR', 'R400-R800', 'Seafood, Beach, Casual'),
        'Le Pickle': ('De Waterkant', 'R', 'R100-R200', 'Burgers, Casual, Fun'),
        'The Vine Bistro': ('Stellenbosch', 'RR', 'R200-R400', 'Bistro, Views, French'),
        'The Wes Bistro': ('City Centre', 'RR', 'R200-R400', 'Bistro, City, Quirky'),
        'Meuse Farm': ('Hout Bay', 'RRR', 'R400-R800', 'Farm, Seasonal, Hidden'),
        'Gather': ('Stellenbosch', 'RRR', 'R400-R800', 'Farm, Seasonal, Intimate'), # Good to Gather
        'Dressing Room': ('De Waterkant', 'R', 'R100-R200', 'Cafe, Healthy, Stylish'),
        'Arkeste': ('Franschhoek', 'RR', 'R200-R400', 'Forest, Fine Dining, Nature'),
        'Homespun': ('Claremont', 'RRR', 'R400-R800', 'Theatrical, Intimate, Fine Dining'), # Homespun Claremont / Andros
        'Urchin': ('City Centre', 'RRR', 'R400-R800', 'Seafood, Luxury, Hotel'),
        'Willaston Bar': ('V&A Waterfront', 'RR', 'R200-R400', 'Bar, Views, Cocktails'),
        'De Grendel': ('Durbanville', 'RRR', 'R400-R800', 'Fine Dining, Views, Wine'),
        'Chorus': ('Somerset West', 'RRR', 'R400-R800', 'Fine Dining, Views, Wine'),
        'Hidden Valley': ('Stellenbosch', 'RR', 'R200-R400', 'Wine Farm, Views, Art'),
        'Florentin': ('City Centre', 'RR', 'R200-R400', 'Mediterranean, Social, City'),
        'Smitten': ('Franschhoek', None, None, None)
    }

    print("\nApplying updates...")
    
    for key, (sub, tier, num_price, vibe) in updates.items():
        # Find matching rows (case insensitive partial match)
        mask = df['Name'].str.lower().str.contains(key.lower(), regex=False)
        
        matches = df[mask]
        if matches.empty:
            print(f"⚠ No match found for '{key}'")
            continue
            
        for index, row in matches.iterrows():
            name = row['Name']
            print(f"  Updating '{name}':")
            
            if sub:
                print(f"    - Suburb: {sub}")
                df.at[index, 'Suburb'] = sub
            if tier:
                print(f"    - Price: {tier} ({num_price})")
                df.at[index, 'Price_Range'] = tier
                df.at[index, 'Numerical_Price'] = num_price
            if vibe:
                print(f"    - Vibe: {vibe}")
                df.at[index, 'Vibe'] = vibe

    # Save
    df.to_csv(CSV_FILE, index=False)
    print("\n✓ CSV updated successfully.")

if __name__ == "__main__":
    fix_data()
