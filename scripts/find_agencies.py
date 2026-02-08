#!/usr/bin/env python3
"""
Lekker Find - Agency Lead Discovery
===================================
Finds restaurants in Stellenbosch/Somerset West that need a new website.
Scores leads based on Google Maps popularity + Website Quality.

Usage:
    python scripts/find_agencies.py --location "Stellenbosch"
    python scripts/find_agencies.py --test-names "Bluebird Cafe R44,Casa Vera,Bossa Strand"
"""

import os
import sys
import argparse
import requests
# Suppress InsecureRequestWarning from verify=False
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import ssl
import socket
import re
import math
import time
import builtwith
import pandas as pd
from urllib.parse import urlparse
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

# Configuration
MAPS_API_KEY = os.getenv('MAPS_API_KEY')
TEXT_SEARCH_URL = 'https://places.googleapis.com/v1/places:searchText'

CAPE_TOWN_LOCATION_BIAS = {
    "circle": {
        "center": {"latitude": -33.9249, "longitude": 18.4241},
        "radius": 50000.0
    }
}

class WebsiteAuditor:
    def __init__(self, url):
        self.url = url
        self.domain = urlparse(url).netloc
        self.issues = []
        self.tech_stack = []
        self.emails = set()
        self.socials = set()
        self.ttfb = 0
        self.mobile_friendly = False
        self.copyright_year = None
        self.ssl_valid = False
        self.status_code = 0
        self.high_value_keywords = []

    def check_ssl(self):
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=self.domain) as s:
                s.settimeout(5)
                s.connect((self.domain, 443))
                cert = s.getpeercert()
                self.ssl_valid = True
        except:
            self.issues.append("SSL Invalid/Missing")
            self.ssl_valid = False

    def audit(self):
        print(f"    Scanning {self.url}...")
        try:
            # 1. SSL Check
            self.check_ssl()

            # 2. Request & Performance
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            start_time = time.time()
            response = requests.get(self.url, headers=headers, timeout=10, verify=False)
            self.ttfb = response.elapsed.total_seconds()
            self.status_code = response.status_code

            if self.status_code != 200:
                self.issues.append(f"Broken Link (Status {self.status_code})")
                return

            if self.ttfb > 1.5:
                self.issues.append(f"Slow Server (TTFB {self.ttfb:.2f}s)")

            # 3. Content Analysis (Mobile, Freshness, Contact)
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text()
            
            # Mobile
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            if viewport:
                self.mobile_friendly = True
            else:
                self.issues.append("Not Mobile Friendly (No viewport tag)")

            # Freshness (Copyright Year)
            # Look for copyright patterns: © 2024, (c) 2023, etc.
            years = re.findall(r'(?:©|&copy;|Copyright)\s*(?:20)(\d{2})', str(response.content))
            if not years:
                 years = re.findall(r'(?:20)(\d{2})', text_content[-500:]) # Fallback scan footer text
            
            if years:
                latest_year = max([int(y) for y in years])
                self.copyright_year = 2000 + latest_year
                if self.copyright_year < (datetime.now().year - 2):
                    self.issues.append(f"Outdated (© {self.copyright_year})")

            # Contact Info (Emails)
            # Simple regex for emails
            found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text_content)
            # Filter dummy emails
            for email in found_emails:
                if not any(x in email for x in ['example.com', 'yourdomain.com', '.png', '.jpg', '.svg']):
                    self.emails.add(email)

            # Social Media & Pixels
            text_lower = str(response.content).lower()
            if 'connect.facebook.net' in text_lower or 'fbevents.js' in text_lower:
                self.tech_stack.append("Facebook Pixel")
            if 'googletagmanager.com' in text_lower or 'google-analytics.com' in text_lower:
                self.tech_stack.append("Google Analytics")

            # Social Media Links
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                if 'facebook.com' in href: self.socials.add('Facebook')
                if 'instagram.com' in href: self.socials.add('Instagram')
                if 'linkedin.com' in href: self.socials.add('LinkedIn')
                if 'twitter.com' in href or 'x.com' in href: self.socials.add('X/Twitter')
                if 'tiktok.com' in href: self.socials.add('TikTok')

            # High Value Signals (Keywords)
            keywords = ['wedding', 'function', 'corporate', 'event', 'conference', 'luxury', 'estate', 'fine dining', 'tasting menu', 'wagyu', 'crayfish']
            for kw in keywords:
                if kw in text_lower:
                    self.high_value_keywords.append(kw)
            
            # 4. Tech Stack (CMS Detection)
            try:
                tech = builtwith.parse(self.url)
                if 'cms' in tech:
                    self.tech_stack.extend(tech['cms'])
                if 'web-frameworks' in tech:
                    self.tech_stack.extend(tech['web-frameworks'])
                if 'advertising-networks' in tech:
                    self.tech_stack.extend(tech['advertising-networks'])
            except:
                pass 
                
        except requests.exceptions.Timeout:
            self.issues.append("Website Timeout (>10s)")
        except requests.exceptions.ConnectionError:
            self.issues.append("Connection Refused / Down")
        except Exception as e:
            self.issues.append(f"Audit Error: {str(e)[:50]}")


