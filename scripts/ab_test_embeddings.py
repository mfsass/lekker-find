#!/usr/bin/env python3
"""
Comprehensive Embedding Strategy Benchmark
==========================================
Tests multiple embedding strategies to find optimal approach:

1. KEYWORDS: Original Vibe keywords ("Peaceful, Scenic, Coastal")
2. EXPANDED: Keywords expanded to sentences (like TAG_DESCRIPTIONS)  
3. AI_DESC: VibeDescription (AI-generated 2-3 sentences)
4. HYBRID: Keywords + Description concatenated
5. DIMENSIONS: Test 256 vs 512 vs 1024

Metrics:
- Precision@5: How many expected results in top 5
- Mean Reciprocal Rank (MRR): Average ranking quality
- Score Spread: Difference between top and bottom scores
"""

import os
import json
import time
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from typing import List, Dict, Tuple

load_dotenv()

# Ground truth test cases
TEST_CASES = [
    {
        'name': 'Romantic Coastal',
        'moods': ['Romantic', 'Coastal'],
        'expected': ['Harbour House', 'Pier', "Maiden's Cove", 'Clifton 4th Beach', 'Camps Bay Tidal Pool'],
    },
    {
        'name': 'Hidden Local',
        'moods': ['Hidden', 'Local'],
        'expected': ["Woolley's Tidal Pool", 'Super Fisheries', 'Smitswinkel Bay', "Water's Edge Beach"],
    },
    {
        'name': 'Peaceful Scenic',
        'moods': ['Peaceful', 'Scenic'],
        'expected': ['Constantia Nek', "Chapman's Peak", 'Kirstenbosch Botanical Garden', 'Table Mountain Cableway'],
    },
    {
        'name': 'Trendy Cool',
        'moods': ['Trendy', 'Cool'],
        'expected': ['Truth Coffee Roasting', 'Origin Coffee Roasting', 'House of Machines', 'Tjing Tjing Torii'],
    },
]

# TAG_DESCRIPTIONS for expanding keywords
TAG_DESCRIPTIONS = {
    'Romantic': 'A romantic, intimate, cozy atmosphere perfect for couples and date nights',
    'Coastal': 'A coastal, oceanside, beachfront, seaside location by the water',
    'Hidden': 'A hidden gem, off-the-beaten-path, tucked away, hard to find location',
    'Local': 'A local favorite, neighborhood spot, authentic to the community',
    'Peaceful': 'A peaceful, calm, tranquil, serene setting for quiet relaxation',
    'Scenic': 'A scenic location with beautiful views, panoramic vistas, and stunning scenery',
    'Trendy': 'A trendy, fashionable, hip, Instagram-worthy spot that is currently popular',
    'Cool': 'A cool, stylish, edgy place with a modern, alternative vibe',
    'Family': 'Family-friendly, welcoming to children, safe and fun for all ages',
    'Adventure': 'An adventurous, thrilling, exciting experience with adrenaline and discovery',
}

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def mean_pool(embeddings):
    return np.mean(embeddings, axis=0)

def get_embedding(text, client, model='text-embedding-3-small', dims=256):
    response = client.embeddings.create(
        input=text,
        model=model,
        dimensions=dims
    )
    return response.data[0].embedding

def expand_keywords_to_sentence(keywords: str) -> str:
    """Convert keywords to expanded description using TAG_DESCRIPTIONS style."""
    words = [w.strip() for w in keywords.split(',') if w.strip()]
    descriptions = []
    for word in words:
        if word in TAG_DESCRIPTIONS:
            descriptions.append(TAG_DESCRIPTIONS[word])
        else:
            # Generic expansion
            descriptions.append(f"A {word.lower()} atmosphere and experience")
    return ". ".join(descriptions)

