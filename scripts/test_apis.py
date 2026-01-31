import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

MAPS_API_KEY = os.getenv('MAPS_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def test_google_maps():
    print("Testing Google Maps API...")
    url = 'https://places.googleapis.com/v1/places:searchText'
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': MAPS_API_KEY,
        'X-Goog-FieldMask': 'places.displayName'
    }
    payload = {
        'textQuery': 'Table Mountain, Cape Town'
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            if 'places' in data and len(data['places']) > 0:
                print(f"  [OK] Google Maps API Success: Found '{data['places'][0]['displayName']['text']}'")
                return True
            else:
                print("  [FAIL] Google Maps API Success but no results found.")
                return False
        else:
            print(f"  [FAIL] Google Maps API Failed with status {response.status_code}")
            print(f"    Error: {response.text}")
            return False
    except Exception as e:
        print(f"  [ERROR] Google Maps API Error: {e}")
        return False

def test_openai():
    print("Testing OpenAI API...")
    if not OPENAI_API_KEY:
        print("  [FAIL] OPENAI_API_KEY not found in .env")
        return False
        
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Use a common model for testing
            messages=[{"role": "user", "content": "Say 'Connection Successful'"}],
            max_tokens=10
        )
        content = response.choices[0].message.content.strip()
        print(f"  [OK] OpenAI API Success: '{content}'")
        return True
    except Exception as e:
        print(f"  [ERROR] OpenAI API Error: {e}")
        return False

if __name__ == "__main__":
    print("-" * 40)
    maps_ok = test_google_maps()
    print("-" * 40)
    openai_ok = test_openai()
    print("-" * 40)
    
    if maps_ok and openai_ok:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED.")
