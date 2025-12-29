# Antigravity Agent Rules — Lekker Find

> Optimized for Gemini 3 Pro. Direct instructions, consistent structure, zero fluff.

---

## Identity

You are an AI coding agent building **Lekker Find** — a vibe-based recommendation engine for Cape Town. You collaborate through planning, execution, and verification phases.

---

## Project Context

### What We're Building

A client-side React app that matches users to 261 curated Cape Town spots based on mood, budget, and persona. No backend. Works offline.

### Core Principles

| Principle | Implementation |
|:----------|:---------------|
| Vibe-first | Match feelings via embeddings, not keyword search |
| Quality over quantity | 261 vetted spots, no filler |
| Instant & offline | All logic client-side, static JSON data |
| Local soul | Voice like a Capetonian, real prices, actual context |

### Tech Stack

- **Framework:** React 18+ with Vite
- **Language:** TypeScript (strict)
- **Styling:** Tailwind CSS only
- **Animations:** Framer Motion
- **Data:** Static JSON with pre-computed embeddings
- **Hosting:** Vercel (static)

### Constraints

- Mobile-first (90%+ mobile traffic expected)
- Bundle < 1MB total
- Time to first result < 500ms
- Offline-capable after initial load
- No backend, no database, no API calls at runtime

---

## Workflow Modes

### Planning Mode

Use for multi-file changes or new features:

1. Create implementation plan artifact
2. List files to create/modify
3. Define acceptance criteria
4. Wait for approval before executing

### Execution Mode

Use after approval or for simple tasks:

1. Make incremental changes
2. Verify each step compiles
3. Test via browser subagent when applicable

### Fast Mode

Use for quick fixes: typos, single-file edits, minor styling.

---

## Code Principles

### 1. Functional Components Only

```tsx
// ✅ Correct
const VenueCard: React.FC<VenueCardProps> = ({ venue }) => { ... }

// ❌ Never
class VenueCard extends React.Component { ... }
```

### 2. Components Outside Parent Scope

Define helper components **outside** the parent to prevent re-mounting.

```tsx
// ❌ Causes input focus loss, re-renders
function ParentComponent() {
  const ChildInput = () => <input value={text} onChange={...} />;
  return <ChildInput />;
}

// ✅ Stable component identity
interface ChildInputProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const ChildInput: React.FC<ChildInputProps> = ({ value, onChange }) => (
  <input value={value} onChange={onChange} />
);

function ParentComponent() {
  const [text, setText] = useState('');
  return <ChildInput value={text} onChange={(e) => setText(e.target.value)} />;
}
```

### 3. Avoid useEffect Infinite Loops

```tsx
// ❌ Infinite loop: callback recreates on every render
const fetchData = useCallback(() => {
  setCount(count + 1); // depends on count
}, [count]);

useEffect(() => {
  fetchData();
}, [fetchData]); // triggers on every count change

// ✅ Functional update, runs once
useEffect(() => {
  setCount(prev => prev + 1);
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []); // empty deps = mount only
```

### 4. Generics in TSX Need Trailing Comma

```tsx
// ✅ Correct (trailing comma disambiguates from JSX)
const processData = <T,>(data: T): T => { ... };

// ❌ Parser confusion
const processData = <T>(data: T): T => { ... };
```

### 5. Named Imports Only

```tsx
// ✅ Correct
import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

// ❌ Never destructure from namespace
const { motion } = FramerMotion;
```

---

## Styling Rules

### Tailwind Only

No CSS files, no styled-components, no inline `style` attributes.

### Design System Structure

```
index.css (tokens) → tailwind.config.ts (theme) → components (variants)
```

### Token Definition

```css
/* index.css */
:root {
  --primary: 210 100% 50%;
  --secondary: 160 84% 39%;
  --background: 0 0% 100%;
  --foreground: 222 47% 11%;
  --muted: 210 40% 96%;
  --accent: 210 40% 96%;
  --destructive: 0 84% 60%;
  --border: 214 32% 91%;
  --radius: 0.5rem;
}
```

### Forbidden Patterns

```tsx
// ❌ Never hardcode colors
<div className="bg-white text-black">
<button className="bg-blue-500">

// ✅ Always use tokens
<div className="bg-background text-foreground">
<button className="bg-primary text-primary-foreground">
```

### Mobile-First

```tsx
// ✅ Base styles for mobile, enhance for larger screens
<div className="px-4 md:px-8 lg:px-12">
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
```

---

## File Organization

```
src/
├── components/
│   ├── ui/              # Primitives (Button, Card, Tag)
│   ├── landing/         # Hero, CTAs
│   ├── questions/       # Persona, Budget, Vibe selectors
│   └── results/         # VenueCard, CardDeck
├── hooks/
│   ├── useVenueSearch.ts
│   └── useEmbeddings.ts
├── lib/
│   ├── matching.ts      # Cosine similarity, ranking
│   ├── filters.ts       # Budget, persona filters
│   └── utils.ts
├── data/
│   └── venues.json      # Static dataset with embeddings
├── types/
│   └── venue.ts
├── App.tsx
└── main.tsx
```

### Naming Conventions

- Components: `PascalCase.tsx`
- Utilities: `camelCase.ts`
- Types: `camelCase.ts` with `PascalCase` exports

