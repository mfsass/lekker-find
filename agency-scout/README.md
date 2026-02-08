# 🕵️ Agency Scout - Production Ready

**Lekker Find's Lead Generation Engine.**
Consolidated database of **173 verified leads** across Stellenbosch, Strand, and Somerset West.

### 🚀 Quick Start (Production)

1.  **Install Expectations:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Dashboard:**
    ```bash
    uvicorn app:app --reload --port 8000
    ```

3.  **View Leads:**
    Open [http://localhost:8000](http://localhost:8000)

---

### 📂 Data Structure

-   `data/agency_leads.csv`: **Primary Database** (Used by App). Contains 173 unique leads.
-   `data/agency_leads.json`: **Portable Export** (Machine Readable).
-   `services/`: Core logic (Maps, Auditor).

### 📊 Capabilities

-   **Deep Discovery**: Scans 40+ permutations per location (Restaurants, Wineries, Real Estate).
-   **Auto-Audit**: Checks SSL, Mobile Friendliness, Tech Stack, and Contact Info.
-   **Lead Scoring**: Ranks leads by "Pain Score" (High Score = Better Lead).
-   **Deduplication**: Ensures unique agency candidates.

### 🛠 Maintenance

To freshen data:
1.  Clear `data/agency_leads.csv`.
2.  Use the `scan_venues` endpoint via the UI (Note: API rate limits apply).