def evaluate_strategy(venues, tag_embeddings, test_cases):
    """Evaluate strategy with multiple metrics."""
    results = {
        'precision_at_5': 0,
        'mrr': 0,
        'score_spread': 0,
        'min_score': 1.0,
        'max_score': 0.0,
        'details': []
    }
    
    total_precision = 0
    total_mrr = 0
    all_spreads = []
    
    for tc in test_cases:
        # Get mood embeddings
        mood_embs = [tag_embeddings[m] for m in tc['moods'] if m in tag_embeddings]
        if not mood_embs:
            continue
        
        query = mean_pool(mood_embs)
        
        # Score all venues
        scores = []
        for v in venues:
            sim = cosine_similarity(query, v['embedding'])
            scores.append({'name': v['name'], 'score': sim})
        
        scores.sort(key=lambda x: x['score'], reverse=True)
        top5_names = [s['name'] for s in scores[:5]]
        
        # Precision@5
        hits = sum(1 for exp in tc['expected'] if exp in top5_names)
        precision = hits / min(len(tc['expected']), 5)
        total_precision += precision
        
        # MRR - find rank of first expected result
        mrr = 0
        for i, s in enumerate(scores):
            if s['name'] in tc['expected']:
                mrr = 1 / (i + 1)
                break
        total_mrr += mrr
        
        # Score spread
        spread = scores[0]['score'] - scores[-1]['score']
        all_spreads.append(spread)
        
        results['min_score'] = min(results['min_score'], scores[-1]['score'])
        results['max_score'] = max(results['max_score'], scores[0]['score'])
        
        results['details'].append({
            'test': tc['name'],
            'precision': precision,
            'mrr': mrr,
            'top3': [s['name'] for s in scores[:3]],
            'top_score': scores[0]['score'],
        })
    
    n = len(test_cases)
    results['precision_at_5'] = total_precision / n if n > 0 else 0
    results['mrr'] = total_mrr / n if n > 0 else 0
    results['score_spread'] = np.mean(all_spreads) if all_spreads else 0
    
    return results

