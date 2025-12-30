# Lekker Find - Data & Scripts

This directory contains utility scripts for managing venue data, images, and embeddings.

## 🛠️ Data Management Workflow

### 1. Add New Venues (Automated)
The easiest way to add venues is using the Admin Tool with the Automation Server.

1.  **Start the Server:**
    ```bash
    python scripts/serve_admin.py
    ```
2.  **Open Browser:** Go to `http://localhost:8000/admin/add-venue.html`
3.  **Add Venue:** Fill in the details and click **"🚀 Save & Process"**.
    *   This will automatically append to CSV, fetch images, enrich data, and regenerate embeddings in one step.

### 2. Manual Method
If you prefer manual control:
1. Open `admin/add-venue.html` (drag into browser or use Live Server).
2. Generate the CSV row and paste it into `data-262-2025-12-26.csv`.
3.  Run the scripts manually as needed (see below).

### 3. Enrich Data (Optional)
If you want to auto-generate `VibeDescription` using GPT-50-nano (or similar) instead of writing them manually:
```bash
python scripts/enrich_venues.py
```
*   **Note:** The Admin tool allows you to write these manually, which is often better/cheaper.

### 4. Image Management
To fetch and localize images for venues:
```bash
# Fetch new images from Google Places (External APIs)
python scripts/fetch_images.py

# Download remote images to local /public/images/venues/ folder
python scripts/localize_images.py
```

---

## 📂 Key Files

-   `generate_embeddings.py`: **Main script** for building the app's data file (`public/lekker-find-data.json`).
-   `ab_test_embeddings.py`: Benchmark script to scientifically test embedding quality and scoring logic.
-   `enrich_venues.py`: AI script to generate rich descriptions for venues.
-   `fetch_images.py`: Fetches image URLs from Google connection.
-   `localize_images.py`: Downloads images locally to avoid external dependencies.

## 🧪 Benchmarking
To test if the search logic is improving:
```bash
python scripts/ab_test_embeddings.py
```
This runs a suite of test cases (e.g., "Romantic Coastal") and measures precision/ranking quality.

---

## 💡 Best Practices
-   **Always run `generate_embeddings.py`** after changing the CSV.
-   **Local Images:** The app prefers local images (`/images/venues/v{id}.jpg`). Ensure `localize_images.py` is run if you've fetched new URLs.
