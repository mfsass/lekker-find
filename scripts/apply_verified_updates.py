
import pandas as pd

CSV_FILE = 'data-262-2025-12-26.csv'

def apply_verified_updates():
    print(f"Reading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)

    # Define the verified updates
    # Format: Key Name (substring matching): {
    #   'Name': New Name (optional),
    #   'Vibe': New Vibe,
    #   'Price_Range': New Price Range,
    #   'Numerical_Price': New Numerical Price
    # }
    
    updates = {
        'The Deli Social': {
            'Vibe': 'Bakery, Local, Storytelling',
            'Price_Range': 'RR', # Interpreted from R / RR
            'Numerical_Price': 'R150 - R220'
        },
        'Le Pickle': {
            'Vibe': 'Fun, Vibrant, Burgers',
            'Price_Range': 'RR',
            'Numerical_Price': 'R200 - R250'
        },
        'Florentin': {
            'Vibe': 'Social, Med, City',
            'Price_Range': 'RR',
            'Numerical_Price': 'R250 - R350'
        },
        'Tjing Tjing Torii': { # Existing one
            'Vibe': 'Cool, Urban, Japanese',
            'Price_Range': 'RR',
            'Numerical_Price': 'R200 - R350'
        },
        'Tjing Tjing House': { # The one we added - repurposing to Momiji
            'Name': 'Tjing Tjing Momiji',
            'Vibe': 'Refined, Exclusive',
            'Price_Range': 'RRR',
            'Numerical_Price': 'R795'
        },
        'Yama Asian Eatery': {
            'Vibe': 'Tranquil, Garden, Sushi',
            'Price_Range': 'RR',
            'Numerical_Price': 'R250 - R400'
        },
        'The Vine Bistro': {
            'Vibe': 'French, Bistro, Views',
            'Price_Range': 'RR',
            'Numerical_Price': 'R390 - R500'
        },
        'Arkeste': {
            'Vibe': 'Forest, Nature, Casual Fine',
            'Price_Range': 'RRR', # Interpreted from RR / RRR
            'Numerical_Price': 'R350 - R550'
        },
        'Melfort': {
            'Vibe': 'Relaxed, Family, Farm',
            'Price_Range': 'RRR',
            'Numerical_Price': 'R695'
        },
        'Meuse Farm': {
            'Vibe': 'Hidden, Seasonal, Farm',
            'Price_Range': 'RRR',
            'Numerical_Price': 'R600'
        },
        'Good to Gather': {
            'Vibe': 'Intimate, Seasonal',
            'Price_Range': 'RRR',
            'Numerical_Price': 'R670'
        },
        'Die Strandloper': {
            'Vibe': 'Beach, Elemental, Seafood',
            'Price_Range': 'RRR',
            'Numerical_Price': 'R440 - R600'
        },
        'Precious Hidden Valley': {
            'Vibe': 'Views, Art, New African',
            'Price_Range': 'RRR',
            'Numerical_Price': 'R450 - R650'
        }
    }

    print("\nApplying verified updates...")

    for key, data in updates.items():
        # Find matching row(s)
        # Use simple string matching or exact match if preferred
        mask = df['Name'].str.contains(key, case=False, regex=False)
        
        # Special case for Tjing Tjing to differentiate
        if key == 'Tjing Tjing Torii':
             mask = df['Name'].str.contains('Torii', case=False, regex=False)
        elif key == 'Tjing Tjing House':
             mask = df['Name'] == 'Tjing Tjing House' # Exact match for the one we added

        matches = df[mask]
        
        if matches.empty:
            print(f"⚠ No match found for '{key}'")
            continue

        for index, row in matches.iterrows():
            print(f"  Updating '{row['Name']}':")
            
            if 'Name' in data:
                print(f"    - Name: {data['Name']}")
                df.at[index, 'Name'] = data['Name']
                
            if 'Vibe' in data:
                print(f"    - Vibe: {data['Vibe']}")
                df.at[index, 'Vibe'] = data['Vibe']
                
            if 'Price_Range' in data:
                print(f"    - Price_Range: {data['Price_Range']}")
                df.at[index, 'Price_Range'] = data['Price_Range']
                
            if 'Numerical_Price' in data:
                print(f"    - Numerical_Price: {data['Numerical_Price']}")
                df.at[index, 'Numerical_Price'] = data['Numerical_Price']

    # Save
    df.to_csv(CSV_FILE, index=False)
    print("\n✓ CSV updated successfully.")

if __name__ == "__main__":
    apply_verified_updates()
