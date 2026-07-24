# MASA Quick Start Guide
**Mindy Autonomous Sales Agent — May 2026 Setup**

---

## ✅ What's Already Working

- **FastAPI Dashboard** with Outreach Desk UI
- **SQLite Database** with 47 contactable leads ready
- **Gemma 4 Integration** (Google GenAI API) as primary model
- **Daily Auto-Scheduler** runs every morning at 9:00 AM Amsterdam time
- **Gmail Draft System** with RFC 8058 compliance
- **Anti-Spam Validation** built-in (blocks AI slop, enforces word limits)

---

## 🔑 Required: Add Your API Keys

Open `C:\Users\markussass\Desktop\.env.txt` and add:

```bash
# Google Gemini API (for Gemma 4 — free tier available)
GEMINI_API_KEY=your-gemini-api-key-here

# OpenRouter API (fallback when Gemini unavailable)
OPEN_ROUTER_API=your-openrouter-key-here
```

### Where to Get Keys

1. **GEMINI_API_KEY** (FREE)
   - Go to: https://aistudio.google.com/apikey
   - Click "Create API Key"
   - Copy and paste into .env.txt

2. **OPEN_ROUTER_API** (Backup, Optional)
   - Go to: https://openrouter.ai/keys
   - Create account + generate key
   - Used only if Gemini fails

---

## 🚀 Start the System

### 1. Open Terminal

```powershell
cd "C:\Users\markussass\OneDrive - StratHost Office 365\Documents\lekker-find\agency-scout"
```

### 2. Start Dashboard

```powershell
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

You'll see:
```
INFO:     Daily draft scheduler started (runs at 09:00 Amsterdam time)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Open Dashboard

Go to: **http://localhost:8000**

---

## 📋 Daily Workflow (5 Minutes/Day)

### Morning Routine (Automatic)
- **09:00 AM**: System auto-generates 5 email drafts from top candidates
- You get a notification (check terminal logs)

### Your Review (Manual)
1. Open dashboard → **Outreach Desk** section
2. Review the 5 drafts:
   - ✅ **Edit** if tone feels off
   - 🔄 **Regenerate** to get new version
   - 📦 **Archive** if lead isn't relevant
   - 🚀 **Approve & Send** when ready

### Daily Limits (Reputation Safety)
- Max 5 sends per day (current setting)
- System won't auto-approve — you must manually click "Approve & Send"

---

## 🎯 How It Works

### Model Stack (Gemma 4 First)
1. **Primary**: Gemma 4 31B (via Google Gemini API)
   - FREE tier available
   - Proven for cold email in World Bank project
   - Low temperature (0.55) for consistency

2. **Fallback 1**: Mistral Small 3.2 (OpenRouter)
   - If Gemini unavailable or fails validation

3. **Fallback 2**: Local Template
   - If both LLMs fail
   - Deterministic, always passes validation

### Email Validation Rules
Every draft must pass these checks:
- ✅ Under 100 words (excluding URLs)
- ✅ Starts with "Hi [Name]"
- ✅ One CTA only: "Mind if I send over a free, zero-strings mock-up?"
- ✅ Opt-out line: "Opt out: [URL]"
- ❌ Blocks: "hope you're well", "stunning", "modernize", etc.

---

## 🔧 Configuration Options

### Change Daily Schedule

Edit `app.py` line 62:
```python
CronTrigger(hour=9, minute=0, timezone="Europe/Amsterdam")
```

Change `hour=9` to any hour (24-hour format).

### Change Daily Draft Limit

Edit `app.py` line 47:
```python
result = generate_drafts(limit=5, candidate_limit=10, allow_template_fallback=True)
```

Change `limit=5` to desired number (recommended: 5-10).

### Switch Model Priority

Edit `.env.txt`:
```bash
# Force specific model (bypasses Gemini)
OPENROUTER_MODEL=mistralai/mistral-small-3.2-24b-instruct

# Or switch Gemini model
GEMINI_MODEL=gemma-4-26b-a4b-it
```

---

## 📊 Dashboard Features

### Outreach Desk Tab

**Candidate Pool** (left column)
- Top 10 leads ranked by score
- Shows: Name, Email, Lead Score, Issues, Advice
- Click "Suppress" to block permanently

**Draft Review** (right column)
- 5 pending drafts awaiting approval
- Edit subject/body inline
- Regenerate with one click
- Archive bad drafts
- Approve → sends via Gmail

**Stats Panel**
- Total candidates available
- Drafts sent today
- Total suppressed addresses
- Reply rate (once tracking enabled)

---

## 🛡️ Anti-Spam Compliance

### Current Setup ✅
- **Volume**: 5 emails/day (safe for new domain)
- **Authentication**: RFC 8058 List-Unsubscribe headers
- **Validation**: Anti-AI-slop rules built-in
- **Manual approval**: No auto-send

