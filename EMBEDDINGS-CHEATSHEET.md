# Embeddings Cheat Sheet

> Quick reference for working with OpenAI embeddings in recommendation systems.

---

## Model Selection

| Model | Dimensions | Cost | Best For |
|-------|------------|------|----------|
| `text-embedding-3-small` | 256-1536 | $0.02/1M tokens | Production, high-volume |
| `text-embedding-3-large` | 256-3072 | $0.13/1M tokens | Maximum accuracy |
| `text-embedding-ada-002` | 1536 | $0.10/1M tokens | Legacy (avoid) |

**We use:** `text-embedding-3-small` @ 256 dimensions (API-level truncation)

---

## The Golden Rule

```
OpenAI embeddings are L2-normalized (length = 1.0)
→ Dot product = Cosine similarity (no division needed)
→ BUT: Any vector operation breaks this!
```

**After these operations, ALWAYS re-normalize:**
- Mean pooling (averaging vectors)
- Vector subtraction
- Vector addition
- Weighted combinations

---

## Normalization Formula

```javascript
function normalizeVector(v) {
    const magnitude = Math.sqrt(v.reduce((sum, x) => sum + x * x, 0));
    if (magnitude === 0) return v;
    return v.map(x => x / magnitude);
}
```

**Usage:**
```javascript
// WRONG
let userVibe = meanPool(embeddings);

// CORRECT
let userVibe = normalizeVector(meanPool(embeddings));
```

---

## Common Operations

### Combine Multiple Preferences (Mean Pool)
```javascript
const combined = normalizeVector(meanPool([emb1, emb2, emb3]));
```

### Subtract Dislikes (Preference Refinement)
```javascript
const liked = normalizeVector(meanPool(likedEmbeddings));
const disliked = normalizeVector(meanPool(dislikedEmbeddings));
const final = normalizeVector(subtractVectors(liked, disliked));
```

### Calculate Similarity
```javascript
// Only works if BOTH vectors are normalized!
const similarity = dotProduct(queryVector, venueVector);
```

---

## Similarity Score Ranges

| Raw Cosine | Interpretation |
|------------|----------------|
| 0.85 - 1.00 | Excellent match |
| 0.60 - 0.85 | Strong match |
| 0.40 - 0.60 | Moderate match |
| 0.15 - 0.40 | Weak match |
| < 0.15 | Poor/unrelated |

---

## Converting to Percentages

```javascript
// Power curve emphasizes high matches
const scaledSim = Math.pow(Math.max(0, similarity), 0.7);

// Map to user-friendly range (40% - 88% base)
const basePercent = 40 + (scaledSim * 48);

// Add bonuses for keywords, ratings, etc.
const finalPercent = Math.min(98, basePercent + bonuses);
```

---

## Hybrid Search Strategy

Pure semantic matching isn't enough. Combine:

| Signal | Weight | Purpose |
|--------|--------|---------|
| Cosine similarity | 70% | Semantic meaning |
| Keyword boost | +8% per match | Exact tag matches |
| Rating bonus | +1% to +4% | Quality signal |
| Avoid penalty | -200% | Hard filter |

---

## The Normalization Problem (Why It Matters)

**Problem:** Averaging unit vectors creates shorter vectors.

```
Romantic = [0.8, 0.6]    length = 1.0
Hidden   = [0.6, 0.8]    length = 1.0
Average  = [0.7, 0.7]    length = 0.99 ← Broken!
```

**Impact:**

| Scenario | Error Without Normalization |
|----------|----------------------------|
| 2 similar vibes | ~1% |
| 2 diverse vibes | ~16% |
| 5 diverse vibes | ~25% |
| Likes + Avoids | ~30% |

**Solution:** Always normalize after any vector operation.

---

## Quick Debugging

**Check if vector is normalized:**
```javascript
const length = Math.sqrt(v.reduce((sum, x) => sum + x * x, 0));
console.log(length); // Should be ~1.0
```

**Verify similarity range:**
- If you're getting values > 1.0 or < -1.0, vectors aren't normalized
- If all scores cluster around 0.5, check your embedding source

---

## API Best Practices

```javascript
// Use dimensions parameter for API-level truncation
const response = await openai.embeddings.create({
    model: "text-embedding-3-small",
    input: text,
    dimensions: 256  // Native truncation, preserves quality
});
```

**Don't:** Manually truncate vectors after retrieval  
**Do:** Use the `dimensions` parameter in the API call

---

## Cost Optimization

- **Batch requests:** Combine multiple texts in one API call
- **Cache embeddings:** Store in JSON, only regenerate when source changes
- **Incremental updates:** Hash source text, skip unchanged items
- **Reduce dimensions:** 256d is 6× smaller than 1536d with minimal quality loss

---

## File Structure

```
/public/lekker-find-data.json    # Cached embeddings
/scripts/generate_embeddings.py   # Embedding generation
/src/utils/matcher.ts             # Similarity matching
```

---

## Remember

1. **Embeddings are arrows** — direction matters, not length
2. **Normalize after operations** — averaging/subtracting breaks unit length
3. **Dot product = cosine** — but ONLY for normalized vectors
4. **Hybrid is better** — combine semantic + keyword + quality signals
5. **Cache everything** — embeddings are expensive to generate but free to reuse
