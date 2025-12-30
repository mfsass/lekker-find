import http.server
import socketserver
import json
import os
import csv
import sys
import time

# Configuration
PORT = 8000
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FILE = 'data-262-2025-12-26.csv' 

class AdminHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/add-venue':
            try:
                # 1. Read Data
                content_len = int(self.headers.get('Content-Length'))
                post_body = self.rfile.read(content_len)
                data = json.loads(post_body)
                
                print(f"\n[Server] Received add request for: {data.get('name')}")

                # 2. Append to CSV
                row = [
                    data.get('name', ''),
                    data.get('category', ''),
                    data.get('touristLevel', ''),
                    data.get('priceRange', ''),
                    data.get('numericalPrice', ''),
                    data.get('bestSeason', ''),
                    data.get('vibes', ''),
                    data.get('shortDesc', ''),
                    data.get('rating', ''),
                    data.get('vibeDesc', '')
                ]
                
                # Check for CSV format consistency (quotes etc handled by csv module)
                csv_path = os.path.join(PROJECT_ROOT, CSV_FILE)
                with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(row)
                
                print(f"✅ Appended to {CSV_FILE}")
                
                # 3. Run Pipeline Steps
                self.run_pipeline_steps()

                # 4. Respond Success
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": "Venue added and processed!"}).encode())
                
            except Exception as e:
                print(f"❌ Error processing request: {e}")
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
        else:
            self.send_error(404, "Not Found")

    def run_pipeline_steps(self):
        """Runs the python scripts sequentially"""
        # Ensure we are in project root
        os.chdir(PROJECT_ROOT)
        
        # A. Fetch Images (Google Places)
        print("\n[Step A] Fetching external images...")
        exit_code = os.system('python scripts/fetch_images.py')
        if exit_code != 0: print("⚠️ Step A warning/error")

        # B. Localize Images
        print("\n[Step B] Localizing images...")
        exit_code = os.system('python scripts/localize_images.py')
        if exit_code != 0: print("⚠️ Step B warning/error")

        # C. Enrich (Descriptions/Ratings)
        # Note: enrich_venues usually skips if description exists. 
        # If user left description blank in form, this will fill it.
        print("\n[Step C] Enriching data (AI)...")
        exit_code = os.system('python scripts/enrich_venues.py')
        if exit_code != 0: print("⚠️ Step C warning/error")

        # D. Generate Embeddings (Final JSON)
        print("\n[Step D] Generating embeddings & JSON...")
        exit_code = os.system('python scripts/generate_embeddings.py')
        if exit_code != 0: 
            print("❌ Step D Failed")
            raise Exception("Embedding generation failed")

        print("\n--- ✅ Pipeline Complete ---")

if __name__ == "__main__":
    # Ensure we start from project root
    os.chdir(PROJECT_ROOT)
    print(f"Directory: {os.getcwd()}")
    print(f"Starting Admin Server at http://localhost:{PORT}")
    print(f"Use the tool at http://localhost:{PORT}/admin/add-venue.html")
    
    with socketserver.TCPServer(("", PORT), AdminHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()
