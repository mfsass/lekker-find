/**
 * Lekker Find - Client-Side Matcher
 * ==================================
 * 
 * Handles all recommendation logic using pre-computed embeddings.
 * Returns venues with match percentage for Tinder-style card display.
 * 
 * Configuration (from benchmarks):
 * - Model: text-embedding-3-small @ 256d
 * - Accuracy: 100% (8/8 tests)
 * - Top match: 67%
 * - File size: ~2MB
 * 
 * Key features:
 * - Cosine similarity matching
 * - Mean pooling for multi-tag queries (max 5 tags)
 * - Threshold filtering (configurable, default 40%)
 * - Returns 1-20 results for card swiping
 */

import { useState, useEffect, useCallback } from 'react';

// ============================================================================
// TYPES
// ============================================================================

export interface Venue {
    id: string;
    name: string;
    category: string;
    tourist_level: number;
    price_tier: string;
    numerical_price: string;
    best_season: string;
    vibes: string[];
    description: string;
    embedding: number[];
    // Google Places data (optional)
    place_id?: string;
    maps_url?: string;
    image_url?: string;
    image_width?: number;
    image_height?: number;
    image_attribution?: string;
    rating?: number;  // Google Maps rating (1-5)
}

export interface VenueWithMatch extends Venue {
    matchPercentage: number;
}

export interface EmbeddingsData {
    version: string;
    model: string;
    dimensions: number;
    venues: Venue[];
    tag_embeddings: Record<string, number[]>;
    metadata: {
        total_venues: number;
        total_tags: number;
        generated_at: string;
    };
}

export interface MatchParams {
    intent?: string | null;
    touristLevel?: number | null;
    budget?: string | null;
    moods: string[];  // Max 5 selected
}

export interface MatchOptions {
    minScore?: number;    // Default: 0.4 (40%)
    maxResults?: number;  // Default: 20
}

// ============================================================================
// VECTOR MATH
// ============================================================================

/**
 * Calculate cosine similarity between two vectors.
 * OpenAI embeddings are normalized, so dot product = cosine similarity.
 */
function cosineSimilarity(a: number[], b: number[]): number {
    if (!a || !b || a.length !== b.length) {
        console.warn('Invalid vectors for similarity');
        return 0;
    }

    let dotProduct = 0;
    for (let i = 0; i < a.length; i++) {
        dotProduct += a[i] * b[i];
    }

    return dotProduct;
}

/**
 * Mean pool multiple embeddings into single vector.
 * Used when user selects 2-5 mood tags.
 */