def generate_advice(place, auditor):
    advice = []
    name = place.get('displayName', {}).get('text', 'Venue')
    rating = place.get('rating', 0)
    reviews = place.get('userRatingCount', 0)
    price_level = place.get('priceLevel', '')
    
    # 1. Budget/Ads Signal
    if auditor and ("Facebook Pixel" in auditor.tech_stack or "Google Analytics" in auditor.tech_stack):
        if "Slow Server" in str(auditor.issues) or "Not Mobile Friendly" in str(auditor.issues):
            advice.append("💰 HIGH VALUE: They are running Ads/Analytics but have a bad site. Pitch: 'You are wasting ad spend sending traffic to a slow/broken site'.")
        else:
             advice.append("Marketing Active: They track data. Pitch: 'Improve conversion rates'.")

    # Scene 1: High Popularity, No/Bad Website
    if reviews > 100:
        if not place.get('websiteUri'):
            advice.append(f"Traffic Waste: {reviews} reviews but NO website. Pitch: 'Capture direct bookings instead of giving fees to UberEats/Booking platforms'.")
        elif auditor and ("Broken Link" in str(auditor.issues) or "Connection Refused" in str(auditor.issues)):
            advice.append(f"CRITICAL: Site is DOWN. Pitch: 'Immediate fix needed'.")
            
    # Scene 2: High Value Signals
    if auditor and auditor.high_value_keywords:
        advice.append(f"High Value: Mentions {', '.join(auditor.high_value_keywords[:3])}. Pitch: 'Premium clients expect a premium digital experience'.")

    # Scene 3: Mobile Issues
    if auditor and "Not Mobile Friendly" in str(auditor.issues):
        advice.append("Mobile: '50%+ of traffic bounces. We build mobile-first'.")
        
    # 4. Outdated
    if auditor and "Outdated" in str(auditor.issues):
        advice.append(f"Refresh: 'Copyright is {auditor.copyright_year}. Modernize to match your brand'.")
        
    if not advice:
        advice.append("General Upgrade: 'Modernize digital presence'.")
        
    return " | ".join(advice)


def calculate_score(place, auditor):
    # 1. Popularity Score (0-50)
    rating = place.get('rating', 0) or 0
    reviews = place.get('userRatingCount', 0) or 0
    
    if reviews == 0:
        popularity_score = 0
    else:
        # Log scale: 100 reviews -> 2, 1000 -> 3, 10000 -> 4
        # Rating factor: 4.5 -> 1.5. 
        # Score approx: 1.5 * 3 * 10 = 45
        popularity_score = (max(rating, 3.0) - 3.0) * math.log10(reviews) * 10
    
    # 2. Pain Points (0-100+)
    pain_points = 0
    if not place.get('websiteUri'):
        pain_points += 100
    
    if auditor:
        issues_str = str(auditor.issues)
        if "Broken Link" in issues_str or "Connection Refused" in issues_str:
            pain_points += 90
        if "Not Mobile Friendly" in issues_str:
            pain_points += 50
        if "Outdated" in issues_str:
            pain_points += 30
        if "Slow Server" in issues_str:
            pain_points += 20
        if "SSL Invalid" in issues_str:
            pain_points += 20
        if not auditor.socials:
            pain_points += 10
            
    # 3. Budget Likelihood (New)
    budget_score = 0
    price_level = place.get('priceLevel', '')
    if price_level in ['PRICE_LEVEL_EXPENSIVE', 'PRICE_LEVEL_VERY_EXPENSIVE']:
        budget_score += 20
    
    if auditor:
        # They spend on tech/marketing already
        if "Facebook Pixel" in auditor.tech_stack: budget_score += 20
        if "Google Analytics" in auditor.tech_stack: budget_score += 10
        # High Value Content
        if auditor.high_value_keywords: budget_score += 15 # e.g. Weddings/Functions imply budget
    
    # Total
    total = popularity_score + pain_points + budget_score
    return round(total, 1), f"Pain: {pain_points}, Pop: {round(popularity_score)}, Budget: {budget_score}"

