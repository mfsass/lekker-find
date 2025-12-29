# Lekker Find — Product Specification

**Your local plug for Cape Town.**

| | |
|---|---|
| Domain | `lekker-find.co.za` |
| Version | 1.0 |
| Status | Ready for Build |

---

## 1. What Is This?

Lekker Find is a vibe-based recommendation engine for Cape Town. It helps users decide what to do in under 60 seconds.

**It is not** a directory, a review site, or a search engine. It's a curated deck of 261 hand-picked spots matched to your mood, budget, and whether you're a local or visitor.

### Why It Exists

- Google Maps shows 5,000 "average" results
- TripAdvisor sends locals to tourist traps
- Most apps understand "Pizza" but not "I want something secret and romantic"

### Core Principles

| Principle | What It Means |
|-----------|---------------|
| **Vibe-first** | Matches feelings, not keywords. "Swimming" is a mood, not a category. |
| **Quality over quantity** | 261 spots, every one vetted. No filler. |
| **Instant & offline** | All logic runs client-side. Works with zero signal. |
| **Local soul** | Speaks like a Capetonian. Jokes about load shedding. Gives actual prices. |

---

## 2. The Data

The dataset contains **261 unique activities** across Cape Town.

### Categories (5)

| Category | Count | Share |
|----------|-------|-------|
| Food | 91 | 35% |
| Activity | 45 | 17% |
| Nature | 44 | 17% |
| Drink | 41 | 16% |
| Culture | 40 | 15% |

### Price Tiers (4)

| Tier | Count | Description |
|------|-------|-------------|
| R | 99 | Budget-friendly |
| RR | 81 | Mid-range |
| Free | 49 | No cost |
| RRR | 32 | Premium |

### Tourist Levels (1-10)

- **Levels 6-7** dominate (116 items, 44%) — popular but not over-touristed
- **Levels 1-2** are rare (13 items) — true local gems
- **Levels 8-10** represent well-known attractions (54 items)

### Key Insight

The dataset skews toward culinary and outdoor experiences, with a strong mid-tier concentration. This makes it ideal for both locals seeking variety and tourists wanting popular-but-not-clichéd spots.

---

## 3. Branding

### Voice & Tone

Friendly, local, slightly cheeky. Like a mate who knows every spot in the city.

### Hero Copy

| Element | Content |
|---------|---------|
| **Headline** | Discover something lekker. |
| **Subhead** | We built this to help you find your next thing to do in Cape Town. No ads. No sign-up. Free, personal, instant. |
| **CTA Primary** | Personalize |
| **CTA Secondary** | Surprise Me |

### Loading Screen Messages (Random)

- "Asking the car guard for advice..."
- "Checking the load shedding schedule..."
- "Putting another chop on the braai..."
- "Waiting for the mist to clear..."

### SEO Content (Embed in Footer/Meta)

```
Lekker Find — We built this to help you find your next thing to do in 
Cape Town. No ads. No sign-up. Free, personal, instant. Hidden gems, 
date spots, local favourites — matched to your vibe by AI.

Keywords: things to do in Cape Town, Cape Town hidden gems, what to do 
Cape Town, Cape Town date ideas, local Cape Town recommendations, 
Cape Town this weekend, best spots Cape Town.
```

### Meta Tags

```html
<title>Lekker Find — Discover Things to Do in Cape Town</title>
<meta name="description" content="Find your next thing to do in Cape Town. No ads. No sign-up. Free, personal, instant. AI-matched to your vibe.">
<meta property="og:title" content="Lekker Find — Discover Something Lekker">
<meta property="og:description" content="260 hand-picked Cape Town spots. AI-matched to your vibe. Free.">
```

---

## 4. How It Works

### User Flow

```
Landing Page
     ↓
┌────────────────────────────────────┐
│  "Discover something lekker."      │
│                                    │
│  [Personalize]    [Surprise Me]    │
└────────────────────────────────────┘
        ↓                   ↓
   3 Questions         Random Results
        ↓              (10 diverse picks)
  [✨ Find Something]
        ↓
   Matched Results
   (top 20 ranked)
```

