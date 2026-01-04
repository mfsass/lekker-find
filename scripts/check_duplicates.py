
import json
from difflib import SequenceMatcher

def check_fuzzy_duplicates():
    with open('public/lekker-find-data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    venues = data['venues']
    names = [v['name'] for v in venues]
    
    print(f"Checking {len(names)} venues for fuzzy duplicates...")
    
    potential_duplicates = []
    
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            name1 = names[i]
            name2 = names[j]
            
            # Simple containment check
            if name1.lower() in name2.lower() or name2.lower() in name1.lower():
                 potential_duplicates.append((name1, name2, 1.0))
                 continue

            # Fuzzy check
            ratio = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
            if ratio > 0.8:
                potential_duplicates.append((name1, name2, ratio))
    
    if not potential_duplicates:
        print("No duplicates found.")
    else:
        print(f"Found {len(potential_duplicates)} potential duplicates:")
        for n1, n2, score in potential_duplicates:
            print(f" - {n1} <-> {n2} ({score:.2f})")

if __name__ == "__main__":
    check_fuzzy_duplicates()
