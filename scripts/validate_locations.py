import csv
import sys
import os

# Define known associations between keywords and expected valid suburbs (or lists of valid suburbs)
# If a keyword is found in the Name or Description, the Suburb MUST be one of the values in the list.
LOCATION_RULES = {
    "Hellshoogte": ["Stellenbosch"],
    "Jonkershoek": ["Stellenbosch"],
    "Stellenbosch": ["Stellenbosch"],
    "Franschhoek": ["Franschhoek"],
    "Constantia": ["Constantia", "Constantia Nek", "High Constantia"],
    "V&A Waterfront": ["V&A Waterfront", "Waterfront", "Silo District"],
    "Waterfront": ["V&A Waterfront", "Waterfront", "Silo District", "Granger Bay"],
    "Camps Bay": ["Camps Bay"],
    "Clifton": ["Clifton"],
    "Hout Bay": ["Hout Bay"],
    "Kalk Bay": ["Kalk Bay", "Harbour"],
    "Simons Town": ["Simon's Town", "Simon’s Town"], # Handle varied spelling
    "Simon's Town": ["Simon's Town", "Simon’s Town"],
    "Muizenberg": ["Muizenberg"],
    "Sea Point": ["Sea Point", "Three Anchor Bay"],
    "Green Point": ["Green Point"],
    "Woodstock": ["Woodstock", "Salt River"], # Often close/blurred
    "Winelands": ["Stellenbosch", "Franschhoek", "Paarl", "Somerset West", "Constantia", "Durbanville", "Helderberg", "Elgin"]
}

def check_csv(filename):
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found.")
        return

    mismatches = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2): # Start at 2 for header
            name = row.get('Name', '')
            desc = row.get('Description', '')
            suburb = row.get('Suburb', '').strip()
            
            # Combine text for search
            text_to_search = f"{name} {desc}"
            
            for keyword, valid_suburbs in LOCATION_RULES.items():
                # Case insensitive check
                if keyword.lower() in text_to_search.lower():
                    # Check if current suburb is valid (fuzzy match or exact?)
                    # Let's do exact match or partial match
                    is_valid = False
                    for valid in valid_suburbs:
                        if valid.lower() in suburb.lower():
                            is_valid = True
                            break
                    
                    if not is_valid:
                        # Double check logic: if "Waterfront" is keyword, but suburb is "Stellenbosch", FAIL.
                        # However, we must be careful of "Near Waterfront" description.
                        # But for "Hellshoogte", it's distinct.
                        mismatches.append({
                            "line": i,
                            "name": name,
                            "keyword_found": keyword,
                            "current_suburb": suburb,
                            "expected_one_of": valid_suburbs,
                            "context": desc[:50] + "..."
                        })

    # Report
    import json
    with open('anomalies.json', 'w') as f:
        json.dump(mismatches, f, indent=2)

    if mismatches:
        print(f"Found {len(mismatches)} potential location anomalies. Saved to anomalies.json")
        print("-" * 80)
        for m in mismatches:
            try:
                print(f"Line {m['line']}: {m['name'].encode('ascii', 'replace').decode()}")
                print(f"  - Found keyword: {m['keyword_found']} -> Expected: {m['expected_one_of']}")
                print(f"  - Current Suburb: {m['current_suburb'].encode('ascii', 'replace').decode()}")
                print(f"  - Context: {m['context'].encode('ascii', 'replace').decode()}")
                print("-" * 80)
            except Exception as e:
                print(f"Error printing item on line {m['line']}: {e}")
    else:
        print("No obvious anomalies found with current keyword set.")

if __name__ == "__main__":
    # Find the data file
    files = [f for f in os.listdir('.') if f.startswith('data-') and f.endswith('.csv')]
    if files:
        # Sort by date usually or just pick the first likely one
        target_file = files[0] # Simplistic, but works for now given directory listing showed one main file
        print(f"Scanning {target_file}...")
        check_csv(target_file)
    else:
        print("No data file found.")
