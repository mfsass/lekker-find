---
trigger: model_decision
description: When optimising SEO and LLM traffic and detection to improve search results and increase traffic to site, use were applicable.
---

# Antigravity Rules — UI/UX Design Specialist

> Pixel-perfect, accessible, delightful. Every class matters.

---

## Design Tokens

### Colors

```css
:root {
  --primary: 174 72% 40%;           /* Ocean teal */
  --primary-foreground: 0 0% 100%;
  --secondary: 24 95% 53%;          /* Sunset orange */
  --secondary-foreground: 0 0% 100%;
  --background: 40 20% 98%;         /* Warm white */
  --foreground: 220 20% 14%;        /* Warm dark */
  --muted: 40 15% 92%;
  --muted-foreground: 220 10% 40%;
  --border: 40 15% 88%;
  --ring: 174 72% 40%;
  --radius: 0.75rem;
}
```

**Rules:**
- Never pure black (`#000`) or pure white (`#fff`)
- Primary: one action color, used sparingly
- Always use tokens: `bg-primary`, never `bg-teal-500`

### Typography

```css
--font-sans: 'Inter', system-ui, sans-serif;

/* Scale */
--text-xs: 0.75rem;    /* Labels */
--text-sm: 0.875rem;   /* Secondary */
--text-base: 1rem;     /* Body */
--text-lg: 1.125rem;   /* Lead */
--text-xl: 1.25rem;    /* Card titles */
--text-2xl: 1.5rem;    /* Section headers */
--text-3xl: 2rem;      /* Page titles */
--text-4xl: 2.5rem;    /* Hero mobile */
--text-5xl: 3.5rem;    /* Hero desktop */
```

| Level | Classes |
|:------|:--------|
| Hero | `text-4xl md:text-5xl font-bold tracking-tight` |
| H1 | `text-3xl font-bold tracking-tight` |
| H2 | `text-2xl font-semibold` |
| H3 | `text-xl font-semibold` |
| Body | `text-base leading-relaxed` |
| Caption | `text-sm text-muted-foreground` |

### Spacing

4px grid. Use Tailwind scale:

| Value | Use |
|:------|:----|
| `p-4` (16px) | Card padding mobile |
| `p-6` (24px) | Card padding desktop |
| `gap-2` (8px) | Inline elements |
| `gap-4` (16px) | Stack elements |
| `py-12` (48px) | Section mobile |
| `py-16` (64px) | Section desktop |

### Radius

| Element | Class |
|:--------|:------|
| Buttons | `rounded-full` |
| Cards | `rounded-xl` |
| Inputs | `rounded-lg` |
| Tags | `rounded-full` |

---

## Components

### Primary Button

```tsx
<button className="
  bg-primary text-primary-foreground
  px-6 py-3 rounded-full
  font-semibold text-base
  shadow-lg shadow-primary/25
  hover:shadow-xl hover:-translate-y-0.5
  active:translate-y-0 active:shadow-md
  transition-all duration-200
">
  ✨ Find Something
</button>
```

### Secondary Button

```tsx
<button className="
  bg-white text-foreground
  border-2 border-border
  px-6 py-3 rounded-full
  font-semibold
  hover:border-primary hover:text-primary
  transition-colors duration-200
">
  Surprise Me
</button>
```

### Ghost Button

```tsx
<button className="
  text-muted-foreground
  px-4 py-2 rounded-lg
  hover:bg-muted hover:text-foreground
  transition-colors duration-150
">
  Skip
</button>
```

**Button Rules:**
- One primary per screen
- Min touch target: 44×44px
- Hover: lift + shadow
- Active: press down

### Card

```tsx
<div className="
  bg-white rounded-xl
  shadow-lg shadow-black/5
  overflow-hidden
  hover:shadow-xl hover:-translate-y-1
  transition-all duration-300
">
  <div className="aspect-[4/3] relative overflow-hidden">
    <img className="w-full h-full object-cover" alt="..." />
    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent" />
    <span className="
      absolute top-3 right-3
      bg-white/90 backdrop-blur-sm
      px-3 py-1 rounded-full
      text-sm font-semibold text-primary
    ">
      92% match
    </span>
  </div>
  <div className="p-4">
    <h3 className="text-lg font-semibold">Venue Name</h3>
    <p className="text-sm text-muted-foreground mt-1">Food • RR</p>
  </div>
</div>
```

**Card Rules:**
- Always `overflow-hidden` + `rounded-xl`
- Image aspect: `4:3`
- Gradient overlay on images with text
- Shadow subtle default, pronounced on hover

### Tag (Unselected)

```tsx
<button className="
  px-4 py-2 rounded-full
  bg-muted text-muted-foreground
  text-sm font-medium
  hover:bg-accent hover:text-accent-foreground
  transition-colors duration-150
">
  Romantic
</button>
```

