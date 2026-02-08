import math

def generate_advice(place, auditor):
    advice = []
    # name = place.get('displayName', {}).get('text', 'Venue')
    rating = place.get('rating', 0)
    reviews = place.get('userRatingCount', 0)
    
    # 1. Budget/Ads Signal
    if auditor and ("Facebook Pixel" in auditor.tech_stack or "Google Analytics" in auditor.tech_stack):
        if "Slow Server" in str(auditor.issues) or "Not Mobile Friendly" in str(auditor.issues):
            advice.append("[HIGH VALUE] Running Ads but site is poor. Pitch: 'Stop wasting ad spend on a broken site'.")
        else:
             advice.append("Marketing Active: Tracks data. Pitch: 'Improve conversion rates with better UX'.")

    # 2. High Popularity, No/Bad Website
    if reviews > 100:
        if not place.get('websiteUri'):
            advice.append(f"Traffic Waste: {reviews} reviews but NO website. Pitch: 'Capture direct bookings'.")
        elif auditor and ("Broken Link" in str(auditor.issues) or "Connection Refused" in str(auditor.issues)):
            advice.append(f"[CRITICAL] Site is DOWN. Pitch: 'Immediate fix needed'.")
            
    # 3. High Value Signals
    if auditor and auditor.high_value_keywords:
        advice.append(f"High Value: Mentions {', '.join(auditor.high_value_keywords[:3])}. Pitch: 'Premium clients expect a premium digital experience'.")

    # 4. Mobile Issues
    if auditor and "Not Mobile Friendly" in str(auditor.issues):
        advice.append("Mobile: '50%+ of traffic bounces. We build mobile-first'.")
        
    # 5. Outdated
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
        popularity_score = (max(rating, 3.0) - 3.0) * math.log10(reviews) * 10
    
    # 2. Pain Points & Tags
    pain_points = 0
    tags = []
    
    if not place.get('websiteUri'):
        pain_points += 100
        tags.append("No Website")
    
    if auditor:
        issues_str = str(auditor.issues)
        if "Broken Link" in issues_str or "Connection Refused" in issues_str:
            pain_points += 90
            tags.append("Site Down")
        if "Not Mobile Friendly" in issues_str:
            pain_points += 50
            tags.append("Desktop Only")
        if "Outdated" in issues_str:
            pain_points += 30
            tags.append(f"Outdated (©{auditor.copyright_year})")
        if "Slow Server" in issues_str:
            pain_points += 20
            tags.append("Slow Load")
        if "SSL Invalid" in issues_str:
            pain_points += 20
            tags.append("Insecure")
        if not auditor.socials:
            pain_points += 10
            tags.append("No Socials")
            
    # 3. Budget Likelihood
    budget_score = 0
    price_level = place.get('priceLevel', '')
    if price_level in ['PRICE_LEVEL_EXPENSIVE', 'PRICE_LEVEL_VERY_EXPENSIVE']:
        budget_score += 20
        tags.append("High Budget")
    
    if auditor:
        # They spend on tech/marketing already
        if "Facebook Pixel" in auditor.tech_stack: 
            budget_score += 20
            tags.append("Ads Active")
        if "Google Analytics" in auditor.tech_stack: 
            budget_score += 10
        # High Value Content
        if auditor.high_value_keywords: 
            budget_score += 15 
            tags.append("Luxury")
    
    # Total
    total = popularity_score + pain_points + budget_score
    return round(total, 1), tags

def detect_vibes(place, auditor):
    """Extract attributes that describe the 'feeling' of the place for the pitch."""
    vibes = []
    
    # 1. Price Level
    price = place.get('priceLevel', '')
    if price in ['PRICE_LEVEL_EXPENSIVE', 'PRICE_LEVEL_VERY_EXPENSIVE']:
        vibes.append("Premium/Luxury")
    elif price == 'PRICE_LEVEL_CHEAP':
        vibes.append("Budget/Friendly")
        
    # 2. Categories
    categories = [c.lower() for c in place.get('types', [])]
    if 'winery' in categories or 'vineyard' in categories: vibes.append("Scenic/Wine Farm")
    if 'cafe' in categories or 'bakery' in categories: vibes.append("Cozy/Casual")
    if 'bar' in categories or 'night_club' in categories: vibes.append("Energetic/Nightlife")
    
    # 3. Keywords from Auditor
    if auditor:
        if any(x in auditor.high_value_keywords for x in ['wedding', 'function', 'event']):
            vibes.append("Event Venue")
        if 'fine dining' in auditor.high_value_keywords:
            vibes.append("High-End")
            
    return list(set(vibes))

def recommend_package(lead_score, tags):
    """Suggest a specific agency package + price point."""
    if "No Website" in tags or "Site Down" in tags:
        return {
            "name": "The Digital Foundation",
            "price": "R 8,500",
            "includes": "Custom Website, Google Maps Setup, Basic SEO"
        }
    elif "Desktop Only" in tags or "Outdated" in tags:
         return {
            "name": "The Modern Refresh",
            "price": "R 5,500",
            "includes": "Mobile-First Redesign, Speed Optimization, Social Integration"
        }
    elif "Ads Active" in tags or "High Budget" in tags:
         return {
            "name": "Performance Marketing",
            "price": "R 3,500 / mo",
            "includes": "Conversion Rate Optimization (CRO), Landing Pages, Ad Management"
        }
    else:
         return {
            "name": "Growth Retainer",
            "price": "R 2,500 / mo",
            "includes": "SEO Content, Monthly Reporting, Google Business Management"
        }
