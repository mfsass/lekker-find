import json

def extract_venues():
    try:
        with open('public/lekker-find-data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        venues = data.get('venues', [])
        output = []
        for v in venues:
            name = v.get('name', 'N/A')
            category = v.get('category', 'N/A')
            suburb = v.get('suburb', 'N/A')
            output.append(f"{name} | {category} | {suburb}")
        
        with open('venues_check_list.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(output))
        print(f"Successfully extracted {len(output)} venues.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_venues()