### Tag (Selected)

```tsx
<button className="
  px-4 py-2 rounded-full
  bg-primary text-primary-foreground
  text-sm font-medium
  ring-2 ring-primary ring-offset-2
">
  Romantic ✓
</button>
```

### Input

```tsx
<input className="
  w-full px-4 py-3
  bg-background border-2 border-border rounded-lg
  text-foreground placeholder:text-muted-foreground
  focus:border-primary focus:ring-2 focus:ring-primary/20
  transition-colors duration-200
" />
```

---

## Motion

### Timing

| Type | Duration | Use |
|:-----|:---------|:----|
| Micro | `150ms` | Hover, focus |
| State | `200ms` | Toggle, expand |
| Transition | `300ms` | Page, modal |
| Complex | `500ms` | Flip, shuffle |

### Framer Motion

```tsx
// Fade up
const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: 'easeOut' }
};

// Stagger children
const stagger = {
  animate: { transition: { staggerChildren: 0.08 } }
};

// Press
const tap = { whileTap: { scale: 0.97 } };

// Swipe
const swipe = {
  drag: 'x',
  dragConstraints: { left: 0, right: 0 },
  dragElastic: 0.7,
};
```

### Reduced Motion

```tsx
const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const duration = prefersReduced ? 0 : 0.3;
```

---

## Layout

### Container

```tsx
<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
```

### Grid

```tsx
<div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
```

### Sticky Header

```tsx
<header className="
  sticky top-0 z-50
  bg-background/80 backdrop-blur-lg
  border-b border-border
">
```

### Sticky Bottom CTA

```tsx
<div className="
  fixed bottom-0 inset-x-0 z-40
  bg-gradient-to-t from-background via-background to-transparent
  px-4 pb-6 pt-8
">
  <button className="w-full">Find Something</button>
</div>
```

---

## States

### Skeleton

```tsx
<div className="animate-pulse">
  <div className="aspect-[4/3] bg-muted rounded-xl" />
  <div className="mt-4 space-y-3">
    <div className="h-5 bg-muted rounded w-3/4" />
    <div className="h-4 bg-muted rounded w-1/2" />
  </div>
</div>
```

### Empty State

```tsx
<div className="text-center py-16 px-6">
  <div className="text-6xl mb-4">🏔️</div>
  <h2 className="text-xl font-semibold mb-2">No spots match</h2>
  <p className="text-muted-foreground mb-6">Try different vibes</p>
  <button>Adjust Filters</button>
</div>
```

### Error State

```tsx
<div className="text-center py-16 px-6">
  <div className="text-6xl mb-4">😬</div>
  <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
  <p className="text-muted-foreground mb-6">Try again?</p>
  <button>Retry</button>
</div>
```

---

## Accessibility

### Focus

```tsx
className="
  focus:outline-none
  focus-visible:ring-2
  focus-visible:ring-ring
  focus-visible:ring-offset-2
"
```

### Touch Targets

- Minimum: 44×44px
- Add padding, not just visual size

### Contrast

- Text on background: 4.5:1 minimum
- Use gradient overlays on images

### Screen Reader

```tsx
<button aria-label="Next venue">→</button>
<div aria-live="polite">20 results</div>
<a className="sr-only focus:not-sr-only">Skip to content</a>
```

---

## Responsive

| Breakpoint | Width |
|:-----------|:------|
| Default | 0-639px (mobile) |
| `sm` | 640px+ |
| `md` | 768px+ |
| `lg` | 1024px+ |

### Patterns

```tsx
// Typography
<h1 className="text-4xl md:text-5xl">

// Layout
<div className="flex flex-col md:flex-row">

// Spacing
<section className="py-12 md:py-16">

// Grid
<div className="grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
```

---

## Loading Messages

```typescript
const messages = [
  "Asking the car guard for advice...",
  "Checking the load shedding schedule...",
  "Putting another chop on the braai...",
  "Consulting the penguins at Boulders...",
];
```

Rotate every 2-3s with fade.

---

## Checklist

- [ ] Works at 320px width
- [ ] Touch targets ≥ 44px
- [ ] Contrast AA minimum
- [ ] Focus states visible
- [ ] Reduced motion respected
- [ ] Skeleton loaders exist
- [ ] Empty/error states designed
- [ ] No layout shift
- [ ] 60fps animations

---

## Anti-Patterns

| ❌ | ✅ |
|:---|:---|
| `bg-white` | `bg-background` |
| `text-black` | `text-foreground` |
| `#000` / `#fff` | Warm neutrals |
| `rounded-md` on cards | `rounded-xl` |
| `border` (1px) | `border-2` or shadow |
| Instant changes | 150-300ms transition |
| Generic spinner | Skeleton + context |
| Tiny targets | 44px minimum |
| Text on busy images | Gradient overlay |