### Two Paths

| Path | Entry | Flow |
|------|-------|------|
| **Personalize** | "Personalize" button | 3 questions → `[✨ Find Something]` → ranked results |
| **Surprise Me** | "Surprise Me" button | Skip questions → instant random 10 |

### The 3 Questions (Personalize Flow)

1. **Who are you?** — Local · Explorer · Tourist
2. **What's the budget?** — Free · R · RR · RRR
3. **What's the vibe?** — Multi-select tags (Romantic, Chill, Ocean, etc.)

After completing → single CTA with AI icon: `[✨ Find Something]`

### "Surprise Me" Mode

A single button that skips the selection process entirely. Returns 10 random spots with enforced variety:

- At least 2 categories represented
- Mix of price tiers
- Mix of tourist levels

This serves users who don't know what they want or just want to browse.

### Persona Modes

| Mode | Behaviour |
|------|-----------|
| **Local** | Hides tourist traps (Tourist_Level > 7) |
| **Tourist** | Boosts famous spots in ranking |
| **Explorer** | Shows everything, no filtering |

### Tag Categories

| Type | Tags |
|------|------|
| Mood | Chill · Lively · Romantic · Authentic · Unique |
| Setting | Nature · Ocean · Indoors · Views |
| Crowd | Date Night · Group Fun · Solo · Family |
| Money | Cheap Eat · Boujee |

---

## 5. Algorithm Overview

All processing is **client-side JavaScript**. No server calls for recommendations.

### Personalize Flow

1. **Filter** — Remove spots that don't match budget or persona
2. **Match** — Average selected tag vectors to create "target vibe," compare via cosine similarity
3. **Rank** — Sort by score, apply persona boost if Tourist, return top 20

### Surprise Me Flow

1. Shuffle all spots
2. Sample 10 with diversity constraints (category, price, tourist level spread)
3. Return in random order

### Edge Cases

| Scenario | Behaviour |
|----------|-----------|
| Zero tags selected | Skip vector matching, return filtered results by default sort |
| Conflicting tags (Indoors + Nature) | Vector averaging finds hybrids (aquariums, conservatories) |
| No results (< 3 matches) | Relax price filter, show toast explaining why |
| Budget + Boujee tag conflict | Budget wins — shows "classiest cheap places" |

---

## 6. Data Architecture

### Source

A curated CSV with 261 Cape Town spots containing: Name, Category, Vibe tags, Description, Price, Tourist_Level, Image_Source (real/generate).

### Build Process (Python Script — One-Time)

1. Generate text embeddings per spot using OpenAI `text-embedding-3-small`
2. Truncate to **256 dimensions** (Matryoshka optimization — 83% size reduction)
3. Pre-compute tag vectors for the 15 filter tags
4. Export as `data.json` (Structure of Arrays format)

### Updating Data

Edit CSV → Re-run Python script → Redeploy to Vercel. No live database. Embeddings are generated at build time, not runtime.

### Output

A single static JSON file (~500KB–1MB) containing all data and embeddings. Ships with the app.

---

## 7. Image Strategy

**Production app serves static images only. No live API calls. Ever.**

All image sourcing happens at build time. The deployed app contains only hard copies.

### Process

```
CSV with venues
      ↓
┌─────────────────────────────────────┐
│  For each venue:                    │
│  1. Check if image path exists      │
│  2. If yes → use it                 │
│  3. If no → generate via Gemini     │
│     → save to /public/images/{id}   │
└─────────────────────────────────────┘
      ↓
All images committed to repo
      ↓
Production app (100% static)
```

### Two Sources

| Priority | Source | When |
|----------|--------|------|
| 1 | **Real photo** | Venue website, Unsplash, Pexels — download and save locally |
| 2 | **Gemini-generated** | No suitable real photo found — generate once, save hard copy |

### Gemini Prompt Template

```
A photograph of "{name}" in Cape Town, South Africa. {description}.
Style: natural lighting, vibrant colours, travel photography aesthetic.
Landscape orientation, 16:9 aspect ratio.
```