### File Size Limits

- Components: < 150 lines
- Utilities: < 100 lines
- Split when exceeding

---

## Data Types

```typescript
interface Venue {
  id: string;
  name: string;
  category: 'Food' | 'Activity' | 'Nature' | 'Culture' | 'Drink';
  vibe: string[];
  description: string;
  price: number;
  price_tier: 'Free' | 'R' | 'RR' | 'RRR';
  tourist_level: number; // 1-10
  embedding: number[];   // 256-dim vector
  image: string;         // local path
}

type Persona = 'local' | 'explorer' | 'tourist';

interface SearchParams {
  persona: Persona;
  budget: ('Free' | 'R' | 'RR' | 'RRR')[];
  vibes: string[];
}
```

---

## Algorithm Reference

### Personalize Flow

1. **Filter** — Remove mismatched budget/persona
2. **Match** — Average selected vibe vectors → cosine similarity
3. **Rank** — Sort by score, apply persona boost, return top 20

### Surprise Me Flow

1. Shuffle all venues
2. Sample 10 with diversity constraints
3. Return random order

### Edge Cases

| Scenario | Behavior |
|:---------|:---------|
| Zero vibes selected | Skip vector matching, return filtered by default |
| < 3 results | Relax budget filter, show explanatory toast |
| Conflicting vibes | Vector averaging finds hybrids |

---

## UI Components Needed

| Component | Purpose |
|:----------|:--------|
| `Hero` | Headline, subhead, dual CTAs |
| `QuestionFlow` | 3-step stepper (Persona → Budget → Vibes) |
| `TagCloud` | Multi-select vibe pills |
| `VenueCard` | Flip animation, front (image/name/score) + back (details) |
| `CardDeck` | Swipeable stack with gesture support |
| `LoadingScreen` | Random Cape Town quips |

### Loading Messages (Random)

```typescript
const loadingMessages = [
  "Asking the car guard for advice...",
  "Checking the load shedding schedule...",
  "Putting another chop on the braai...",
  "Waiting for the mist to clear...",
];
```

---

## Accessibility Checklist

- [ ] Keyboard navigation (arrows, enter, escape)
- [ ] All images have descriptive alt: `{name} - {category}`
- [ ] Color contrast WCAG AA minimum
- [ ] Swipe gestures have button alternatives
- [ ] Focus states visible on all interactives
- [ ] Reduced motion preference respected

---

## SEO Defaults

Apply to `index.html`:

```html
<title>Lekker Find — Discover Things to Do in Cape Town</title>
<meta name="description" content="Find your next thing to do in Cape Town. No ads. No sign-up. Free, personal, instant. AI-matched to your vibe.">
<meta property="og:title" content="Lekker Find — Discover Something Lekker">
<meta property="og:description" content="260 hand-picked Cape Town spots. AI-matched to your vibe. Free.">
```

---

## Tool Usage

### Cardinal Rules

1. **Check context first** — Never re-read files already provided
2. **Batch operations** — Parallel reads/writes when independent
3. **Verify before write** — Ensure file is loaded before editing
4. **Prefer search-replace** — Over full file rewrites

### Tool Selection

| Task | Tool |
|:-----|:-----|
| Read file | `view_file` |
| Edit file | `search_replace` |
| Create file | `write_file` |
| Run commands | `run_command` |
| Debug UI | `browser_subagent` |
| Find patterns | `codebase_search` |

---

## Communication Style

### Response Format

```
[Brief action statement]

[Code/changes]

[One-line summary]
```

### Conciseness

| Context | Length |
|:--------|:-------|
| Quick fix | 1-2 sentences |
| Feature | 3-5 sentences |
| Architecture | As needed |

### Formatting

- GitHub-style markdown
- Code blocks with language tags
- Backticks for file/function names
- No emojis

---

## Quality Checklist

Before completing any task:

- [ ] Code compiles (`npm run build` passes)
- [ ] **Check `@current_problems` metadata tag** — Fix any reported lint/compile errors
- [ ] Design tokens used (no hardcoded colors)
- [ ] Components < 150 lines
- [ ] Mobile-first responsive
- [ ] TypeScript strict mode satisfied
- [ ] Changes match user's actual request

---

## Anti-Patterns

| ❌ Avoid | ✅ Instead |
|:--------|:----------|
| Reading context files again | Use provided context |
| Sequential tool calls | Batch operations |
| Long explanations | Concise summaries |
| Hardcoded styles | Design system tokens |
| Monolithic components | Small, focused files |
| Class components | Functional + hooks |
| CSS files | Tailwind only |
| `style` attribute | Tailwind classes |
| useEffect with callback deps | Empty deps + functional updates |

---

## Project Phases

### Phase 1: Data Pipeline ✓
Python script: CSV → embeddings → JSON

### Phase 2: Core App (Current)
- Landing page with Hero
- Question flow (3 steps)
- Matching algorithm
- Result cards with flip animation

### Phase 3: Polish
- PWA setup
- Loading states
- Analytics integration
- Lighthouse > 90

---

## Out of Scope (v1.0)

- User accounts
- Saved favorites
- User submissions
- Reviews/ratings
- Live weather
- Social sharing
- Push notifications
