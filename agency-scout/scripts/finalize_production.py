import pandas as pd
import os
import shutil

DATA_DIR = 'data'
CSV_FILE = os.path.join(DATA_DIR, 'agency_leads.csv')
JSON_FILE = os.path.join(DATA_DIR, 'agency_leads.json')
CACHE_DIR = os.path.join(DATA_DIR, 'cache')
SCRIPTS_TO_REMOVE = ['massive_populate_v2.py', 'scripts/build_database.py']

def finalize():
    print("--- FINALIZING FOR PRODUCTION ---")
    
    # 1. Convert CSV to JSON
    if os.path.exists(CSV_FILE):
        print(f"Converting {CSV_FILE} to JSON...")
        try:
            df = pd.read_csv(CSV_FILE)
            # Ensure index=False equivalent for JSON (records orientation)
            df.to_json(JSON_FILE, orient='records', indent=2)
            print(f"SUCCESS: Created {JSON_FILE} with {len(df)} records.")
        except Exception as e:
            print(f"Error converting to JSON: {e}")
    else:
        print(f"WARNING: {CSV_FILE} not found!")

    # 2. Delete Cache
    if os.path.exists(CACHE_DIR):
        print(f"Removing cache directory: {CACHE_DIR}")
        try:
            shutil.rmtree(CACHE_DIR)
            print("SUCCESS: Cache removed.")
        except Exception as e:
            print(f"Error removing cache: {e}")
    
    # 3. Remove Scripts
    for script in SCRIPTS_TO_REMOVE:
        if os.path.exists(script):
            print(f"Removing script: {script}")
            try:
                os.remove(script)
                print("SUCCESS: Script removed.")
            except Exception as e:
                print(f"Error removing script {script}: {e}")

    print("--- CLEANUP COMPLETE ---")

if __name__ == "__main__":
    finalize()
