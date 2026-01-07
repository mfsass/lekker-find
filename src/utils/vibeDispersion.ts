/**
 * Vibe Dispersion - Embedding-based diversity selection
 * 
 * Uses pre-computed tag embeddings to select vibes with maximum semantic
 * dispersion, ensuring diverse options that help users clearly express preferences.
 * 
 * Algorithm: Greedy farthest-first selection using cosine distance.
 */

/**
 * Calculate cosine similarity between two vectors.
 * Higher = more similar (0 to 1 range for normalized vectors)
 */
function cosineSimilarity(a: number[], b: number[]): number {
    if (!a || !b || a.length !== b.length) return 0;

    let dotProduct = 0;
    for (let i = 0; i < a.length; i++) {
        dotProduct += a[i] * b[i];
    }

    return dotProduct;
}

/**
 * Calculate cosine distance (inverse of similarity).
 * Higher = more different (0 to 2 range, typically 0-1 for normalized vectors)
 */
function cosineDistance(a: number[], b: number[]): number {
    return 1 - cosineSimilarity(a, b);
}

/**
 * Select vibes with maximum semantic dispersion using greedy farthest-first.
 * 
 * This ensures each vibe is as different as possible from already selected ones,
 * giving users clear, distinct choices.
 * 
 * @param candidates - List of vibe tags to choose from
 * @param embeddings - Pre-computed tag embeddings
 * @param count - Number of vibes to select
 * @param avoidList - Vibes to explicitly exclude (e.g., already shown)
 * @returns Array of diverse vibe tags
 */
export function selectDiverseVibes(
    candidates: string[],
    embeddings: Record<string, number[]>,
    count: number,
    avoidList: string[] = []
): string[] {
    // Filter out avoided vibes
    const available = candidates.filter(v => !avoidList.includes(v));

    if (available.length === 0) {
        console.warn('No available vibes after filtering');
        return [];
    }

    if (available.length <= count) {
        return available;
    }

    const selected: string[] = [];

    // Step 1: Pick random starting vibe
    const firstVibe = available[Math.floor(Math.random() * available.length)];
    selected.push(firstVibe);

    // Step 2: Greedily select vibes that maximize distance to all selected
    while (selected.length < count) {
        let maxMinDistance = -1;
        let bestVibe = '';

        for (const candidate of available) {
            if (selected.includes(candidate)) continue;
            if (!embeddings[candidate]) continue;

            // Calculate minimum distance to any selected vibe
            let minDistance = Infinity;
            for (const selectedVibe of selected) {
                if (!embeddings[selectedVibe]) continue;
                const dist = cosineDistance(
                    embeddings[candidate],
                    embeddings[selectedVibe]
                );
                minDistance = Math.min(minDistance, dist);
            }

            // Pick candidate whose closest selected vibe is still far away
            if (minDistance > maxMinDistance) {
                maxMinDistance = minDistance;
                bestVibe = candidate;
            }
        }

        if (bestVibe) {
            selected.push(bestVibe);
        } else {
            // Fallback: just pick randomly if algorithm fails
            const remaining = available.filter(v => !selected.includes(v));
            if (remaining.length > 0) {
                selected.push(remaining[0]);
            } else {
                break;
            }
        }
    }

    return selected;
}

/**
 * Select vibes that are semantically opposite/different from a given list.
 * Useful for "disliked vibes" - we want options that are clearly different
 * from what the user liked.
 * 
 * @param likedVibes - Vibes the user selected as liked
 * @param candidates - Pool of all possible vibes
 * @param embeddings - Pre-computed tag embeddings
 * @param count - Number of opposite vibes to select
 * @returns Array of vibes maximally distant from liked vibes
 */
export function selectOppositeVibes(
    likedVibes: string[],
    candidates: string[],
    embeddings: Record<string, number[]>,
    count: number
): string[] {
    if (likedVibes.length === 0) {
        // If no liked vibes, just use diverse selection
        return selectDiverseVibes(candidates, embeddings, count, []);
    }

    // Calculate average embedding of liked vibes
    const likedEmbeddings = likedVibes
        .map(v => embeddings[v])
        .filter((emb): emb is number[] => emb !== undefined);

    if (likedEmbeddings.length === 0) {
        return selectDiverseVibes(candidates, embeddings, count, []);
    }

    const avgLikedEmbedding = normalizeVector(meanPool(likedEmbeddings));

    // Score all candidates by distance to liked vibes
    const scored = candidates
        .filter(v => !likedVibes.includes(v)) // Exclude already liked
        .filter(v => embeddings[v] !== undefined)
        .map(vibe => ({
            vibe,
            distance: cosineDistance(embeddings[vibe], avgLikedEmbedding)
        }))
        .sort((a, b) => b.distance - a.distance); // Furthest first

    // Take top N distant vibes, then apply dispersion selection among them
    const topOpposites = scored.slice(0, Math.min(count * 3, scored.length)).map(s => s.vibe);

    // Apply diversity selection within these opposites
    return selectDiverseVibes(topOpposites, embeddings, count, likedVibes);
}

/**
 * Mean pool multiple embeddings into single vector.
 */
function meanPool(embeddings: number[][]): number[] {
    if (embeddings.length === 0) {
        throw new Error('Cannot pool empty embeddings');
    }

    if (embeddings.length === 1) {
        return embeddings[0];
    }

    const dimensions = embeddings[0].length;
    const mean = new Array(dimensions).fill(0);

    for (const embedding of embeddings) {
        for (let i = 0; i < dimensions; i++) {
            mean[i] += embedding[i];
        }
    }

    for (let i = 0; i < dimensions; i++) {
        mean[i] /= embeddings.length;
    }

    return mean;
}

/**
 * L2 normalize a vector to unit length.
 * Required after mean pooling to maintain dot product = cosine similarity.
 */
function normalizeVector(v: number[]): number[] {
    if (!v || v.length === 0) return v;

    let magnitude = 0;
    for (let i = 0; i < v.length; i++) {
        magnitude += v[i] * v[i];
    }
    magnitude = Math.sqrt(magnitude);

    if (magnitude === 0) return v;

    const normalized = new Array(v.length);
    for (let i = 0; i < v.length; i++) {
        normalized[i] = v[i] / magnitude;
    }

    return normalized;
}

export default {
    selectDiverseVibes,
    selectOppositeVibes
};
