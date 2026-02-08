from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
import pandas as pd
from datetime import datetime

# Import Services
from services.maps import MapsService
from services.auditor import WebsiteAuditor
from services.scoring import calculate_score, generate_advice, detect_vibes, recommend_package

app = FastAPI()

# Mount Static & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize Services
maps_service = MapsService()

# Data Storage (In-Memory for now, or load from CSV)
LEADS_FILE = 'data/agency_leads.csv'

def load_leads():
    if os.path.exists(LEADS_FILE):
        try:
            df = pd.read_csv(LEADS_FILE).fillna('')
            leads = df.to_dict(orient='records')
            
            # Legacy Data Migration: Generate IDs if missing
            updated = False
            for lead in leads:
                if 'id' not in lead or not lead['id']:
                    lead['id'] = generate_lead_id(lead.get('Name', ''), lead.get('Address', ''))
                    updated = True
            
            # Save back if we populated new IDs
            if updated:
                df = pd.DataFrame(leads)
                df.to_csv(LEADS_FILE, index=False)
                
            return leads
        except Exception as e:
            print(f"Error loading leads: {e}")
            return []
    return []

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/leads")
async def get_leads():
    return load_leads()

@app.get("/api/export")
async def export_leads():
    """Download the leads CSV directly"""
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, 'r') as f:
            content = f.read()
        return HTMLResponse(content=content, media_type='text/csv', headers={"Content-Disposition": "attachment; filename=agency_leads.csv"})
    return {"error": "No data found"}

class SearchRequest(BaseModel):
    category: str
    location: str

import hashlib

def generate_lead_id(name, address):
    """Generate a consistent ID based on name and address"""
    raw = f"{name}-{address}".encode('utf-8')
    return hashlib.md5(raw).hexdigest()[:8]

@app.get("/lead/{lead_id}", response_class=HTMLResponse)
async def lead_details(request: Request, lead_id: str):
    leads = load_leads()
    lead = next((l for l in leads if str(l.get('id', '')) == lead_id), None)
    
    if not lead:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Lead not found (ID mismatch)"}, status_code=404)
        
    return templates.TemplateResponse("lead_details.html", {"request": request, "lead": lead})