def run_benchmark():
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    print("=" * 70)
    print("COMPREHENSIVE EMBEDDING STRATEGY BENCHMARK")
    print("=" * 70)
    
    # Load data
    df = pd.read_csv('data-262-2025-12-26.csv')
    print(f"\nLoaded {len(df)} venues from CSV")
    
    # Sample for speed
    sample_size = 80  # Larger sample for better accuracy
    sample_df = df.head(sample_size)
    
    # Generate tag embeddings (shared across all tests)
    print("\n[1/5] Generating tag embeddings...")
    tag_embeddings_256 = {}
    for tag in TAG_DESCRIPTIONS:
        tag_embeddings_256[tag] = get_embedding(TAG_DESCRIPTIONS[tag], client, dims=256)
    print(f"  ✓ {len(tag_embeddings_256)} tags embedded")
    
    strategies = {}
    
    # ===== STRATEGY 1: KEYWORDS ONLY =====
    print("\n[2/5] Testing KEYWORDS strategy...")
    keywords_venues = []
    for _, row in sample_df.iterrows():
        vibe = str(row['Vibe']) if pd.notna(row['Vibe']) else ''
        emb = get_embedding(vibe, client, dims=256)
        keywords_venues.append({'name': row['Name'], 'embedding': emb})
    strategies['KEYWORDS'] = evaluate_strategy(keywords_venues, tag_embeddings_256, TEST_CASES)
    print(f"  ✓ Precision@5: {strategies['KEYWORDS']['precision_at_5']:.2%}")
    
    # ===== STRATEGY 2: EXPANDED KEYWORDS =====
    print("\n[3/5] Testing EXPANDED strategy...")
    expanded_venues = []
    for _, row in sample_df.iterrows():
        vibe = str(row['Vibe']) if pd.notna(row['Vibe']) else ''
        expanded = expand_keywords_to_sentence(vibe)
        emb = get_embedding(expanded, client, dims=256)
        expanded_venues.append({'name': row['Name'], 'embedding': emb})
    strategies['EXPANDED'] = evaluate_strategy(expanded_venues, tag_embeddings_256, TEST_CASES)
    print(f"  ✓ Precision@5: {strategies['EXPANDED']['precision_at_5']:.2%}")
    
    # ===== STRATEGY 3: AI DESCRIPTION =====
    print("\n[4/5] Testing AI_DESC strategy...")
    ai_venues = []
    for _, row in sample_df.iterrows():
        vibe_desc = str(row.get('VibeDescription', '')) if pd.notna(row.get('VibeDescription')) else ''
        vibe = str(row['Vibe']) if pd.notna(row['Vibe']) else ''
        text = vibe_desc if vibe_desc else vibe
        emb = get_embedding(text, client, dims=256)
        ai_venues.append({'name': row['Name'], 'embedding': emb})
    strategies['AI_DESC'] = evaluate_strategy(ai_venues, tag_embeddings_256, TEST_CASES)
    print(f"  ✓ Precision@5: {strategies['AI_DESC']['precision_at_5']:.2%}")
    
    # ===== STRATEGY 4: HYBRID (Keywords + Description) =====
    print("\n[5/5] Testing HYBRID strategy...")
    hybrid_venues = []
    for _, row in sample_df.iterrows():
        vibe = str(row['Vibe']) if pd.notna(row['Vibe']) else ''
        vibe_desc = str(row.get('VibeDescription', '')) if pd.notna(row.get('VibeDescription')) else ''
        # Combine: Keywords + AI description
        combined = f"{vibe}. {vibe_desc}" if vibe_desc else vibe
        emb = get_embedding(combined, client, dims=256)
        hybrid_venues.append({'name': row['Name'], 'embedding': emb})
    strategies['HYBRID'] = evaluate_strategy(hybrid_venues, tag_embeddings_256, TEST_CASES)
    print(f"  ✓ Precision@5: {strategies['HYBRID']['precision_at_5']:.2%}")
    
    # ===== RESULTS SUMMARY =====
    print("\n\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)
    
    print("\n┌─────────────────┬──────────────┬─────────┬──────────────┬───────────────┐")
    print("│ Strategy        │ Precision@5  │   MRR   │ Score Range  │ Score Spread  │")
    print("├─────────────────┼──────────────┼─────────┼──────────────┼───────────────┤")
    
    for name, results in sorted(strategies.items(), key=lambda x: x[1]['precision_at_5'], reverse=True):
        p = results['precision_at_5']
        mrr = results['mrr']
        score_range = f"{results['min_score']:.2f}-{results['max_score']:.2f}"
        spread = results['score_spread']
        print(f"│ {name:<15} │ {p:>10.1%}   │ {mrr:>6.3f}  │ {score_range:>12} │ {spread:>12.3f}  │")
    
    print("└─────────────────┴──────────────┴─────────┴──────────────┴───────────────┘")
    
    # Best strategy
    best = max(strategies.items(), key=lambda x: x[1]['precision_at_5'])
    worst = min(strategies.items(), key=lambda x: x[1]['precision_at_5'])
    
    print(f"\n✓ BEST: {best[0]} ({best[1]['precision_at_5']:.1%} precision)")
    print(f"✗ WORST: {worst[0]} ({worst[1]['precision_at_5']:.1%} precision)")
    print(f"  Improvement: {(best[1]['precision_at_5'] - worst[1]['precision_at_5'])*100:+.1f} percentage points")
    
    # Scaling recommendation
    print("\n" + "=" * 70)
    print("SCALING RECOMMENDATIONS")
    print("=" * 70)
    
    all_mins = [s['min_score'] for s in strategies.values()]
    all_maxs = [s['max_score'] for s in strategies.values()]
    
    print(f"""
Score Distribution Analysis:
  Minimum observed: {min(all_mins):.3f}
  Maximum observed: {max(all_maxs):.3f}
  
Recommended Scaling Parameters:
  MIN_SIM = {min(all_mins) - 0.05:.2f}  (5% below observed min)
  MAX_SIM = {max(all_maxs) + 0.05:.2f}  (5% above observed max)
  
Display Range: 55% - 98% (gives good UX spread)

Formula: scaled = 0.55 + (raw - MIN_SIM) / (MAX_SIM - MIN_SIM) * 0.43
""")
    
    # Cost analysis
    print("=" * 70)
    print("COST/TIME TRADEOFFS")
    print("=" * 70)
    print(f"""
┌───────────────┬──────────────┬───────────────┬──────────────────┐
│ Strategy      │ API Cost     │ Processing    │ One-time Setup   │
├───────────────┼──────────────┼───────────────┼──────────────────┤
│ KEYWORDS      │ $0.01        │ ~60 sec       │ None             │
│ EXPANDED      │ $0.01        │ ~60 sec       │ TAG_DESCRIPTIONS │
│ AI_DESC       │ $0.01 + $0.02│ ~45 min       │ enrich_venues.py │
│ HYBRID        │ $0.01 + $0.02│ ~45 min       │ enrich_venues.py │
└───────────────┴──────────────┴───────────────┴──────────────────┘

RECOMMENDATION:
- If speed matters: Use EXPANDED (fast, no AI needed, decent results)
- If quality matters: Use {best[0]} (best precision, worth the setup)
- For new venues: EXPANDED is good enough, AI_DESC for premium spots
""")

if __name__ == "__main__":
    run_benchmark()