### Cost Guardrails

| Rule | Why |
|------|-----|
| Generate at build time only | One-time cost, not per-request |
| Use free tier (Google AI Studio) | Sufficient for ~300 images |
| Save all outputs as static files | No runtime API exposure |
| Manual review before commit | Catch poor generations |
| Prefer real photos | Generate only when necessary |

### Output

All images stored at `/public/images/{venue-id}.jpg`. Production app references local paths only. Zero external dependencies at runtime.

---

## 8. Technical Approach

| Layer | Choice |
|-------|--------|
| Framework | React + Vite (TypeScript) |
| Styling | Tailwind CSS |
| Animations | Framer Motion |
| Hosting | Vercel (free tier) |
| Analytics | Vercel Analytics or Plausible |
| Backend | None — fully static |

### Key Constraints

- Mobile-first design (90%+ expected mobile traffic)
- Responsive for desktop/laptop but not the priority
- Bundle size < 1MB total
- Time to first result < 500ms
- Must work offline after initial load

### Analytics Goals

Track lightweight metrics to understand usage:

- Page views
- Card interactions (which spots get attention)
- Most-selected tags (what vibes people want)
- "Surprise Me" vs Personalize flow split
- Heatmaps (attention/scroll depth)

---

## 9. UI Components

| Component | Purpose |
|-----------|---------|
| **Landing Hero** | Headline, subhead, two CTAs: "Personalize" (→ questions) + "Surprise Me" (→ random) |
| **Question Flow** | 3 steps: Persona → Budget → Vibe tags |
| **Final CTA** | `[✨ Find Something]` with AI sparkle icon (only after questions) |
| **Tag Cloud** | Multi-select vibe pills |
| **Result Cards** | Swipeable deck with flip animation |
| **Card Front** | Image, name, match % |
| **Card Back** | Vibe tags, description, price |

---

## 10. Accessibility

Follow best practices:

- Keyboard navigation for cards (arrow keys, enter to flip/select)
- All images have descriptive alt text (`{name} - {category}`)
- Colour contrast meets WCAG AA
- Swipe gestures have button alternatives (next/prev arrows)
- Focus states visible on all interactive elements

---

## 11. Implementation Phases

### Phase 1: Data Pipeline

Build Python script to process CSV → embeddings → JSON.

**Done when:** Script produces valid `data.json` with all 261 spots and vectors.

### Phase 2: Core App

Build the UI and algorithm in React.

**Done when:** Both flows (Personalize + Surprise Me) work end-to-end with real data.

### Phase 3: Polish & Launch

Responsive design, PWA setup, loading states, analytics, deploy to Vercel.

**Done when:** Live at `lekker-find.co.za`, Lighthouse score > 90.

---

## 12. Out of Scope (v1.0)

- User accounts
- Saved favourites
- User-submitted spots *(see v1.2 — suggestion form)*
- Reviews or ratings
- Live weather integration
- Social sharing
- Push notifications

---

## Appendix: Data Schema

```typescript
interface Venue {
  id: string;
  name: string;
  category: "Food" | "Activity" | "Nature" | "Culture" | "Drink";
  vibe: string[];
  description: string;
  price: number;
  price_tier: "Free" | "R" | "RR" | "RRR";
  tourist_level: number; // 1-10
  image_source: "real" | "generate"; // For build-time image sourcing
  embedding: number[]; // 256-dim
}
```

---

## Appendix: Future Enhancements

### v1.1

| Feature | Description |
|---------|-------------|
| **Maps Integration** | "Go" button opens Google Maps search: `https://www.google.com/maps/search/{name}+Cape+Town` |

### v1.2

| Feature | Description |
|---------|-------------|
| **Suggestion Form** | "Have a suggestion?" link in footer → simple form (Spot name, Category, Why it's lekker, Your email). 30 seconds to complete. Sends to inbox via form-to-email service (Formspree/Web3Forms free tier). No backend needed. |
