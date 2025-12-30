#!/usr/bin/env python3
"""
Test embedding quality for Lekker Find.
Verifies that semantically similar tags cluster together.
"""

import json
import numpy as np

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def main():
    print("=" * 60)
    print("LEKKER FIND - EMBEDDING QUALITY TEST")
    print("=" * 60)
    
    # Load embeddings
    with open('public/lekker-find-data.json', 'r') as f:
        data = json.load(f)
    
    tags = data['tag_embeddings']
    venues = data['venues']
    
    print(f"\nLoaded {len(venues)} venues, {len(tags)} tags")
    
    # Test 1: Tag similarity tests
    print("\n--- Tag Similarity Tests ---")
    tests = [
        # Should be HIGH (similar vibes)
        {'pair': ['Romantic', 'Cozy'], 'expect': 'high'},
        {'pair': ['Lively', 'Fun'], 'expect': 'high'},
        {'pair': ['Hidden', 'Secret'], 'expect': 'high'},
        {'pair': ['Scenic', 'Big-views'], 'expect': 'high'},
        {'pair': ['Peaceful', 'Quiet'], 'expect': 'high'},
        # Should be LOW (opposite vibes)
        {'pair': ['Peaceful', 'Lively'], 'expect': 'low'},
        {'pair': ['VIP', 'Good-value'], 'expect': 'low'},
        {'pair': ['Famous', 'Hidden'], 'expect': 'low'},
    ]
    
    passed = 0
    for test in tests:
        tag1, tag2 = test['pair']
        if tag1 not in tags or tag2 not in tags:
            print(f"⚠ Missing tag: {tag1} or {tag2}")
            continue
        
        sim = cosine_similarity(tags[tag1], tags[tag2])
        pct = round(sim * 100)
        
        # High = >50%, Low = <50%
        is_pass = (test['expect'] == 'high' and sim > 0.5) or \
                  (test['expect'] == 'low' and sim < 0.5)
        
        icon = '✓' if is_pass else '✗'
        print(f"{icon} {tag1:15} ↔ {tag2:15}: {pct:3}% (expect {test['expect']})")
        
        if is_pass:
            passed += 1
    
    print(f"\nTag tests: {passed}/{len(tests)} passed")
    
    # Test 2: Sample venue matching
    print("\n--- Venue Matching Test ---")
    print("Query: ['Romantic', 'Coastal']")
    
    if 'Romantic' in tags and 'Coastal' in tags:
        # Mean pool the query
        query = np.mean([tags['Romantic'], tags['Coastal']], axis=0)
        
        # Find top 5 matches
        scores = []
        for venue in venues:
            sim = cosine_similarity(query, venue['embedding'])
            scores.append({
                'name': venue['name'],
                'vibes': venue['vibes'],
                'score': round(sim * 100)
            })
        
        scores.sort(key=lambda x: x['score'], reverse=True)
        
        print("\nTop 5 matches:")
        for i, v in enumerate(scores[:5], 1):
            vibes = ', '.join(v['vibes'][:3])
            print(f"  {i}. {v['name']} ({v['score']}%) - {vibes}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
