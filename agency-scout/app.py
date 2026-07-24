from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Import Services
from services.maps import MapsService
from services.auditor import WebsiteAuditor
from services.scoring import calculate_score, generate_advice, detect_vibes, recommend_package
from services.config import load_environment
from services.database import (
    add_to_suppression,
    get_candidate_leads,
    get_email_drafts,
    get_outreach_stats,
    get_suppression_list,
    ingest_agency_leads,
    mark_draft_status,
    update_email_draft,
)
from services.gmail_service import GmailServiceError
from services.llm import LLMServiceError
from services.outreach import approve_and_send, generate_drafts, process_unsubscribe, regenerate_draft

import hashlib
import logging

logger = logging.getLogger(__name__)


async def _daily_draft_job() -> None:
    """Auto-generate 5 drafts every morning. Requires leads in the database."""
    from services.outreach import generate_drafts
    load_environment()
    try:
        result = generate_drafts(limit=5, candidate_limit=10, allow_template_fallback=True)
        created = len(result.get("created", []))
        errors = len(result.get("errors", []))
        logger.info("Daily draft job: created=%d errors=%d", created, errors)
    except Exception as exc:
        logger.error("Daily draft job failed: %s", exc)


_scheduler = AsyncIOScheduler(timezone="Europe/Amsterdam")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _scheduler.add_job(
        _daily_draft_job,
        CronTrigger(hour=9, minute=0, timezone="Europe/Amsterdam"),
        id="daily_drafts",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    _scheduler.start()
    logger.info("Daily draft scheduler started (runs at 09:00 Amsterdam time)")
    yield
    _scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)
load_environment()

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

@app.post("/api/masa/ingest")
async def masa_ingest():
    try:
        result = ingest_agency_leads(Path("data") / "agency_leads.json")
        return {"message": "MASA lead database refreshed", **result}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/masa/candidates")
async def masa_candidates(limit: int = 10):
    return get_candidate_leads(limit)

@app.get("/api/masa/drafts")
async def masa_drafts(limit: int = 5):
    return get_email_drafts(limit, status="Drafted")

@app.get("/api/masa/stats")
async def masa_stats():
    return get_outreach_stats()

@app.get("/api/masa/suppression")
async def masa_suppression(limit: int = 50):
    return get_suppression_list(limit)

@app.post("/api/masa/drafts")
async def masa_create_drafts(limit: int = 5, candidate_limit: int = 10):
    try:
        result = generate_drafts(limit=limit, candidate_limit=candidate_limit, allow_template_fallback=True)
        status_code = 200 if result["created"] else 424
        return JSONResponse(result, status_code=status_code)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/masa/drafts/{draft_id}/regenerate")
async def masa_regenerate(draft_id: int):
    try:
        return regenerate_draft(draft_id, allow_template_fallback=True)
    except (KeyError, LLMServiceError) as e:
        return JSONResponse({"error": str(e)}, status_code=400)

class DraftUpdateRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=180)
    body: str = Field(min_length=1, max_length=2000)

@app.patch("/api/masa/drafts/{draft_id}")
async def masa_update_draft(draft_id: int, update: DraftUpdateRequest):
    try:
        return update_email_draft(draft_id, update.subject, update.body)
    except (KeyError, ValueError) as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.post("/api/masa/drafts/{draft_id}/archive")
async def masa_archive_draft(draft_id: int):
    try:
        mark_draft_status(draft_id, "Archived")
        return {"message": "Draft archived"}
    except (KeyError, ValueError) as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.post("/api/masa/drafts/{draft_id}/approve")
async def masa_approve(draft_id: int):
    try:
        return approve_and_send(draft_id)
    except (KeyError, GmailServiceError) as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/unsubscribe", response_class=PlainTextResponse)
async def unsubscribe(email: str, token: str):
    try:
        process_unsubscribe(email, token)
    except ValueError:
        return PlainTextResponse("Invalid unsubscribe link.", status_code=400)
    return "You have been unsubscribed. No further outreach will be sent to this address."

class SuppressionRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    reason: str = Field(default="Manual suppression", max_length=200)

@app.post("/api/masa/suppression")
async def masa_add_suppression(request: SuppressionRequest):
    try:
        add_to_suppression(request.email, request.reason)
        return {"message": "Email suppressed"}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

class SearchRequest(BaseModel):
    category: str
    location: str
    deep: bool = False
    max_results: int = Field(default=40, ge=5, le=80)


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
    if search.deep:
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
    scan_errors = []

    # 1. Maps Search Loop
    for q in queries:
        try:
            # We use a slightly smaller max_results per sub-query to be efficient, 
            # but rely on the breadth of queries to get quantity.
            print(f"Scanning sub-query: {q}")
            places = maps_service.search_places(
                q,
                max_results=search.max_results,
                search_strategy="deep_discovery" if search.deep else "normal"
            )
            
            for p in places:
                pid = p.get('id')
                if pid and pid not in seen_place_ids:
                    seen_place_ids.add(pid)
                    all_raw_places.append(p)
                    
        except Exception as e:
            print(f"Error scanning '{q}': {e}")
            scan_errors.append({"query": q, "error": str(e)})
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
        df.to_json('data/agency_leads.json', orient='records', indent=2, force_ascii=False)
        ingest_agency_leads(Path("data") / "agency_leads.json")
        
    response_body = {
        "message": f"Scan complete. Scanned {len(queries)} queries. Found {len(all_raw_places)} places. Added {len(top_results)} unique high-value leads.",
        "leads": top_results,
        "errors": scan_errors,
    }
    if scan_errors and not all_raw_places:
        return JSONResponse(response_body, status_code=424)
    return response_body

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