@app.post("/api/scan")
async def scan_venues(search: SearchRequest):
    base_category = search.category
    location = search.location
    
    # Generate Permutations for Massive Coverage
    # If it's a "Deep" scan, we expand the single query into multiple specific ones
    queries = []
    if getattr(search, 'deep', True): # Default to Deep if not specified
        if base_category == "Restaurants":
            prefixes = ["Best", "Cheap", "Luxury", "Romantic", "Family", "Italian", "Burger", "Steak", "Sushi", "Cafe", "Bistro"]
            queries = [f"{p} {base_category} in {location}" for p in prefixes]
        elif base_category == "Wineries":
            queries = [f"Best Wineries in {location}", f"Family Friendly Wineries in {location}", f"Wineries with Restaurant in {location}"]
        elif base_category == "Gyms":
            queries = [f"Gyms in {location}", f"Crossfit in {location}", f"Yoga Studio in {location}", f"Pilates in {location}"]
        else:
            queries = [f"Best {base_category} in {location}", f"Cheap {base_category} in {location}"]
        
        # Add the base generic query too
        queries.append(f"{base_category} in {location}")
    else:
        queries = [f"{base_category} in {location}"]

    print(f"--- MASSIVE SCAN INITIATED ---")
    print(f"Targeting {len(queries)} sub-queries for '{base_category}' in '{location}'")

    all_raw_places = []
    seen_place_ids = set()

    # 1. Maps Search Loop
    for q in queries:
        try:
            # We use a slightly smaller max_results per sub-query to be efficient, 
            # but rely on the breadth of queries to get quantity.
            print(f"Scanning sub-query: {q}")
            places = maps_service.search_places(q, max_results=40, search_strategy="deep_discovery")
            
            for p in places:
                pid = p.get('id')
                if pid and pid not in seen_place_ids:
                    seen_place_ids.add(pid)
                    all_raw_places.append(p)
                    
        except Exception as e:
            print(f"Error scanning '{q}': {e}")
            continue

    print(f"Total Unique Places Found: {len(all_raw_places)}")

    # 2. Filter & Deduplicate (against existing CSV)
    existing_leads = load_leads()
    existing_names = {l['Name'] for l in existing_leads}
    
    places_to_process = []
    for place in all_raw_places:
        name = place.get('displayName', {}).get('text')
        if name and name not in existing_names:
            places_to_process.append(place)
            
    print(f"New Candidates to Audit: {len(places_to_process)}")

    # Helper function for parallel execution
    def process_place(place):
        try:
            name = place.get('displayName', {}).get('text')
            website = place.get('websiteUri', '')
            
            # Audit
            auditor = WebsiteAuditor(website)
            try:
                auditor.audit(name)
            except Exception as e:
                # Silent fail for audit, continue with data we have
                pass
            
            # Score
            score, tags = calculate_score(place, auditor)
            
            # BOOST LOGIC: Hidden Gems (Bluebird Cafe Rule)
            rating = place.get('rating', 0)
            reviews = place.get('userRatingCount', 0)
            
            if (not website and not auditor.guessed_domain) and reviews > 50 and rating >= 4.0:
                score += 50
                tags.append("Hidden Gem")
            
            advice = generate_advice(place, auditor)
            vibes = detect_vibes(place, auditor)
            package = recommend_package(score, tags)
            
            website_status = 'Good'
            if not website:
                if auditor.guessed_domain:
                    website_status = 'Found by Scout'
                else:
                    website_status = 'Missing'
            elif auditor.issues:
                website_status = 'Issues'

            lead = {
                'id': generate_lead_id(name, place.get('formattedAddress')),
                'Name': name,
                'Lead_Score': score,
                'Tags': tags,
                'Vibes': vibes,
                'Package_Name': package['name'],
                'Package_Price': package['price'],
                'Package_Includes': package['includes'],
                'Advice': advice,
                'Emails': ', '.join(auditor.emails) if auditor else '',
                'Socials': ', '.join(auditor.socials) if auditor else '',
                'Website_Status': website_status,
                'Issues': ', '.join(auditor.issues) if auditor else 'No Website',
                'Tech_Stack': ', '.join(auditor.tech_stack) if auditor else '',
                'Rating': rating,
                'Reviews': reviews,
                'Website': auditor.url if auditor.url else '',
                'Phone': place.get('internationalPhoneNumber'),
                'Address': place.get('formattedAddress')
            }
            return lead
        except Exception as e:
            return None

    # 3. Parallel Processing (Massive Scale)
    import concurrent.futures
    new_results = []
    
    # Use ThreadPoolExecutor - increased workers for massive scan
    max_workers = 20 # Bump up to 20 for speed
    if places_to_process:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_place = {executor.submit(process_place, place): place for place in places_to_process}
            for future in concurrent.futures.as_completed(future_to_place):
                result = future.result()
                if result:
                    new_results.append(result)

    # 4. Sort and Slice (Top 50)
    # We increased retention from 20 to 50 because we have way more data now
    new_results.sort(key=lambda x: x['Lead_Score'], reverse=True)
    top_results = new_results[:50] 
    
    if new_results:
        print(f"Processed {len(new_results)} leads. Keeping top {len(top_results)}.")

    # 5. Save to CSV
    if top_results:
        all_leads = existing_leads + top_results
        df = pd.DataFrame(all_leads)
        df = df.sort_values(by='Lead_Score', ascending=False)
        # Deduplicate by Name just in case
        df = df.drop_duplicates(subset=['Name'])
        os.makedirs('data', exist_ok=True)
        df.to_csv(LEADS_FILE, index=False)
        
    return {"message": f"Massive Scan complete. Scanned {len(queries)} queries. Found {len(all_raw_places)} places. Added {len(top_results)} unique high-value leads.", "leads": top_results}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