### Required Later (Before Live Sends)
- [ ] SPF record on your domain
- [ ] DKIM signing enabled
- [ ] DMARC policy published (`p=none` to start)
- [ ] Gmail OAuth credentials (see below)

---

## 📧 Enable Gmail Sending

### Step 1: Create OAuth Credentials

1. Go to: https://console.cloud.google.com
2. Select project #495746473793 (or create new)
3. **Enable billing** on the project
4. Go to: **APIs & Services → Credentials**
5. Click **Create Credentials → OAuth 2.0 Client ID**
6. Application type: **Desktop application**
7. Name: "MASA Gmail Integration"
8. Download JSON → Save as:
   ```
   C:\Users\markussass\OneDrive - StratHost Office 365\Documents\lekker-find\agency-scout\credentials.json
   ```

### Step 2: First-Time Authorization

1. Dashboard → Generate 5 drafts
2. Click **Approve & Send** on one draft
3. Browser will open asking for Gmail permissions
4. Approve the permissions
5. System creates `token.json` automatically
6. Future sends work without browser popup

---

## 🔍 Testing Checklist

### Before First Send

- [ ] Verify API keys in .env.txt:
  ```powershell
  cat "C:\Users\markussass\Desktop\.env.txt" | Select-String GEMINI_API_KEY
  ```
- [ ] Verify leads ingested:
  ```powershell
  # Open dashboard → Outreach Desk → Should show 10 candidates
  ```
- [ ] Generate test draft:
  ```powershell
  # Dashboard → Click "Generate 5 Drafts"
  ```
- [ ] Check draft quality:
  ```
  - Under 100 words?
  - One CTA only?
  - No AI slop phrases?
  ```

### After First Send

- [ ] Email delivered (check Gmail sent folder)
- [ ] Email not in recipient's spam (use test address)
- [ ] Unsubscribe link works (click it, verify suppression)
- [ ] Dashboard shows "Sent" status

---

## 🐛 Troubleshooting

### Error: "Gemini API key not found"
**Fix**: Add `GEMINI_API_KEY=...` to `C:\Users\markussass\Desktop\.env.txt`

### Error: "No candidates available"
**Fix**: 
```powershell
cd "C:\Users\markussass\OneDrive - StratHost Office 365\Documents\lekker-find\agency-scout"
python -c "from services.outreach import ingest_default_leads; print(ingest_default_leads())"
```

### Error: "Gmail OAuth failed"
**Fix**: Download `credentials.json` from Google Cloud Console (see "Enable Gmail Sending" above)

### Draft looks generic/bad
**Solution 1**: Click "Regenerate" (tries Gemini again)  
**Solution 2**: Click "Edit" and hand-tune the copy  
**Solution 3**: Click "Archive" and move to next candidate

### Scheduler not running
**Check**: Terminal should show `Daily draft scheduler started` on startup  
**Force run**: Dashboard → Click "Generate 5 Drafts" button manually

---

## 📈 Next Steps (Once Working)

### Week 1: Test & Monitor
- Send 5 emails per day
- Track opens/replies manually
- Suppress uninterested leads
- Adjust messaging if needed

### Week 2: Scale Discovery
- Enable Maps API billing
- Run "New Scan" for more leads
- Try "Franschhoek coffee shops", "Stellenbosch restaurants"
- Review new candidates in dashboard

### Week 3: Optimize
- A/B test subject lines
- Track which "issues" get best reply rate
- Adjust lead scoring thresholds
- Add custom tags for segmentation

### Month 2+: Automate Reply Tracking
- Forward replies to webhook
- Auto-mark "Replied" status
- Track conversion rate
- Export metrics to CSV

---

## 💡 Pro Tips

1. **Best time to send**: 9 AM is ideal (breakfast coffee check)
2. **Edit before approve**: Personalizing 1-2 sentences boosts replies 3x
3. **Suppress aggressively**: Better to skip 10 bad leads than annoy 1 person
4. **Monitor spam complaints**: Check Google Workspace Admin weekly
5. **Warm up slowly**: Stay at 5/day for first month, then 10/day

---

## 📞 Need Help?

### Check Logs
```powershell
# Watch real-time logs
python -m uvicorn app:app --reload --log-level debug
```

### Export Current State
Dashboard → Export leads as CSV (top-right button)

### Reset Database (Nuclear Option)
```powershell
rm data\masa.sqlite3
python scripts\seed_masa.py
```

---

## ✨ You're Ready!

**Your 3-step daily routine:**

1. **09:00 AM**: System auto-generates 5 drafts
2. **09:05 AM**: You review + approve in dashboard (5 min)
3. **Rest of day**: System waits for next morning

That's it. Set it up once, run it forever.