function meanPool(embeddings: number[][]): number[] {
    if (!embeddings || embeddings.length === 0) {
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

// ============================================================================
// FILTERING
// ============================================================================

/**
 * Map budget string to price tiers
 */
function getBudgetTiers(budget: string | null | undefined): string[] {
    switch (budget) {
        case 'free':
            return ['Free'];
        case 'budget':
            return ['Free', 'R'];
        case 'moderate':
            return ['R', 'RR'];
        case 'premium':
            return ['RR', 'RRR'];
        default:
            return ['Free', 'R', 'RR', 'RRR']; // All
    }
}

/**
 * Filter venues by tourist level.
 * Lower touristLevel = more hidden/local gems.
 */
function filterByTouristLevel(venues: Venue[], touristLevel: number | null | undefined): Venue[] {
    if (touristLevel === null || touristLevel === undefined) {
        return venues;
    }

    // touristLevel 1-2 (Famous) = show tourist_level 7-10
    // touristLevel 3 (Balanced) = show all
    // touristLevel 4-5 (Local/Hidden) = hide tourist_level > 7
    if (touristLevel <= 2) {
        return venues.filter(v => v.tourist_level >= 6);
    } else if (touristLevel >= 4) {
        return venues.filter(v => v.tourist_level < 8);
    }

    return venues;
}

/**
 * Filter venues by category/intent.
 */
function filterByIntent(venues: Venue[], intent: string | null | undefined): Venue[] {
    if (!intent || intent === 'any') {
        return venues;
    }

    const categoryMap: Record<string, string[]> = {
        food: ['Food'],
        drink: ['Drink'],
        activity: ['Activity'],
        nature: ['Nature'],
        culture: ['Culture'],
    };

    const categories = categoryMap[intent];
    if (!categories) {
        return venues;
    }

    return venues.filter(v => categories.includes(v.category));
}

// ============================================================================
// MAIN MATCHER
// ============================================================================

/**
 * Find matching venues based on user selections.
 * 
 * @param params - User selections (intent, touristLevel, budget, moods)
 * @param data - Loaded embeddings data
 * @param options - Match options (threshold, limit)
 * @returns Venues sorted by match percentage (highest first)
 */
export function findMatches(
    params: MatchParams,
    data: EmbeddingsData,
    options: MatchOptions = {}
): VenueWithMatch[] {
    const { minScore = 0.4, maxResults = 20 } = options;
    const startTime = performance.now();

    console.log('🔍 Finding matches...', { params, minScore, maxResults });

    let venues = [...data.venues];

    // Phase 1: Hard filters
    venues = filterByIntent(venues, params.intent);
    console.log(`  After intent filter: ${venues.length}`);

    venues = filterByTouristLevel(venues, params.touristLevel);
    console.log(`  After tourist filter: ${venues.length}`);

    const allowedTiers = getBudgetTiers(params.budget);
    venues = venues.filter(v => allowedTiers.includes(v.price_tier));
    console.log(`  After budget filter: ${venues.length}`);

    // Phase 2: Semantic matching
    if (params.moods.length === 0) {
        // No moods selected - return shuffled results with neutral score
        const shuffled = venues.sort(() => Math.random() - 0.5);
        return shuffled.slice(0, maxResults).map(v => ({
            ...v,
            matchPercentage: 50
        }));
    }

    // Get tag embeddings for selected moods
    const moodEmbeddings = params.moods
        .slice(0, 5) // Max 5 moods
        .map(mood => data.tag_embeddings[mood])
        .filter((emb): emb is number[] => emb !== undefined);

    if (moodEmbeddings.length === 0) {
        console.warn('No valid mood embeddings found');
        return venues.slice(0, maxResults).map(v => ({ ...v, matchPercentage: 50 }));
    }

    console.log(`  Using ${moodEmbeddings.length} mood embeddings`);

    // Create user vibe vector
    const userVibe = meanPool(moodEmbeddings);

    // Step 1: Calculate raw scores with keyword boost
    const rawScored = venues.map(venue => {
        const rawScore = cosineSimilarity(userVibe, venue.embedding);

        // KEYWORD BOOST: Add bonus when venue has exact mood tag match
        const matchingVibes = params.moods.filter(mood =>
            venue.vibes.some(v => v.toLowerCase() === mood.toLowerCase())
        );
        const keywordBoost = matchingVibes.length * 0.08; // +8% per matching vibe
        const boostedScore = rawScore + keywordBoost;

        return { venue, boostedScore, matchingVibes: matchingVibes.length };
    });

    // Step 2: Find min/max for RELATIVE scaling
    const scores = rawScored.map(r => r.boostedScore);
    const highestScore = Math.max(...scores);
    const lowestScore = Math.min(...scores);
    const scoreRange = highestScore - lowestScore || 0.1; // Avoid division by zero

    // Step 3: Relative scaling - best match gets 85-95%, others scale down
    // The top score maps to ~90%, spread based on actual score distribution
    const scored = rawScored.map(({ venue, boostedScore, matchingVibes }) => {
        // Normalize to 0-1 range within this result set
        const normalized = (boostedScore - lowestScore) / scoreRange;

        // Map to display range: 55% (worst in set) to 90% (best in set)
        // Add small bonus for keyword matches (up to +5%)
        const basePercent = 55 + (normalized * 35); // 55-90%
        const keywordBonus = Math.min(5, matchingVibes * 2); // Up to 5% extra
        const finalPercent = Math.min(95, basePercent + keywordBonus);

        return {
            ...venue,
            matchPercentage: Math.round(finalPercent)
        };
    });

    // Filter by threshold and sort
    const filtered = scored
        .filter(v => v.matchPercentage >= options.minScore! * 100)
        .sort((a, b) => {
            const scoreDiff = b.matchPercentage - a.matchPercentage;

            // If scores are within 5%, prefer the one with the higher rating
            // This pushes quality venues up even if the flavor match is slightly lower
            if (Math.abs(scoreDiff) <= 5) {
                const ratingA = a.rating || 0;
                const ratingB = b.rating || 0;
                // Only if ratings differ meaningfully (e.g. > 0.1)
                if (Math.abs(ratingB - ratingA) > 0.1) {
                    return ratingB - ratingA;
                }
            }

            return scoreDiff;
        });

    const results = filtered.slice(0, maxResults);

    const duration = performance.now() - startTime;
    console.log(`✓ Found ${results.length} matches in ${duration.toFixed(1)}ms`);
    console.log(`  Score range: ${Math.round(lowestScore * 100)}-${Math.round(highestScore * 100)}% → Display: ${results[results.length - 1]?.matchPercentage}-${results[0]?.matchPercentage}%`);

    return results;
}

/**
 * Surprise Me - random diverse selection.
 */
export function surpriseMe(
    data: EmbeddingsData,
    count: number = 10
): VenueWithMatch[] {
    const shuffled = [...data.venues].sort(() => Math.random() - 0.5);

    // Ensure diversity: at least 2 categories, 2 price tiers
    const selected: Venue[] = [];
    const categories = new Set<string>();
    const tiers = new Set<string>();

    for (const venue of shuffled) {
        if (selected.length >= count) break;

        if (selected.length < count / 2) {
            if (categories.size < 2 && !categories.has(venue.category)) {
                selected.push(venue);
                categories.add(venue.category);
                tiers.add(venue.price_tier);
                continue;
            }
            if (tiers.size < 2 && !tiers.has(venue.price_tier)) {
                selected.push(venue);
                categories.add(venue.category);
                tiers.add(venue.price_tier);
                continue;
            }
        }

        selected.push(venue);
        categories.add(venue.category);
        tiers.add(venue.price_tier);
    }

    return selected.map(v => ({ ...v, matchPercentage: 0 })); // 0 = no match score for surprise
}

// ============================================================================
// REACT HOOK
// ============================================================================

interface UseRecommendationsResult {
    findMatches: (params: MatchParams, options?: MatchOptions) => VenueWithMatch[];
    surpriseMe: (count?: number) => VenueWithMatch[];
    loading: boolean;
    error: Error | null;
    ready: boolean;
}

/**
 * React hook for recommendation system.
 * 
 * @example
 * const { findMatches, loading, ready } = useRecommendations();
 * 
 * if (ready) {
 *   const results = findMatches({ moods: ['Romantic', 'Hidden'] });
 * }
 */
export function useRecommendations(): UseRecommendationsResult {
    const [data, setData] = useState<EmbeddingsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        async function loadData() {
            try {
                // @ts-ignore - 'priority' is supported in modern browsers to deprioritize large data
                // Add timestamp to bust cache as we recently changed image paths to local
                const response = await fetch(`/lekker-find-data.json?v=${Date.now()}`, { priority: 'low' });

                if (!response.ok) {
                    throw new Error(`Failed to load embeddings: ${response.status}`);
                }

                // Local images don't need crossOrigin
                // img.crossOrigin = 'anonymous';
                const json = await response.json();

                if (!json.venues || !json.tag_embeddings) {
                    throw new Error('Invalid embeddings data structure');
                }

                console.log(`✓ Loaded ${json.venues.length} venues, ${Object.keys(json.tag_embeddings).length} tags`);

                setData(json);
                setLoading(false);
            } catch (err) {
                console.error('Error loading recommendations:', err);
                setError(err instanceof Error ? err : new Error(String(err)));
                setLoading(false);
            }
        }

        // Delay fetch to prioritize LCP/FCP even more
        // User takes ~3-5s to read the landing page anyway
        const timer = setTimeout(() => {
            loadData();
        }, 3500);

        return () => clearTimeout(timer);
    }, []);

    const find = useCallback((params: MatchParams, options?: MatchOptions) => {
        if (!data) {
            console.warn('Data not loaded yet');
            return [];
        }
        return findMatches(params, data, options);
    }, [data]);

    const surprise = useCallback((count?: number) => {
        if (!data) {
            console.warn('Data not loaded yet');
            return [];
        }
        return surpriseMe(data, count);
    }, [data]);

    return {
        findMatches: find,
        surpriseMe: surprise,
        loading,
        error,
        ready: !loading && !error && data !== null
    };
}

