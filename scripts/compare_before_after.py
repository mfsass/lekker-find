import json
import re
from collections import Counter

BEFORE_FILE = "data/backups/lekker-find-data_20260131_121539.json"
AFTER_FILE = "public/lekker-find-data.json"

def load_data(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)['venues']
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return []

def is_address_like(suburb):
    # Check for starting with digit, or containing common street suffixes
    if not suburb: return False
    if re.match(r'^\d+', suburb): return True
    street_suffixes = [' St', ' Rd', ' Ave', ' Dr', ' Cl', ' Ln', 'Street', 'Road', 'Avenue', 'Drive']
    if any(s in suburb for s in street_suffixes) and len(suburb.split()) > 1:
        # Avoid false positives like "Main Rd" which is a valid suburb name in some contexts? 
        # But generally we want to flag these.
        return True
    return False

def analyze(venues, label):
    stats = {
        'count': len(venues),
        'rated_count': sum(1 for v in venues if v.get('rating')),
        'priced_standard_count': sum(1 for v in venues if v.get('price_tier') in ['Free', 'R', 'RR', 'RRR']),
        'imaged_count': sum(1 for v in venues if v.get('image_url') and 'placeholder' not in v.get('image_url', '')),
        'unique_suburbs': len(set(v.get('suburb') for v in venues if v.get('suburb'))),
        'address_like_suburbs': set(v.get('suburb') for v in venues if is_address_like(v.get('suburb')))
    }
    return stats

def main():
    before = load_data(BEFORE_FILE)
    after = load_data(AFTER_FILE)
    
    stats_before = analyze(before, "Before")
    stats_after = analyze(after, "After")
    
    print("## Data Audit Comparison\n")
    print(f"| Metric | Before | After | Change |")
    print(f"| :--- | :--- | :--- | :--- |")
    print(f"| **Total Venues** | {stats_before['count']} | {stats_after['count']} | {stats_after['count'] - stats_before['count']} |")
    print(f"| **Rated Venues** | {stats_before['rated_count']} | {stats_after['rated_count']} | +{stats_after['rated_count'] - stats_before['rated_count']} |")
    print(f"| **Standard Prices** | {stats_before['priced_standard_count']} | {stats_after['priced_standard_count']} | +{stats_after['priced_standard_count'] - stats_before['priced_standard_count']} |")
    print(f"| **Valid Images** | {stats_before['imaged_count']} | {stats_after['imaged_count']} | +{stats_after['imaged_count'] - stats_before['imaged_count']} |")
    print(f"| **Unique Suburbs** | {stats_before['unique_suburbs']} | {stats_after['unique_suburbs']} | {stats_after['unique_suburbs'] - stats_before['unique_suburbs']} |")
    print(f"| **Address-like Suburbs** | {len(stats_before['address_like_suburbs'])} | {len(stats_after['address_like_suburbs'])} | {len(stats_after['address_like_suburbs']) - len(stats_before['address_like_suburbs'])} |")

    print("\n### Suburb Quality Check")
    if stats_after['address_like_suburbs']:
        print("\n**Warning: The following potential 'Address' suburbs remain:**")
        for s in stats_after['address_like_suburbs']:
            print(f"- {s}")
    else:
        print("\n**Success:** No obvious street addresses found in 'After' dataset.")
        
    print("\n### Pricing Standardization")
    non_standard_prices = [v.get('price_tier') for v in after if v.get('price_tier') not in ['Free', 'R', 'RR', 'RRR']]
    if non_standard_prices:
        print(f"\nNon-standard price tiers remaining ({len(non_standard_prices)}): {Counter(non_standard_prices).most_common(5)}...")
    else:
        print("\n**Success:** All prices standardized to Free/R/RR/RRR.")

if __name__ == "__main__":
    main()
