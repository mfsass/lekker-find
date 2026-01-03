#!/usr/bin/env python3
"""
Complete Image Regeneration Workflow
=====================================

This script orchestrates the complete image regeneration process:
1. Check for existing duplicates
2. Delete all images
3. Fetch fresh images with duplicate detection
4. Extract and add suburb data
5. Update CSV with suburb column
6. Validate final state

Usage:
    python scripts/regenerate_images_workflow.py --confirm

Without --confirm, runs in dry-run mode showing what would happen.
"""

import sys
import subprocess
import os


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*70}")
    print(f"STEP: {description}")
    print(f"{'='*70}")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Command failed with exit code {e.returncode}")
        return False


def workflow(dry_run: bool = True):
    """Execute the complete workflow."""
    print("=" * 70)
    print("COMPLETE IMAGE REGENERATION WORKFLOW")
    print("=" * 70)
    
    if dry_run:
        print("\n⚠ DRY RUN MODE - No changes will be made")
        print("Add --confirm to actually regenerate images\n")
    else:
        print("\n⚠ THIS WILL DELETE AND REGENERATE ALL IMAGES")
        print("Press Ctrl+C within 5 seconds to cancel...")
        import time
        for i in range(5, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        print("\n✓ Proceeding with regeneration\n")
    
    steps = [
        {
            'cmd': ['python', 'scripts/fetch_images_enhanced.py', '--check-dupes'],
            'desc': 'Check for duplicate images',
            'required': False  # Non-fatal - duplicates are expected
        }
    ]
    
    if not dry_run:
        steps.extend([
            {
                'cmd': ['python', 'scripts/fetch_images_enhanced.py', '--regenerate-all', '--force'],
                'desc': 'Regenerate all images with duplicate detection',
                'required': True
            },
            {
                'cmd': ['python', 'scripts/add_suburb_to_csv.py'],
                'desc': 'Add suburb column to CSV',
                'required': False
            },
            {
                'cmd': ['python', 'scripts/validate_image_sync.py'],
                'desc': 'Validate image-venue sync',
                'required': False
            },
            {
                'cmd': ['python', 'scripts/fetch_images_enhanced.py', '--check-dupes'],
                'desc': 'Final duplicate check',
                'required': False
            }
        ])
    
    # Execute steps
    for i, step in enumerate(steps, 1):
        success = run_command(step['cmd'], f"{i}/{len(steps)}: {step['desc']}")
        
        if not success and step['required']:
            print(f"\n✗ Required step failed. Aborting workflow.")
            return False
    
    if dry_run:
        print("\n" + "=" * 70)
        print("DRY RUN COMPLETE")
        print("=" * 70)
        print("\nTo regenerate images:")
        print("  python scripts/regenerate_images_workflow.py --confirm")
    else:
        print("\n" + "=" * 70)
        print("WORKFLOW COMPLETE!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Review the regenerated images")
        print("  2. Run: python scripts/validate_image_sync.py")
        print("  3. Commit changes if everything looks good")
    
    return True


def main():
    dry_run = '--confirm' not in sys.argv
    success = workflow(dry_run=dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
