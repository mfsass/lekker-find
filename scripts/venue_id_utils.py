#!/usr/bin/env python3
"""
Venue ID Utilities
==================
Provides stable, consistent venue ID generation to prevent image sync issues.

The ID is based on the venue name, ensuring it remains consistent even when
CSV order changes or venues are reordered.
"""

import re
import hashlib


def generate_stable_venue_id(venue_name: str) -> str:
    """
    Generate a stable, filesystem-safe ID from a venue name.
    
    Strategy:
    1. Convert to lowercase
    2. Remove special characters (apostrophes, etc.)
    3. Replace spaces with hyphens
    4. Truncate to reasonable length
    5. Add short hash suffix to handle collisions
    
    Examples:
        "Woolley's Tidal Pool" -> "woolleys-tidal-pool-a3f2"
        "Beerhouse on Long" -> "beerhouse-on-long-8c91"
        "Camps Bay Beach" -> "camps-bay-beach-1b4e"
    
    Args:
        venue_name: The name of the venue
        
    Returns:
        A stable, filesystem-safe identifier
    """
    if not venue_name:
        raise ValueError("Venue name cannot be empty")
    
    # Normalize the name
    normalized = venue_name.lower()
    
    # Replace apostrophes with empty string (keep the s)
    normalized = re.sub(r"['']", '', normalized)
    
    # Replace non-alphanumeric with hyphens (but preserve already-combined words)
    normalized = re.sub(r'[^a-z0-9]+', '-', normalized)
    
    # Remove leading/trailing hyphens
    normalized = normalized.strip('-')
    
    # Truncate to 40 chars (leave room for hash suffix)
    if len(normalized) > 40:
        normalized = normalized[:40].rstrip('-')
    
    # Generate a short hash to handle potential collisions
    # Use first 4 chars of MD5 hash for uniqueness
    hash_suffix = hashlib.md5(venue_name.encode('utf-8')).hexdigest()[:4]
    
    return f"{normalized}-{hash_suffix}"


def get_image_filename(venue_id: str) -> str:
    """
    Get the image filename for a venue.
    
    Args:
        venue_id: The stable venue ID
        
    Returns:
        The image filename (e.g., "woolleys-tidal-pool-a3f2.jpg")
    """
    return f"{venue_id}.jpg"


def get_image_path(venue_id: str, base_path: str = "/images/venues") -> str:
    """
    Get the full image path for a venue.
    
    Args:
        venue_id: The stable venue ID
        base_path: The base path for images
        
    Returns:
        The full image path (e.g., "/images/venues/woolleys-tidal-pool-a3f2.jpg")
    """
    return f"{base_path}/{get_image_filename(venue_id)}"


if __name__ == "__main__":
    # Test the ID generator
    test_names = [
        "Woolley's Tidal Pool",
        "Beerhouse on Long",
        "Camps Bay Beach",
        "Saunders Rock",
        "Silvermine",
        "Sidecar Adventures",
        "Papa Ron's Shisa Nyama",
        "Ganesh",
    ]
    
    print("Venue ID Generator Test")
    print("=" * 60)
    for name in test_names:
        venue_id = generate_stable_venue_id(name)
        print(f"{name:30} -> {venue_id}")
    print("=" * 60)
