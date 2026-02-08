import requests
import ssl
import socket
import re
import time
import builtwith
import whois
from urllib.parse import urlparse
from datetime import datetime
from bs4 import BeautifulSoup

class WebsiteAuditor:
    def __init__(self, url):
        self.url = url
        self.domain = urlparse(url).netloc
        self.issues = []
        self.tech_stack = []
        self.emails = set()
        self.socials = set()
        self.high_value_keywords = []
        self.ttfb = 0
        self.mobile_friendly = False
        self.copyright_year = None
        self.ssl_valid = False
        self.status_code = 0
        self.domain_expiring = False
        self.guessed_domain = None

    def check_domain_status(self):
        """Check domain expiration and existence."""
        pass
        # Speed Optimization: Disable WHOIS for massive scans as it blocks too long
        # try:
        #     w = whois.whois(self.domain)
        #     if w.expiration_date:
        #         exp_date = w.expiration_date
        #         if isinstance(exp_date, list):
        #             exp_date = exp_date[0]
        #         
        #         if isinstance(exp_date, datetime):
        #             days_to_expire = (exp_date - datetime.now()).days
        #             if days_to_expire < 30:
        #                 self.issues.append(f"Domain Expiring Soon ({days_to_expire} days)")
        #                 self.domain_expiring = True
        # except:
        #     pass

    def guess_and_check_domain(self, venue_name):
        """
        If no website is provided, try to guess it:
        1. Clean name (remove 'Stellenbosch', 'Restaurant', etc).
        2. Try name.co.za
        3. DNS check to see if it exists.
        """
        if self.url: return

        clean_name = re.sub(r'[^a-zA-Z0-9]', '', venue_name.lower())
        potential_domain = f"{clean_name}.co.za"
        
        try:
            # DNS Check
            socket.gethostbyname(potential_domain)
            self.guessed_domain = f"http://{potential_domain}"
            self.issues.append(f"Website Missing on Maps (Found: {potential_domain})")
            # Set URL for further auditing
            self.url = self.guessed_domain
            self.domain = potential_domain
            # Now check status since we found it
            self.check_domain_status()
        except:
            pass # Domain doesn't exist

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

    def audit(self, venue_name=None):
        if not self.url and venue_name:
            self.guess_and_check_domain(venue_name)

        if not self.url:
            return # Still no URL, nothing to audit

        print(f"    Scanning {self.url}...")
        
        # 0. Domain Check
        self.check_domain_status()

        try:
            # 1. SSL Check
            self.check_ssl()

            # 2. Request & Performance
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            start_time = time.time()
            try:
                response = requests.get(self.url, headers=headers, timeout=10, verify=False)
                self.ttfb = response.elapsed.total_seconds()
                self.status_code = response.status_code
            except requests.exceptions.RequestException:
                self.issues.append("Connection Failed (Site Down)")
                return

            if self.status_code != 200:
                self.issues.append(f"Broken Link (Status {self.status_code})")
                return

            if self.ttfb > 1.5:
                self.issues.append(f"Slow Server (TTFB {self.ttfb:.2f}s)")

            # 3. Content Analysis
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text()
            text_lower = str(response.content).lower()

            # Mobile
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            if viewport:
                self.mobile_friendly = True
            else:
                self.issues.append("Not Mobile Friendly")

            # Freshness (Refined)
            # Logic: If site has modern tech (Pixel, GA4), ignore old copyright year (likely just lazy footer update)
            years = re.findall(r'(?:©|&copy;|Copyright)\s*(?:20)(\d{2})', str(response.content))
            if not years:
                 years = re.findall(r'(?:20)(\d{2})', text_content[-500:]) 
            
            # Modern Signals
            has_pixel = 'connect.facebook.net' in text_lower or 'googletagmanager.com' in text_lower
            has_meta_social = soup.find('meta', property=re.compile(r'^(og:|twitter:)'))
            server_header = response.headers.get('Server', '')
            if 'cloudflare' in server_header.lower() or 'netlify' in server_header.lower() or 'vercel' in server_header.lower():
                self.tech_stack.append(f"Modern Host ({server_header.split('/')[0]})")
            
            is_marketing_active = has_pixel or has_meta_social
            
            if years:
                latest_year = max([int(y) for y in years])
                self.copyright_year = 2000 + latest_year
                current_year = datetime.now().year
                
                # Only flag as outdated if > 3 years AND no active marketing
                if self.copyright_year < (current_year - 3) and not is_marketing_active:
                    self.issues.append(f"Outdated Content (© {self.copyright_year})")

            # Contact Info
            found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text_content)
            for email in found_emails:
                if not any(x in email for x in ['example.com', 'yourdomain.com', '.png', '.jpg', '.svg', 'wixpress']):
                    self.emails.add(email)

            # Socials & Pixels
            if 'connect.facebook.net' in text_lower or 'fbevents.js' in text_lower:
                self.tech_stack.append("Facebook Pixel")
            if 'googletagmanager.com' in text_lower or 'google-analytics.com' in text_lower:
                self.tech_stack.append("Google Analytics")

            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                if 'facebook.com' in href: self.socials.add('Facebook')
                if 'instagram.com' in href: self.socials.add('Instagram')
                if 'linkedin.com' in href: self.socials.add('LinkedIn')
                if 'twitter.com' in href or 'x.com' in href: self.socials.add('X/Twitter')

            # High Value Keywords
            keywords = ['wedding', 'function', 'corporate', 'event', 'conference', 'luxury', 'estate', 'fine dining', 'boutique', 'premium']
            for kw in keywords:
                if kw in text_lower:
                    self.high_value_keywords.append(kw)
            
            # Tech Stack
            try:
                tech = builtwith.parse(self.url)
                if 'cms' in tech: self.tech_stack.extend(tech['cms'])
                if 'web-frameworks' in tech: self.tech_stack.extend(tech['web-frameworks'])
                if 'advertising-networks' in tech: self.tech_stack.extend(tech['advertising-networks'])
                if 'ecommerce' in tech: self.tech_stack.extend(tech['ecommerce'])
            except:
                pass 
                
        except Exception as e:
            self.issues.append(f"Audit Error: {str(e)[:50]}")