def search_places(query):
    if not MAPS_API_KEY:
        print("Error: MAPS_API_KEY not set")
        return []

    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': MAPS_API_KEY,
        'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.websiteUri,places.rating,places.userRatingCount,places.internationalPhoneNumber,places.priceLevel,places.types'
    }
    
    print(f"  Searching Maps for: '{query}'...")
    response = requests.post(
        TEXT_SEARCH_URL,
        headers=headers,
        json={
            'textQuery': query,
            'locationBias': CAPE_TOWN_LOCATION_BIAS,
            'pageSize': 5 
        }
    )
    
    if response.status_code != 200:
        print(f"  Maps API Error: {response.text}")
        return []
        
    return response.json().get('places', [])

def main():
    parser = argparse.ArgumentParser(description="Find agency leads")
    parser.add_argument('--location', type=str, help="Location to search (e.g., Stellenbosch)")
    parser.add_argument('--test-names', type=str, help="Comma-separated list of specific names to test")
    
    args = parser.parse_args()
    
    places = []
    
    if args.test_names:
        names = [n.strip() for n in args.test_names.split(',')]
        print(f"Running TEST MODE for: {names}")
        for name in names:
            found = search_places(name)
            if found:
                # Pick the best match (first one usually)
                places.append(found[0])
            else:
                print(f"  Could not find '{name}' on Maps")
                
    elif args.location:
        # Generic Search
        queries = [
            f"restaurants in {args.location}",
            f"cafes in {args.location}"
        ]
        for q in queries:
            results = search_places(q)
            places.extend(results)
    else:
        print("Please provide --location or --test-names")
        return

    # De-duplicate places and filter by location (South Africa only)
    seen_ids = set()
    unique_places = []
    for p in places:
        # Check address for South Africa/Western Cape to filter out international results
        address = p.get('formattedAddress', '')
        if 'South Africa' not in address and 'Western Cape' not in address:
            print(f"  Skipping international result: {p.get('displayName', {}).get('text')} ({address})")
            continue
            
        # Only add if it has an ID and hasn't been seen
        if 'id' in p and p['id'] not in seen_ids:
            unique_places.append(p)
            seen_ids.add(p['id'])
            
    print(f"\nProcessing {len(unique_places)} venues...")
    leads = []
    
    for place in unique_places:
        name = place.get('displayName', {}).get('text', 'Unknown')
        website = place.get('websiteUri')
        
        print(f"\nAnalyzing: {name}")
        auditor = None
        
        if website:
            auditor = WebsiteAuditor(website)
            auditor.audit()
            if auditor.issues:
                print(f"  ⚠ Issues: {', '.join(auditor.issues)}")
            else:
                print(f"  ✓ Website OK (TTFB: {auditor.ttfb:.2f}s)")
        else:
             print("  ⚠ NO WEBSITE LINKED")
             
        score, pain = calculate_score(place, auditor)
        advice = generate_advice(place, auditor)
        
        leads.append({
            'Name': name,
            'Lead_Score': score,
            'Pain_Score': pain,
            'Advice': advice,
            'Emails': ', '.join(auditor.emails) if auditor else '',
            'Socials': ', '.join(auditor.socials) if auditor else '',
            'Website_Status': 'Missing' if not website else ('Issues' if auditor and auditor.issues else 'Good'),
            'Issues': ', '.join(auditor.issues) if auditor else 'No Website',
            'Tech_Stack': ', '.join(auditor.tech_stack) if auditor else '',
            'Rating': place.get('rating'),
            'Reviews': place.get('userRatingCount'),
            'Website': website,
            'Phone': place.get('internationalPhoneNumber'),
            'Address': place.get('formattedAddress')
        })
        
    # Sort by Lead Score
    if leads:
        df = pd.DataFrame(leads)
        df = df.sort_values(by='Lead_Score', ascending=False)
        
        # Save
        output_file = 'data/agency_leads.csv'
        os.makedirs('data', exist_ok=True)
        df.to_csv(output_file, index=False)
        
        print("\n" + "="*60)
        print(f"REPORT GENERATED: {output_file}")
        print("="*60)
        # Show specific columns
        print(df[['Name', 'Lead_Score', 'Advice', 'Emails', 'Socials']].head(10).to_string())
    else:
        print("\nNo leads found.")

if __name__ == "__main__":
    main()
