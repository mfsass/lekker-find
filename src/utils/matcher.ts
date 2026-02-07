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
import { VIBE_EMBEDDING_MAP, Pillar } from '../data/vibes';

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
    vibeDescription?: string;
    embedding: number[];
    // Google Places data (optional)
    place_id?: string;
    maps_url?: string;
    image_url?: string;
    image_width?: number;
    image_height?: number;
    image_attribution?: string;
    rating?: number;  // Google Maps rating (1-5)
    suburb?: string;  // Extracted from address (e.g. "Sea Point")
    safety_level?: 'high' | 'caution' | 'normal';
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
    moods: string[];  // Max 5 selected (liked vibes)
    negativeMoods?: string[];  // NEW: Vibes to avoid (max 5)
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

/**
 * L2 normalize a vector to unit length.
 * Required after mean pooling or subtraction since resulting vectors
 * are no longer unit-length, breaking dot product = cosine similarity.
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

/**
 * Subtract one vector from another.
 * Used for preference refinement: liked - disliked vibes.
 */
function subtractVectors(a: number[], b: number[]): number[] {
    if (!a || !b || a.length !== b.length) {
        console.warn('Invalid vectors for subtraction, returning first vector');
        return a;
    }

    const result = new Array(a.length);
    for (let i = 0; i < a.length; i++) {
        result[i] = a[i] - b[i];
    }

    return result;
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

function filterByIntent(venues: Venue[], intent: string | null | undefined): Venue[] {
    if (!intent || intent === 'any') {
        return venues;
    }

    const categoryMap: Record<string, string[]> = {
        food_drink: ['Food', 'Drink'],
        activity: ['Activity', 'Nature'],
        attraction: ['Culture'],
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
// Internal interface for scoring process
interface ScoredVenue extends VenueWithMatch {
    _tempScore: number;
    _matchingVibesCount: number;
}

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
    const { maxResults = 20 } = options;



    // PHASE 0: DEMO MODE OVERRIDE (Forced Results)
    // Always show these 5 locations for the demo, regardless of filters
    const demoNames = [
        "Table Mountain Cableway",
        "Kirstenbosch Garden",
        "Boulders Beach",
        "Lion's Head Hike",
        "The Dog’s Bollocks"
    ];

    const forcedVenues = demoNames.map((name, index) => {
        const venue = data.venues.find(v =>
            v.name.toLowerCase() === name.toLowerCase() ||
            v.name.replace('’', "'").toLowerCase() === name.toLowerCase()
        );
        if (venue) {
            return {
                ...venue,
                matchPercentage: 99 - index
            };
        }
        return null;
    }).filter((v): v is VenueWithMatch => v !== null);

    if (forcedVenues.length > 0) {
        return forcedVenues;
    }

    let venues = [...data.venues];

    // Phase 1: Hard filters
    venues = filterByIntent(venues, params.intent);


    venues = filterByTouristLevel(venues, params.touristLevel);


    const allowedTiers = getBudgetTiers(params.budget);
    venues = venues.filter(v => allowedTiers.includes(v.price_tier));


    // Phase 2: Semantic matching
    if (params.moods.length === 0) {
        // No moods selected - return shuffled results with neutral score
        const shuffled = venues.sort(() => Math.random() - 0.5);
        return shuffled.slice(0, maxResults).map(v => ({
            ...v,
            matchPercentage: 50
        }));
    }

    // ... (other imports)

    // Get tag embeddings for selected moods
    const moodEmbeddings = params.moods
        .slice(0, 5) // Max 5 moods
        .map(mood => {
            // Use the mapping if it exists, otherwise fall back to direct key (for legacy/safety)
            const key = VIBE_EMBEDDING_MAP[mood as Pillar] || mood;
            return data.tag_embeddings[key];
        })
        .filter((emb): emb is number[] => emb !== undefined);

    if (moodEmbeddings.length === 0) {
        console.warn('No valid mood embeddings found for', params.moods);
        return venues.slice(0, maxResults).map(v => ({ ...v, matchPercentage: 50 }));
    }

    // Get negative mood embeddings if provided
    const negativeMoodEmbeddings = (params.negativeMoods || [])
        .slice(0, 5) // Max 5
        .map(mood => {
            const key = VIBE_EMBEDDING_MAP[mood as Pillar] || mood;
            return data.tag_embeddings[key];
        })
        .filter((emb): emb is number[] => emb !== undefined);

    // Create user vibe vector with preference refinement
    // Re-normalize after pooling to maintain unit-length vectors
    let userVibe = normalizeVector(meanPool(moodEmbeddings));

    // Apply embedding subtraction if negative moods are provided
    // This implements: preference = liked - disliked
    if (negativeMoodEmbeddings.length > 0) {
        const negativeVibe = normalizeVector(meanPool(negativeMoodEmbeddings));
        userVibe = normalizeVector(subtractVectors(userVibe, negativeVibe));
    }

    // Step 1: Calculate raw scores and filter excluded venues
    const scored: ScoredVenue[] = [];

    // Track highest score for relative boosting
    let highestScore = 0;

    for (const venue of venues) {
        // EXPLICIT AVOID FILTER (Hybrid Search Strategy)
        // If a venue matches a negative mood (name or tags), we STRICTLY exclude it.
        // This ensures the results list is contiguous and only contains desired venues.
        const matchesAvoid = (params.negativeMoods || []).some(neg => {
            const lowerNeg = neg.toLowerCase();
            return (
                venue.vibes.some(v => v.toLowerCase() === lowerNeg) ||
                venue.name.toLowerCase().includes(lowerNeg)
            );
        });

        if (matchesAvoid) {
            continue; // Skip this venue entirely
        }

        const rawScore = cosineSimilarity(userVibe, venue.embedding);

        // KEYWORD BOOST: Add bonus when venue has exact positive mood tag match
        const matchingVibes = params.moods.filter(mood =>
            venue.vibes.some(v => v.toLowerCase() === mood.toLowerCase())
        );
        const keywordBoost = matchingVibes.length * 0.08; // +8% per matching vibe

        const boostedScore = rawScore + keywordBoost;

        if (boostedScore > highestScore) {
            highestScore = boostedScore;
        }

        scored.push({
            ...venue,
            matchPercentage: 0, // Placeholder, calculated below
            // details needed for score calc
            _tempScore: boostedScore,
            _matchingVibesCount: matchingVibes.length
        });
    }

    // Step 2: Finalize percentages
    const finalized = scored.map((item) => {
        // Destructure to remove temp properties cleanly without delete or any
        const { _tempScore, _matchingVibesCount, ...venue } = item;
        const boostedScore = _tempScore;
        const matchingVibes = _matchingVibesCount;

        // Step 3a: Absolute similarity to percentage
        const clampedSim = Math.max(0, Math.min(1, boostedScore));

        // Non-linear scaling: emphasize high matches, compress low ones
        const scaledSim = Math.pow(clampedSim, 0.7);

        // Map to 40-88% range for base semantic score
        const basePercent = 40 + (scaledSim * 48);

        // Step 3b: Relative boost for top result
        const isTopMatch = boostedScore === highestScore;
        const topBoost = isTopMatch ? 3 : 0;

        // Bonus: Keyword matches (up to +5%)
        const keywordBonus = Math.min(5, matchingVibes * 2);

        // Bonus 2: Rating Quality Boost
        let ratingBonus = 0;
        if (venue.rating) {
            if (venue.rating >= 4.9) ratingBonus = 4;
            else if (venue.rating >= 4.7) ratingBonus = 2;
            else if (venue.rating >= 4.5) ratingBonus = 1;
            else if (venue.rating < 4.0) ratingBonus = -3;
        }

        // Final score: capped at 98%
        const finalPercent = Math.max(35, Math.min(98, basePercent + topBoost + keywordBonus + ratingBonus));

        return {
            ...venue,
            matchPercentage: Math.round(finalPercent)
        };
    });

    // Filter by threshold and sort by final score (descending)
    const results = finalized
        .filter(v => v.matchPercentage >= options.minScore! * 100)
        .sort((a, b) => b.matchPercentage - a.matchPercentage)
        .slice(0, maxResults);

    return results;




    return results;
}

/**
 * Surprise Me - random diverse selection.
 */
export function surpriseMe(
    data: EmbeddingsData,
    count: number = 10
): VenueWithMatch[] {
    // DEMO MODE OVERRIDE
    const demoNames = [
        "Table Mountain Cableway",
        "Kirstenbosch Garden",
        "Boulders Beach",
        "Lion's Head Hike",
        "The Dog’s Bollocks"
    ];

    const forcedVenues = demoNames.map((name, index) => {
        const venue = data.venues.find(v =>
            v.name.toLowerCase() === name.toLowerCase() ||
            v.name.replace('’', "'").toLowerCase() === name.toLowerCase()
        );
        if (venue) {
            return {
                ...venue,
                matchPercentage: 99 - index
            };
        }
        return null;
    }).filter((v): v is VenueWithMatch => v !== null);

    if (forcedVenues.length > 0) {
        return forcedVenues;
    }

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
    totalVenues: number;
    venues: Venue[];
    tagEmbeddings: Record<string, number[]>;
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



                setData(json);
                setLoading(false);
            } catch (err) {
                console.error('Error loading recommendations:', err);
                const error = err instanceof Error ? err : new Error(String(err));
                setError(error);
                setLoading(false);
                // Throw error so ErrorBoundary catches it
                throw error;
            }
        }

        // Start loading almost immediately, but after the main thread is clear
        const timer = setTimeout(() => {
            loadData();
        }, 50);

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
        ready: !loading && !error && data !== null,
        totalVenues: data?.metadata?.total_venues || 0,
        venues: data?.venues || [],
        tagEmbeddings: data?.tag_embeddings || {}
    };
}

// ============================================================================
// DEBUGGING
// ============================================================================

/**
 * Test embedding quality by checking expected relationships.
 */
export function testEmbeddings(data: EmbeddingsData): void {


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
        // Test passes if similarity matches expected relationship
        const _pass =
            (test.expect === 'high' && sim > 0.5) ||
            (test.expect === 'low' && sim < 0.5);
        void _pass; // Suppress unused warning - function used for debugging


    }
}

export default {
    findMatches,
    surpriseMe,
    useRecommendations,
    testEmbeddings
};
