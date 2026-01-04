
import pandas as pd
import json
import math
import sys

CSV_FILE = 'data-262-2025-12-26.csv'
JSON_FILE = 'public/lekker-find-data.json'

def cosine_similarity(v1, v2):
    """Compute cosine similarity between two vectors."""
    if not v1 or not v2: return 0.0
    dot_product = sum(a*b for a,b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a*a for a in v1))
    norm_v2 = math.sqrt(sum(b*b for b in v2))
    if norm_v1 == 0 or norm_v2 == 0: return 0.0
    return dot_product / (norm_v1 * norm_v2)

def remove_duplicates():
    import argparse
    parser = argparse.ArgumentParser(description="Clean up duplicates from CSV and JSON data.")
    parser.add_argument('--check-embeddings', action='store_true', help='Check for semantic duplicates using embeddings')
    parser.add_argument('--threshold', type=float, default=0.92, help='Similarity threshold (0-1)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be removed without doing it')
    args = parser.parse_args()

    print("=" * 60)
    print("LEKKER FIND - REMOVE DUPLICATES")
    print("=" * 60)

    # -------------------------------------------------------------
    # 1. Exact Name / CSV Cleanup
    # -------------------------------------------------------------
    print(f"Reading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    
    initial_count = len(df)
    # Remove exact name duplicates, keeping the last (newest) one
    df = df.drop_duplicates(subset=['Name'], keep='last')
    
    removed_count = initial_count - len(df)
    if removed_count > 0:
        print(f"✓ Found {removed_count} exact duplicates in CSV.")
        if not args.dry_run:
            df.to_csv(CSV_FILE, index=False)
            print("  - Removed.")
    else:
        print("✓ CSV is clean of exact duplicates.")

    # -------------------------------------------------------------
    # 2. JSON Cleanup
    # -------------------------------------------------------------
    print(f"\nReading {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    venues = data.get('venues', [])
    seen_names = set()
    unique_venues = []
    
    duplicates_found = 0
    
    # Specific known duplicates to canonicalize
    # Lowercase mapped to Canonical Name
    CANONICAL_MAP = {
        'de grendel wine estate and restaurant': 'De Grendel',
        'de grendel': 'De Grendel',
        'chapman’s peak drive': 'Chapman’s Peak Drive', # Keep distinct from Hike if possible
    }
    
    for v in venues:
        name = v['name']
        norm_name = name.lower().strip()
        
        # Canonical checks
        if norm_name in CANONICAL_MAP:
             canon = CANONICAL_MAP[norm_name].lower()
             if canon in seen_names:
                 print(f"  Removing duplicate/variant JSON entry: {name}")
                 duplicates_found += 1
                 continue
             else:
                 seen_names.add(canon)
                 # Update name to canonical if needed?
                 # v['name'] = CANONICAL_MAP[norm_name]
                 unique_venues.append(v)
                 continue

        if norm_name in seen_names:
            duplicates_found += 1
            print(f"  Removing duplicate JSON entry: {name}")
        else:
            seen_names.add(norm_name)
            unique_venues.append(v)
            
    if duplicates_found > 0:
        if not args.dry_run:
            data['venues'] = unique_venues
            data['metadata']['total_venues'] = len(unique_venues)
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            print(f"✓ Removed {duplicates_found} duplicates from JSON.")
        else:
             print(f"✓ [Dry Run] Would remove {duplicates_found} duplicates from JSON.")
    else:
        print("✓ JSON is clean of exact duplicates.")

    # -------------------------------------------------------------
    # 3. Embedding / Semantic Check (Optional)
    # -------------------------------------------------------------
    if args.check_embeddings:
        print(f"\nChecking semantic similarity (Threshold: {args.threshold})...")
        
        # O(N^2) check - acceptable for <1000 venues
        suspects = []
        for i in range(len(unique_venues)):
            v1 = unique_venues[i]
            vec1 = v1.get('embedding')
            if not vec1: continue
            
            for j in range(i + 1, len(unique_venues)):
                v2 = unique_venues[j]
                vec2 = v2.get('embedding')
                if not vec2: continue
                
                score = cosine_similarity(vec1, vec2)
                if score >= args.threshold:
                     suspects.append((score, v1['name'], v2['name']))
        
        suspects.sort(reverse=True, key=lambda x: x[0])
        
        if suspects:
            print(f"\n⚠ Found {len(suspects)} pairs with high semantic similarity:")
            for score, n1, n2 in suspects:
                print(f"  {score:.4f}: '{n1}' <-> '{n2}'")
            print("\nAction: Manually remove one from CSV if they are duplicates, then run this script again.")
        else:
            print("✓ No semantic duplicates found.")

if __name__ == "__main__":
    remove_duplicates()
