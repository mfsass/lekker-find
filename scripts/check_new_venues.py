#!/usr/bin/env python3
"""Quick check of the 12 new venues."""
import json

with open('public/lekker-find-data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get the last 12 venues (newly added)
new_venues = data['venues'][-12:]

print("=" * 70)
print("12 NEW VENUES - COMPLETE PROFILE CHECK")
print("=" * 70)

all_complete = True

for i, v in enumerate(new_venues, 1):
    name = v['name']
    rating = v.get('rating', 'N/A')
    suburb = v.get('suburb', 'N/A')
    has_embedding = len(v.get('embedding', [])) == 256
    has_image = bool(v.get('local_image') or v.get('image_url'))
    has_description = bool(v.get('description'))
    vibes = v.get('vibes', [])
    
    status = "✓" if all([has_embedding, has_image, has_description]) else "⚠"
    if status == "⚠":
        all_complete = False
    
    print(f"\n{i}. {name}")
    print(f"   Rating: {rating}/5 | Suburb: {suburb}")
    print(f"   Vibes: {', '.join(vibes[:3]) if vibes else 'None'}")
    print(f"   Embedding: {'✓ 256D' if has_embedding else '✗ Missing'}")
    print(f"   Image: {'✓' if has_image else '✗ Missing'}")
    print(f"   Description: {'✓' if has_description else '✗ Missing'}")

print("\n" + "=" * 70)
if all_complete:
    print("✓ ALL 12 VENUES HAVE COMPLETE PROFILES!")
else:
    print("⚠ Some venues have incomplete profiles")
print("=" * 70)
