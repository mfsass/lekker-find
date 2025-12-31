# Lekker Find SEO & LLM Discovery Plan (2026)

## Icon Diagnosis & Fix
- **Issue:** Google SERP showed generic globe icon. Likely cause: Google favicon crawler not picking a high-resolution PNG at root or missing explicit 192/512 links.
- **Fix applied:** Added explicit 192x192 and 512x512 `rel="icon"` entries in `index.html` alongside `favicon.ico` and Apple touch icon. All assets live at site root (`/favicon.ico`, `/favicon-32x32.png`, `/favicon-16x16.png`, `/android-chrome-192x192.png`, `/android-chrome-512x512.png`) and are crawlable (robots allows all).
- **Follow-up:** In Search Console, request re-crawl of the homepage and check the **Favicon** report. Clear CDN/cache so Googlebot can fetch the new links.

## Proposed Meta Updates (implemented)
- **Title:** `Find Things to Do in Cape Town | Lekker Find | 320+ AI-Matched Spots`
- **Description:** `Find things to do in Cape Town with Lekker Find. 320+ hidden gems, local events, and date ideas matched to your vibe by AI. Built for 2026 trips, weekends, and locals.`
- **OG/Twitter:** Mirrors the above, focused on 2026 trips/local weekends and AI matching.
- **Keywords:** `find things to do in Cape Town, Cape Town events 2026, things to do Cape Town 2026, what to do in Cape Town, hidden gems Cape Town, Cape Town date ideas, AI trip planner South Africa, Cape Town weekend plans, local Cape Town recommendations, where to find activities Cape Town`
- **Structured Data:** WebApplication description updated to 320+ spots and 2026 travel/weekend framing.

## Priority Queries for 2026 (SA market)
- Things to do in Cape Town 2026
- Cape Town events 2026 / this weekend
- What to do in Cape Town / where to find activities Cape Town
- Hidden gems Cape Town / off-the-path Cape Town
- Cape Town date ideas / romantic things to do Cape Town
- AI trip planner South Africa / AI itinerary Cape Town
- Family-friendly things to do Cape Town / free things to do Cape Town

## Competitive Observations (surgical)
- Top-ranking local guides surface **fresh events** and **seasonal keywords** (summer 2025/2026, festive, school holidays).
- Sites with clear **city-localised titles** (“Find things to do in Cape Town”) and **large-image OG** snippets win CTR.
- Rich **favicon/webmanifest** plus **fast LCP** correlate with presence of branded icon on SERP.
- Successful competitors expose **LLM-readable text blocks** (plain bullet lists, minimal JS gating) and include **FAQ schema**.

## Actionable Engineering Checklist
- [x] Expose high-res favicons (192/512) and keep `favicon.ico` at root.
- [x] Update title/description/OG/Twitter to “Find things to do…” with 2026 intents.
- [x] Refresh JSON-LD with 320+ spots and 2026 framing.
- [ ] Add FAQPage schema targeting “things to do in Cape Town 2026”, “Cape Town events this weekend”, “AI trip planner South Africa”.
- [ ] Ensure `og:image` is lightweight (≤1200x630, <150KB) and hosted on root domain; run URL through Facebook/Twitter/LinkedIn debuggers.
- [ ] Keep a static, crawlable text block on landing with the priority queries above (works for both SEO and LLMs).
- [ ] Submit updated sitemap & request recrawl in Google Search Console; verify **Favicon** status after cache clear.
- [ ] Track branded CTR for “Lekker Find” and generic CTR for “things to do in Cape Town 2026” in GSC.

## Content Schedule Recommendations
- Weekly: short updates for “events in Cape Town this weekend”.
- Monthly: seasonal pages (summer 2026, winter rainy-day ideas, public holidays).
- Evergreen: “hidden gems Cape Town”, “free things to do Cape Town”, “AI trip planner South Africa”.
- Create concise FAQ entries and expose in markup/HTML for LLM retrieval.
