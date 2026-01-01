#!/usr/bin/env python3
"""
Image Migration Script
======================
Migrates existing images from index-based naming (v0.jpg, v1.jpg) 
to stable name-based IDs (venue-name-hash.jpg).

This prevents sync issues when CSV order changes.

Usage:
    python scripts/migrate_images_to_stable_ids.py          # Dry run
    python scripts/migrate_images_to_stable_ids.py --apply  # Actually rename files
"""

import json
import os
import sys
import shutil
from pathlib import Path
from venue_id_utils import generate_stable_venue_id, get_image_filename

JSON_PATH = 'public/lekker-find-data.json'
IMAGE_DIR = 'public/images/venues'
BACKUP_DIR = 'public/images/venues_backup'


def migrate_images(dry_run=True):
    """
    Migrate images from old index-based naming to stable IDs.
    
    Args:
        dry_run: If True, only show what would be done without making changes
    """
    print("=" * 70)
    print("IMAGE MIGRATION: Index-based IDs -> Stable Name-based IDs")
    print("=" * 70)
    
    if not os.path.exists(JSON_PATH):
        print(f"✗ ERROR: {JSON_PATH} not found")
        return False
    
    # Load venue data
    print(f"\n[1/5] Loading venue data from {JSON_PATH}...")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    venues = data.get('venues', [])
    print(f"✓ Loaded {len(venues)} venues")
    
    # Create mapping of old ID -> new ID
    print("\n[2/5] Generating stable IDs...")
    migrations = []
    
    for venue in venues:
        old_id = venue.get('id', '')
        name = venue.get('name', '')
        
        if not name:
            print(f"⚠ Warning: Venue with ID {old_id} has no name, skipping")
            continue
        
        new_id = generate_stable_venue_id(name)
        
        # Check if image exists with old naming
        old_filename = f"{old_id}.jpg"
        new_filename = get_image_filename(new_id)
        old_path = os.path.join(IMAGE_DIR, old_filename)
        new_path = os.path.join(IMAGE_DIR, new_filename)
        
        if os.path.exists(old_path):
            migrations.append({
                'venue_name': name,
                'old_id': old_id,
                'new_id': new_id,
                'old_path': old_path,
                'new_path': new_path,
                'old_filename': old_filename,
                'new_filename': new_filename
            })
    
    print(f"✓ Generated stable IDs for {len(migrations)} venues with images")
    
    # Check for potential collisions
    print("\n[3/5] Checking for ID collisions...")
    new_ids = [m['new_id'] for m in migrations]
    unique_ids = set(new_ids)
    
    if len(new_ids) != len(unique_ids):
        print("✗ ERROR: ID collision detected!")
        # Find duplicates
        seen = set()
        for m in migrations:
            if m['new_id'] in seen:
                print(f"  Duplicate ID: {m['new_id']} for {m['venue_name']}")
            seen.add(m['new_id'])
        return False
    
    print(f"✓ No collisions detected ({len(unique_ids)} unique IDs)")
    
    # Show migration plan
    print("\n[4/5] Migration plan:")
    print("-" * 70)
    
    if dry_run:
        print("DRY RUN MODE - No files will be modified")
        print("-" * 70)
    
    for i, mig in enumerate(migrations[:10], 1):  # Show first 10
        print(f"{i:3}. {mig['venue_name'][:30]:30}")
        print(f"     {mig['old_filename']:25} -> {mig['new_filename']}")
    
    if len(migrations) > 10:
        print(f"     ... and {len(migrations) - 10} more")
    
    print("-" * 70)
    print(f"Total images to migrate: {len(migrations)}")
    
    if dry_run:
        print("\nRun with --apply flag to perform migration")
        print("A backup will be created in:", BACKUP_DIR)
        return True
    
    # Perform migration
    print("\n[5/5] Performing migration...")
    
    # Create backup
    print(f"  Creating backup at {BACKUP_DIR}...")
    if os.path.exists(BACKUP_DIR):
        print(f"  ⚠ Backup directory already exists, skipping backup creation")
    else:
        shutil.copytree(IMAGE_DIR, BACKUP_DIR)
        print(f"  ✓ Backup created")
    
    # Rename files
    success = 0
    failed = 0
    
    for mig in migrations:
        try:
            # Check if target already exists
            if os.path.exists(mig['new_path']):
                # If it's the same file (already migrated), skip
                if os.path.samefile(mig['old_path'], mig['new_path']):
                    continue
                print(f"  ⚠ Target exists: {mig['new_filename']}, skipping")
                failed += 1
                continue
            
            os.rename(mig['old_path'], mig['new_path'])
            success += 1
            
            if success % 50 == 0:
                print(f"  Progress: {success}/{len(migrations)}...")
                
        except Exception as e:
            print(f"  ✗ Failed to rename {mig['old_filename']}: {e}")
            failed += 1
    
    print(f"\n✓ Migration complete!")
    print(f"  Success: {success}")
    print(f"  Failed:  {failed}")
    
    if failed > 0:
        print(f"\n⚠ Some files failed to migrate")
        print(f"  Backup is available at: {BACKUP_DIR}")
        return False
    
    # Update JSON file with new IDs
    print(f"\n[6/6] Updating {JSON_PATH} with new stable IDs...")
    
    for venue in venues:
        name = venue.get('name')
        if name:
            new_id = generate_stable_venue_id(name)
            venue['id'] = new_id
            
            # Update image_url if it exists and points to old format
            image_url = venue.get('image_url', '')
            if image_url and image_url.startswith('/images/venues/v'):
                venue['image_url'] = f"/images/venues/{get_image_filename(new_id)}"
    
    # Save updated JSON
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Updated JSON with new stable IDs")
    
    print("\n" + "=" * 70)
    print("MIGRATION SUCCESSFUL!")
    print("=" * 70)
    print(f"\nBackup location: {BACKUP_DIR}")
    print("You can delete the backup once you verify everything works correctly.")
    
    return True


if __name__ == "__main__":
    dry_run = '--apply' not in sys.argv
    
    if dry_run:
        print("\n*** DRY RUN MODE ***\n")
    
    success = migrate_images(dry_run=dry_run)
    
    if not success:
        sys.exit(1)
    
    if dry_run:
        print("\nTo perform the actual migration, run:")
        print("  python scripts/migrate_images_to_stable_ids.py --apply")
