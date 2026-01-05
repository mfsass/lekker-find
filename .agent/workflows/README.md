---
description: Quick reference for available workflows
---

# Agent Workflows

Quick reference for available workflows.

---

## `/remove-duplicates` — Remove Duplicate Venues

Removes duplicate venues from data files using embedding similarity detection.

### Quick Start

```bash
# 1. Find duplicates (view only)
node scripts/remove-duplicates.cjs --find

# 2. Preview removal
node scripts/remove-duplicates.cjs --dry-run

# 3. Execute removal
node scripts/remove-duplicates.cjs
```

### How It Works

- Uses **cosine similarity** on venue embeddings (92% threshold)
- Combines with a **manual list** for edge cases (e.g., same location, different category)
- Removes from both `lekker-find-data.json` and CSV
- Preserves embeddings — no API calls needed

### Adding Manual Duplicates

Edit `scripts/remove-duplicates.cjs`:

```javascript
const MANUAL_DUPLICATES = [
  'Venue Name To Remove', // Duplicate of "Other Venue"
];
```

See [full workflow →](./remove-duplicates.md)

---

*More workflows will be documented here as they're created.*
