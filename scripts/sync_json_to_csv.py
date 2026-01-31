import json
import csv
import io

JSON_FILE = "public/lekker-find-data.json"
CSV_FILE = "data-262-2025-12-26.csv"

# Fields in CSV order
CSV_FIELDS = [
    "Name", "Category", "Tourist_Level", "Price_Range", "Numerical_Price", 
    "Best_Season", "Vibe", "Description", "Rating", "VibeDescription", 
    "Suburb", "place_id", "image_url"
]

def sync_data():
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            venues = data.get('venues', [])
    except FileNotFoundError:
        print(f"Error: {JSON_FILE} not found.")
        return

    print(f"Syncing {len(venues)} venues to {CSV_FILE}...")
    
    with open(CSV_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        
        for venue in venues:
            # Map JSON fields to CSV columns
            row = {
                "Name": venue.get('name', ''),
                "Category": venue.get('category', ''),
                "Tourist_Level": venue.get('tourist_level', ''),
                "Price_Range": venue.get('price_tier', ''), # price_tier -> Price_Range
                "Numerical_Price": venue.get('numerical_price', ''),
                "Best_Season": venue.get('best_season', ''),
                "Vibe": venue.get('vibes', ''), # Check if this is a list or string in JSON? Typically string in CSV
                "Description": venue.get('description', ''),
                "Rating": venue.get('rating', ''),
                "VibeDescription": venue.get('vibeDescription', ''),
                "Suburb": venue.get('suburb', ''),
                "place_id": venue.get('place_id', ''),
                "image_url": venue.get('image_url', '')
            }
            writer.writerow(row)
            
    print(f"Successfully synced {len(venues)} rows to {CSV_FILE}.")

if __name__ == "__main__":
    sync_data()
