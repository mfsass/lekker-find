import pandas as pd
import re

CSV_FILE = 'data-262-2025-12-26.csv'

# Data from user request
# format: Current/Partial Name -> (New Clean Name, Numerical Price, Price Band, Context/Notes)
# I will try to match loosely on the key to find the row in CSV
UPDATES = {
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
    "FrameZ": ("FrameZ", "Free", "Free", "Public Yellow Frames. (Selfie studios ~R180)."),
    "Rupert Museum": ("Rupert Museum", "Free", "Free", "Complimentary entry."),
    "Motorcycle Museum Helderberg": ("Motorcycle Museum Helderberg", "R100", "R", "Adult entry."),
    "Franschhoek Motor Museum": ("Franschhoek Motor Museum", "R90", "R", "Adult entry."),
    "The Drama Factory": ("The Drama Factory", "R150 – R180", "R", "Show tickets."),
    "Hi5 Tandem Paragliding": ("Hi5 Tandem Paragliding", "R2,200", "RRR", "Flight R1850 + Photos R350."),
    "PadelDeals": ("PadelDeals", "R100 – R150", "R", "Est. playing cost at local venues (Retailer)."),
    "CityROCK": ("CityROCK Cape Town", "R320", "RR", "Day pass + gear rental."),
    "Kayak Cape Town": ("Kayak Cape Town (Simon’s)", "R500 – R690", "RRR", "Penguin paddle."),
    "Bloc 11": ("Bloc 11 – Diep River", "R140 – R200", "R", "Bouldering day pass."),
    "Cape Town Tandem Paragliding": ("CT Tandem Paragliding", "R2,200", "RRR", "Flight R1800 + Photos R400."),
    "NoodleBox": ("NoodleBox Stellenbosch", "R170 – R220", "RR", "Main dish + drink."),
    "De Vier Restaurant": ("De Vier Restaurant", "R350 – R550", "RRR", "3-course meal estimate."),
    "MERTIA": ("MERTIA", "R1,495 – R1,799", "RRR", "Set Menu. Wine pairing extra (+R1250)."),
    "The Table at De Meye": ("The Table at De Meye", "R595", "RRR", "3-course set menu (food only)."),
    "Stellies iCafe": ("Stellies iCafe", "R40 – R60", "R", "Coffee + muffin special."),
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
    "Hazendal": ("Hazendal – Driving Range", "R160 – R380", "RR", "Hourly bay rental (multiplayer)."),
    "India Venster": ("India Venster Hiking Trail", "Free / R1,700", "Free", "Trail: Free. Guide/Cableway: Premium."),
    "Kirstenbosch": ("Kirstenbosch Garden", "R100 – R250", "RR", "SA: R100. Intl: R250."),
    "Chapmans Peak": ("Chapmans Peak Upgrade", "Free", "Free", "The hike is free."), # This is tricky as duplicates exist
    "Chapman’s Peak": ("Chapman’s Peak (Hike)", "Free", "Free", "The hike (not the drive) is free."),
    "Silvermine Reservoir": ("Silvermine Reservoir", "R44 – R200", "R", "SA: R44. Intl: R200."),
    "The Rock": ("The Rock (Bantry Bay)", "Free", "Free", "Sunset spot."),
    "Constantia Nek": ("Constantia Nek Hiking Trail", "Free", "Free", "Open access."),
    "Table Mountain National Park": ("Table Mountain National Park", "Free – R400", "Free", "Open access: Free. Gated: Fees apply."),
    "Pedal Boat Cape Town": ("Pedal Boat Cape Town", "R100", "R", "30 min rental."),
    "Clovelly Golf Course": ("Clovelly Golf Course", "R945 – R1,650", "RRR", "Highly seasonal green fees.")
}

def clean_and_update():
    print(f"Reading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    
    updated_count = 0
    cleaned_count = 0
    
    # 1. Clean Names & Remove Specific Emojis first
    # Regex to remove emojis or specific undesired chars
    # "Bloc 11 - Diep River 🧗" -> "Bloc 11 - Diep River"
    
    for i, row in df.iterrows():
        original_name = row['Name']
        name = original_name
        
        # Remove emojis (basic range or specific char)
        name = re.sub(r'[🧗]', '', name)
        name = name.strip()
        
        # Update if changed
        if name != original_name:
            df.at[i, 'Name'] = name
            cleaned_count += 1
            print(f"Cleaned: '{original_name}' -> '{name}'")
            original_name = name # Update for next step matching
            
        # 2. Apply Custom Updates (Name, Price, Note)
        # Find which update key matches this row
        
        matched_key = None
        # Try exact match first
        if original_name in UPDATES:
            matched_key = original_name
        else:
            # Try partial match
            for key in UPDATES.keys():
                if key in original_name:
                    matched_key = key
                    break
        
        if matched_key:
            new_name, num_price, price_band, note = UPDATES[matched_key]
            
            # Special case for "Chapman's Peak Drive" vs "Chapman's Peak" (Hike)
            # Check ID or Category if needed, but here we rely on existing text
            is_drive = "Drive" in original_name or "toll" in str(row['Description']).lower()
            
            if "Chapman" in matched_key:
                # Disambiguate
                 if is_drive:
                     new_name, num_price, price_band, note = UPDATES["Chapman"]
                 else:
                     new_name, num_price, price_band, note = UPDATES["Chapman’s Peak"]

            # Update fields
            df.at[i, 'Name'] = new_name
            df.at[i, 'Numerical_Price'] = num_price
            df.at[i, 'Price_Range'] = price_band
            
            # Append note to description if not present? 
            # Or just set a new 'Context' field? The user provided "Context / Notes".
            # CSV has "Description". Let's prepend or append the context to Description 
            # so it appears in the app, or maybe overwrite if the description is generic?
            # User said "Context / Notes" - usually valuable for the user. 
            # Let's append it: "Description... Note: {Current Note}"
            
            current_desc = str(row['Description'])
            if note not in current_desc:
                 # Check if description is 'nan'
                 if pd.isna(row['Description']):
                     df.at[i, 'Description'] = note
                 else:
                     # intelligently append
                     if len(current_desc) > 200:
                         # Trim old desc?
                         pass
                     df.at[i, 'Description'] = f"{note} {current_desc}"
            
            updated_count += 1
            print(f"Updated: {original_name} -> {new_name} ({num_price})")

    # Save
    if updated_count > 0 or cleaned_count > 0:
        df.to_csv(CSV_FILE, index=False)
        print(f"\n✓ Saved {CSV_FILE}. Cleaned {cleaned_count}, Updated {updated_count}.")
    else:
        print("\nNo changes needed.")

if __name__ == "__main__":
    clean_and_update()