// ============================================================================
// DEBUGGING
// ============================================================================

/**
 * Test embedding quality by checking expected relationships.
 */
export function testEmbeddings(data: EmbeddingsData): void {
    console.log('🧪 Testing embedding quality...');

    const tests = [
        { pair: ['Romantic', 'Cozy'], expect: 'high' },
        { pair: ['Lively', 'Fun'], expect: 'high' },
        { pair: ['Hidden', 'Secret'], expect: 'high' },
        { pair: ['Peaceful', 'Lively'], expect: 'low' },
        { pair: ['VIP', 'Good-value'], expect: 'low' },
    ];

    for (const test of tests) {
        const [tag1, tag2] = test.pair;
        const emb1 = data.tag_embeddings[tag1];
        const emb2 = data.tag_embeddings[tag2];

        if (!emb1 || !emb2) {
            console.warn(`  Missing: ${tag1} or ${tag2}`);
            continue;
        }

        const sim = cosineSimilarity(emb1, emb2);
        const pct = Math.round(sim * 100);
        const pass =
            (test.expect === 'high' && sim > 0.5) ||
            (test.expect === 'low' && sim < 0.5);

        console.log(`${pass ? '✓' : '✗'} ${tag1} ↔ ${tag2}: ${pct}% (expected ${test.expect})`);
    }
}

export default {
    findMatches,
    surpriseMe,
    useRecommendations,
    testEmbeddings
};
