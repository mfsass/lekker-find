
import json
import pandas as pd
import sys
import re
from pathlib import Path

# Config
CSV_FILE = 'data-262-2025-12-26.csv'
JSON_FILE = 'public/lekker-find-data.json'

def clean_data():
    print("=" * 60)
    print("LEKKER FIND - DATA CLEANUP")
    print("=" * 60)

    print(f"Reading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    
    # ---------------------------------------------------------
    # 1. TOURIST LEVEL FIXES (Curated)
    # ---------------------------------------------------------
    level_updates = {
        'The Wes Bistro': 1, 'Meuse Farm': 1, 'Good to Gather': 1, 
        'The Dressing Room': 2, 'The Deli Social': 2, 'Heaven Coffee': 2,
        'Arkeste': 4, 'Homespun': 5, 'Urchin': 3, 'Melfort': 3, 
        'Precious Hidden Valley': 4, 'Le Pickle': 4, 'La Motte Artisanal Bakery': 5, 
        'Yama Asian Eatery': 4, 'Willaston Bar': 9, 'De Grendel': 9, 
        'Chorus': 8, 'Florentin': 7, 'Die Strandloper': 10, 'Tjing Tjing': 7,
        'Vrymansfontein': 7, 'The Vine Bistro': 6, 
    }
    
    for key, level in level_updates.items():
        mask = df['Name'].str.lower().str.contains(key.lower(), regex=False)
        if not df[mask].empty:
             # Only update if different
             # df.loc[mask, 'Tourist_Level'] = level 
             # (Optimized to avoid SettingWithCopy warnings if complex, but here simplistic)
             df.loc[mask, 'Tourist_Level'] = level

    # ---------------------------------------------------------
    # 2. PRICE & DETAIL UPDATES (Curated)
    # ---------------------------------------------------------
    # Key -> (New Name, Num Price, Price Band, Note)
    price_updates = {
        "Sushi Box Somerset West": ("Sushi Box Somerset West", "R250 – R350", "RR", "Combo box + drink."),
        "Mugg & Bean Strand": ("Mugg & Bean Strand", "R150 – R200", "R", "Breakfast/Lunch + coffee."),
        "Oldenburg Vineyards": ("Oldenburg Vineyards", "R300 – R650", "RRR", "Standard Tasting R300; Library Tasting R650."),
        "Weirdough Bakery": ("Weirdough Bakery & Deli", "R60 – R90", "R", "Pastry + Coffee."),
        "Legacy Coffee Shop": ("Legacy Coffee Shop", "R120 – R160", "R", "Burger/Bagel + Coffee."),
        "Sanook Somerset": ("Sanook Somerset", "R200 – R250", "RR", "Pizza/Burger + Drink."),
        "Idiom Restaurant": ("Idiom Restaurant & Wine", "R400 – R800", "RRR", "Tasting R175; Mains R200+; Pairings high."),
        "Chapman": ("Chapman’s Peak Drive", "R66", "R", "Toll fee per car (one way)."),
        "Stadsaal Caves": ("Stadsaal Caves", "R50 – R80", "R", "CapeNature permit required."),
        "Helderberg Nature Reserve": ("Helderberg Nature Reserve", "R30", "R", "Adult entry. +R20 per vehicle."),
        "Koeël Bay": ("Kogel Bay (Koeël Bay)", "R20 – R65", "R", "Day visitor fee (seasonal)."),
        "Silvermine Waterfall": ("Silvermine Waterfall", "Free / R44", "R", "Free via Gate 2; R44 via Gate 1."),
        "Old Nectar Gardens": ("Old Nectar Gardens", "R50", "R", "Private garden entry."),
        "Jonkershoek Nature Reserve": ("Jonkershoek Nature Reserve", "R50", "R", "CapeNature conservation fee."),
        "Dylan Lewis": ("Dylan Lewis Studio", "R260", "RR", "By appointment."),
        "FrameZ": ("FrameZ", "Free", "Free", "Public Yellow Frames."),
        "Rupert Museum": ("Rupert Museum", "Free", "Free", "Complimentary entry."),
        "Motorcycle Museum Helderberg": ("Motorcycle Museum Helderberg", "R100", "R", "Adult entry."),
        "Franschhoek Motor Museum": ("Franschhoek Motor Museum", "R90", "R", "Adult entry."),
        "The Drama Factory": ("The Drama Factory", "R150 – R180", "R", "Show tickets."),
        "Hi5 Tandem Paragliding": ("Hi5 Tandem Paragliding", "R2,200", "RRR", "Flight R1850 + Photos R350."),
        "PadelDeals": ("PadelDeals", "R100 – R150", "R", "Est. cost."),
        "CityROCK": ("CityROCK Cape Town", "R320", "RR", "Day pass + gear."),
        "Kayak Cape Town": ("Kayak Cape Town (Simon’s)", "R500 – R690", "RRR", "Penguin paddle."),
        "Bloc 11": ("Bloc 11 – Diep River", "R140 – R200", "R", "Bouldering day pass."),
        "Cape Town Tandem Paragliding": ("CT Tandem Paragliding", "R2,200", "RRR", "Flight R1800 + Photos R400."),
        "NoodleBox": ("NoodleBox Stellenbosch", "R170 – R220", "RR", "Main dish + drink."),
        "De Vier Restaurant": ("De Vier Restaurant", "R350 – R550", "RRR", "3-course meal."),
        "MERTIA": ("MERTIA", "R1,495 – R1,799", "RRR", "Set Menu. Wine pairing extra."),
        "The Table at De Meye": ("The Table at De Meye", "R595", "RRR", "3-course set menu (food only)."),
        "Stellies iCafe": ("Stellies iCafe", "R40 – R60", "R", "Coffee + muffin."),
        "Platō Coffee": ("Platō Coffee Stellenbosch", "R35 – R60", "R", "Coffee/Freezo."),
        "The Daisy Jones Bar": ("The Daisy Jones Bar", "R150 – R350", "RR", "Ticket + Drink/Food."),
        "Newlands Forest": ("Newlands Forest Hiking Trail", "R44 – R200", "R", "SA: R44. Intl: R200 (SANParks)."),
        "Acrobranch Stellenbosch": ("Acrobranch Stellenbosch", "R190 – R350", "RR", "Course dependent."),
        "Echo Valley": ("Echo Valley", "Free", "Free", "Open access trail (Kalk Bay)."),
        "Vegan Goods Market": ("Vegan Goods Market", "Free", "Free", "Entry is free."),
        "Winelands Light Railway": ("Winelands Light Railway", "R90 – R145", "R", "1 ride vs Unlimited."),
        "Huckleberry Fish Farm": ("Huckleberry Fish Farm", "R120", "R", "Entry & Fishing."),
        "Cape Town Surf School": ("Cape Town Surf School", "R450 – R600", "RRR", "Private/Group lesson."),
        "Kayak Adventures": ("Kayak Adventures (Hout Bay)", "R400 – R500", "RRR", "Seal sanctuary trip."),
        "Atlantic Surf Collective": ("Atlantic Surf Collective", "R400", "RRR", "Surf lesson."),
        "Hazendal": ("Hazendal – Driving Range", "R160 – R380", "RR", "Hourly bay rental."),
        "India Venster": ("India Venster Hiking Trail", "Free / R1,700", "Free", "Trail: Free. Guide: Premium."),
        "Kirstenbosch": ("Kirstenbosch Garden", "R100 – R250", "RR", "SA: R100. Intl: R250."),
        "Silvermine Reservoir": ("Silvermine Reservoir", "R44 – R200", "R", "SA: R44. Intl: R200."),
        "Table Mountain National Park": ("Table Mountain National Park", "Free – R400", "Free", "Open access: Free. Gated: Fees apply."),
        "Pedal Boat Cape Town": ("Pedal Boat Cape Town", "R100", "R", "30 min rental."),
        "Clovelly Golf Course": ("Clovelly Golf Course", "R945 – R1,650", "RRR", "Seasonal green fees."),
        
        # Specific fixes from old clean_data.py
        "Woolley’s Tidal Pool": ("Woolley’s Tidal Pool", "Free", "Free", "Kalk Bay"),
        "Judas’ Peak": ("Judas’ Peak", "Free", "Free", "Hout Bay"),
        "Elephant's Eye Cave": ("Elephant's Eye Cave", "R", "R", "Silvermine"),
        "Myburgh's Waterfall Ravine": ("Myburgh's Waterfall Ravine", "Free", "Free", "Hout Bay"),
        "Helderberg West Peak": ("Helderberg West Peak", "R", "R", "Somerset West"),
        "Chapman's Peak Drive Lookout Point": ("Chapman's Peak Drive Lookout Point", "R", "R", "Hout Bay"),
        "Boomslang Canopy Trail (Kirstenbosch Tree Canopy Walkway)": ("Boomslang Canopy Trail", "R", "R", "Newlands"),
        "Cecilia Ravine Waterfall": ("Cecilia Ravine Waterfall", "Free", "Free", "Constantia"),
        "Old Cape Point Lighthouse": ("Old Cape Point Lighthouse", "R", "R", "Cape Point"),
        "Tjing Tjing House": ("Tjing Tjing House", "RRR", "RRR", "City Centre")
    }

    # Apply updates
    for i, row in df.iterrows():
        name = row['Name']
        
        # Clean emojis
        cleaned_name = re.sub(r'[🧗]', '', name).strip()
        if cleaned_name != name:
            df.at[i, 'Name'] = cleaned_name
            name = cleaned_name

        matched = None
        if name in price_updates:
            matched = price_updates[name]
        else:
            # Partial match checks
            for k in price_updates:
                if k in name:
                    matched = price_updates[k]
                    break
        
        if matched:
            new_name, num, band, note = matched
            
            # Special case for Chapman's vs Drive
            if "Chapman" in name and "Drive" not in new_name and "toll" in str(row['Description']).lower():
                # Skip naming it Hike if it's the Drive
                continue
                
            df.at[i, 'Name'] = new_name
            
            # Only update price if provided
            if num != "R" and num != "Free" and num is not None:
                df.at[i, 'Numerical_Price'] = num
            if band != "R" and band is not None:
                 df.at[i, 'Price_Range'] = band
            
            # Suburb/Note handling
            # If the 'note' looks like a suburb (simple string), treat as suburb update
            if note and len(note) < 20 and "," not in note and " " not in note:
                 df.at[i, 'Suburb'] = note
            elif note:
                 # Append to description if not present
                 desc = str(row['Description'])
                 if note not in desc:
                     df.at[i, 'Description'] = f"{note} {desc}".replace('nan', '')

    # ---------------------------------------------------------
    # 3. GENERAL CLEANUP
    # ---------------------------------------------------------
    
    # Suburbs defaults
    missing_suburbs = df['Suburb'].isna() | (df['Suburb'] == '') | (df['Suburb'] == 'nan')
    if missing_suburbs.any():
        print(f"Filled {missing_suburbs.sum()} blank suburbs with 'Cape Town'.")
        df.loc[missing_suburbs, 'Suburb'] = 'Cape Town'

    # Price defaults
    missing_prices = df['Price_Range'].isna() | (df['Price_Range'] == '')
    if missing_prices.any():
        print(f"Filled {missing_prices.sum()} blank prices with 'R'.")
        df.loc[missing_prices, 'Price_Range'] = 'R'
        df.loc[missing_prices, 'Numerical_Price'] = 'R100-R200'

    # Save cleaned CSV
    df.to_csv(CSV_FILE, index=False)
    print("✓ CSV Saved.")

    # 4. JSON PATCH (Remove 'nan')
    print(f"\nPatching {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    venues = data.get('venues', [])
    fixed_count = 0
    
    for venue in venues:
        # Fix Suburb "nan"
        sub = venue.get('suburb')
        if not sub or str(sub).lower() == 'nan':
            # Fallback to CSV
            row = df[df['Name'] == venue.get('name')]
            if not row.empty:
                val = row.iloc[0]['Suburb']
                if pd.notna(val):
                    venue['suburb'] = str(val)
                    fixed_count += 1
        
        # Fix Rating "nan" or null
        rating = venue.get('rating')
        if rating is None or str(rating).lower() == 'nan':
             venue['rating'] = None # Ensure explicit null

    if fixed_count > 0:
        data['metadata']['updated_at'] = pd.Timestamp.now().isoformat()
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        print(f"✓ Patched {fixed_count} venues in JSON.")
    else:
        print("✓ JSON appears clean.")

if __name__ == "__main__":
    clean_data()
