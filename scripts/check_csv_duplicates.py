import pandas as pd
from difflib import SequenceMatcher
import re

CSV_FILE = 'data-262-2025-12-26.csv'

def normalize(name):
    # Remove common words and punctuation for comparison
    name = name.lower()
    name = re.sub(r"'s", "", name)
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\b(the|and|restaurant|cafe|bar|hike|trail|drive|nature|reserve|park|garden|gardens|farm|estate|vineyards|winery)\b", "", name)
    return name.strip()

def check_csv_duplicates():
    print(f"Reading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    names = df['Name'].tolist()
    
    print(f"Checking {len(names)} venues in CSV...")
    
    # Check for direct duplicates first
    dups = df[df.duplicated(subset=['Name'], keep=False)]
    if not dups.empty:
        print("\n=== EXACT DUPLICATES ===")
        print(dups['Name'].unique())

    # Fuzzy check
    print("\n=== FUZZY DUPLICATES ===")
    seen = set()
    warnings = []
    
    for i, name1 in enumerate(names):
        norm1 = normalize(name1)
        for j in range(i + 1, len(names)):
            name2 = names[j]
            norm2 = normalize(name2)
            
            # Skip if very different length
            if abs(len(norm1) - len(norm2)) > 10:
                continue

            # Normalized Exact Match
            if norm1 == norm2 and norm1 != "":
                warnings.append(f"MATCH: '{name1}' <-> '{name2}'")
                continue
                
            # Fuzzy
            ratio = SequenceMatcher(None, norm1, norm2).ratio()
            if ratio > 0.85:
                warnings.append(f"FUZZY ({ratio:.2f}): '{name1}' <-> '{name2}'")
    
    # Sort and print
    for w in sorted(warnings):
        print(w)

if __name__ == "__main__":
    check_csv_duplicates()
