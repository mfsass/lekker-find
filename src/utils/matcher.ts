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

    // Calculate similarity for each venue
    const scored = venues.map(venue => {
        const score = cosineSimilarity(userVibe, venue.embedding);
        return {
            ...venue,
            matchPercentage: Math.round(score * 100)
        };
    });

    // Filter by threshold and sort
    const filtered = scored
        .filter(v => v.matchPercentage >= minScore * 100)
        .sort((a, b) => b.matchPercentage - a.matchPercentage);

    const results = filtered.slice(0, maxResults);

    const duration = performance.now() - startTime;
    console.log(`✓ Found ${results.length} matches in ${duration.toFixed(1)}ms`);
    console.log(`  Top score: ${results[0]?.matchPercentage ?? 0}%`);

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
                const response = await fetch('/lekker-find-data.json', { priority: 'low' });

                if (!response.ok) {
                    throw new Error(`Failed to load embeddings: ${response.status}`);
                }

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
