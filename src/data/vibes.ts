/**
 * Vibe/Mood Master List
 * 
 * Curated from 320+ unique vibes in venue data.
 * Context-aware sampling based on user's previous selections.
 * 
 * SEO: Supports "things to do in Cape Town" filtering.
 * Accessibility: Simple, clear mood words.
 */

// 1. Synonym Groups: Choosing one from a group prevents selecting others.
const SYNONYM_GROUPS: Record<string, string[]> = {
    calm: ['Relaxed', 'Chill', 'Easy-going', 'Peaceful', 'Quiet', 'Serene', 'Calm'],
    lively: ['Lively', 'Fun', 'Buzzy', 'Energetic', 'Busy', 'Festive', 'Happy'],
    fancy: ['Classy', 'Fancy', 'Upscale', 'Exclusive', 'VIP', 'Posh', 'Stylish'], // Simplified 'Sophisticated', 'Refined'
    scenic: ['Scenic', 'Views', 'Ocean-view', 'Beautiful', 'Pretty', 'Photo-ready'], // Simplified 'Panoramic'
    hidden: ['Hidden', 'Secret', 'Quiet-spot', 'Hard-to-find', 'Private'], // Simplified 'Undiscovered'
    cool: ['Trendy', 'Cool', 'Hip', 'Funky', 'Artsy', 'Modern'],
    local: ['Local', 'Real', 'Authentic', 'Roots', 'Traditional', 'Home-style'],
    social: ['Social', 'Friendly', 'Welcoming', 'Family', 'Groups'],
    romantic: ['Romantic', 'Cozy', 'Cute', 'Date-night'],
    unique: ['Unique', 'Different', 'Creative', 'Special', 'Magic']
};

const VIBE_TO_GROUP: Record<string, string> = {};
Object.entries(SYNONYM_GROUPS).forEach(([group, words]) => {
    words.forEach(word => {
        VIBE_TO_GROUP[word] = group;
    });
});


// 2. New Curated Vibes by Category (44 total)
// These have embeddings generated from rich descriptions for optimal matching

// Universal vibes (shown for ALL intents)
const UNIVERSAL_VIBES = [
    'Hidden', 'Famous', 'Romantic', 'Family', 'Views',
    'Chill', 'Lively', 'Local', 'Unique', 'Cozy'
] as const;

// Food & Drink vibes
const FOOD_VIBES = [
    'Brunch', 'Fine Dining', 'Street Food', 'International', 'Traditional',
    'Wine', 'Craft Beer', 'Coffee', 'Sweet Tooth', 'Evening', 'Halaal', 'Outdoor Dining'
] as const;

// Activity vibes
const ACTIVITY_VIBES = [
    'Beach', 'Mountain', 'Water', 'Forest', 'Outdoor',
    'Urban', 'Sport', 'Wellness', 'Adventure', 'Wildlife', 'Learning', 'Sunset'
] as const;

// Attraction vibes
const ATTRACTION_VIBES = [
    'History', 'Art', 'Music', 'Theatre', 'Museum',
    'Interactive', 'Heritage', 'Photo-Ready', 'Markets', 'Architecture'
] as const;

// Related vibes - used for smart avoid suggestions
// When user picks a vibe, these related vibes become relevant avoid candidates
const RELATED_VIBES: Record<string, string[]> = {
    // Water-related - helps distinguish water TYPE
    'Water': ['Beach', 'Outdoor', 'Wildlife'],
    'Beach': ['Water', 'Outdoor', 'Sunset'],

    // Nature-related - helps distinguish nature TYPE
    'Mountain': ['Beach', 'Water', 'Urban', 'Forest'],
    'Forest': ['Beach', 'Mountain', 'Urban'],
    'Outdoor': ['Urban', 'Beach', 'Water'],

    // Adventure-related - helps distinguish adventure TYPE
    'Adventure': ['Wellness', 'Chill', 'Water', 'Mountain'],
    'Sport': ['Wellness', 'Chill', 'Adventure'],
    'Wellness': ['Adventure', 'Sport', 'Lively'],

    // Food-related - helps distinguish food TYPE
    'Fine Dining': ['Street Food', 'Brunch', 'Lively'],
    'Street Food': ['Fine Dining', 'Romantic'],
    'Traditional': ['International', 'Fine Dining'],
    'International': ['Traditional'],
    'Wine': ['Craft Beer', 'Lively', 'Urban'],
    'Brunch': ['Evening', 'Fine Dining'],
    'Evening': ['Brunch'],

    // Atmosphere-related - helps distinguish vibe TYPE
    'Romantic': ['Family', 'Lively'],
    'Family': ['Romantic', 'Evening'],
    'Lively': ['Chill', 'Romantic', 'Hidden'],
    'Chill': ['Lively', 'Adventure'],
    'Hidden': ['Famous', 'Lively'],
    'Famous': ['Hidden', 'Local'],
    'Local': ['Famous'],

    // Culture-related - helps distinguish culture TYPE
    'History': ['Art', 'Interactive'],
    'Art': ['History', 'Music'],
    'Music': ['Art', 'Theatre'],
};

// Legacy VIBES_BY_CONTEXT for backward compatibility (updated with new vibes)
const VIBES_BY_CONTEXT = {
    // Intent-specific vibes (NEW curated lists)
    food_drink: [...FOOD_VIBES, 'Romantic', 'Views', 'Lively', 'Chill'],
    activity: [...ACTIVITY_VIBES, 'Views', 'Family', 'Romantic'],
    attraction: [...ATTRACTION_VIBES, 'Famous', 'Hidden', 'Family'],

    // Tourist level specific vibes
    famous: ['Famous', 'Views', 'Photo-Ready', 'Lively'],
    popular: ['Lively', 'Views', 'Outdoor'],
    balanced: ['Unique', 'Local', 'Views'],
    local: ['Local', 'Hidden', 'Traditional', 'Unique'],
    hidden: ['Hidden', 'Local', 'Unique', 'Chill'],

    // Budget specific vibes
    free: ['Outdoor', 'Beach', 'Views', 'Sunset', 'Mountain'],
    budget: ['Street Food', 'Local', 'Outdoor'],
    moderate: ['Coffee', 'Brunch', 'Craft Beer', 'Outdoor Dining'],
    premium: ['Fine Dining', 'Wine', 'Romantic', 'Views']
} as const;

// 3. Negative Exclusion Rules (prevent conflicting vibes)
const EXCLUSIONS: Record<string, string[]> = {
    food_drink: ['Mountain', 'Beach', 'Wildlife', 'Adventure', 'Sport'],
    activity: ['Fine Dining', 'Wine', 'Brunch', 'Coffee'],
    attraction: ['Brunch', 'Street Food', 'Beach', 'Sport'],
    budget: ['Fine Dining', 'Wine'],
    free: ['Fine Dining', 'Wine', 'Sweet Tooth'],
    local: ['Famous'],
    famous: ['Hidden', 'Local']
};


// ALL_VIBES - Now ONLY the 44 curated vibes
// These are the ONLY vibes available for selection - clear, simple, and effective
export const ALL_VIBES = [
    // Universal (10) - shown for ALL intents
    ...UNIVERSAL_VIBES,
    // Food & Drink (12)
    ...FOOD_VIBES,
    // Activity (12)
    ...ACTIVITY_VIBES,
    // Attraction (10)
    ...ATTRACTION_VIBES,
] as const;


/**
 * Get context-aware mood suggestions based on user selections.
 * 
 * Key principle: Only show vibes relevant to the intent!
 * - Food intent → Food vibes + Universal vibes
 * - Activity intent → Activity vibes + Universal vibes
 * - Attraction intent → Attraction vibes + Universal vibes
 */
export function getContextualMoods(
    intent: string | null,
    touristLevel: number | null,
    budget: string | null,
    count: number = 12,
    avoidList: string[] = []
): string[] {
    const bannedVibes = new Set<string>([...avoidList]);

    // Build allowed vibes based on intent (CRITICAL: context filtering)
    const allowedVibes: string[] = [...UNIVERSAL_VIBES];

    if (intent === 'food_drink') {
        allowedVibes.push(...FOOD_VIBES);
    } else if (intent === 'activity') {
        allowedVibes.push(...ACTIVITY_VIBES);
    } else if (intent === 'attraction') {
        allowedVibes.push(...ATTRACTION_VIBES);
    } else {
        // 'any' or null - show a mix of all
        allowedVibes.push(...FOOD_VIBES, ...ACTIVITY_VIBES, ...ATTRACTION_VIBES);
    }

    // Apply exclusions
    if (intent && EXCLUSIONS[intent]) EXCLUSIONS[intent].forEach(v => bannedVibes.add(v));
    if (budget && EXCLUSIONS[budget]) EXCLUSIONS[budget].forEach(v => bannedVibes.add(v));
    if (touristLevel) {
        const levelKey = touristLevel <= 2 ? 'famous' : touristLevel >= 4 ? 'local' : null;
        if (levelKey && EXCLUSIONS[levelKey]) EXCLUSIONS[levelKey].forEach(v => bannedVibes.add(v));
    }

    // Filter to only allowed vibes that aren't banned
    const candidates = allowedVibes.filter(v => !bannedVibes.has(v));

    // Weight vibes by context
    const candidateWeights: Record<string, number> = {};
    const addWeight = (vibes: readonly string[], weight: number) => {
        vibes.forEach(v => {
            if (candidates.includes(v)) {
                candidateWeights[v] = (candidateWeights[v] || 0) + weight;
            }
        });
    };

    // Intent-specific vibes get higher weight
    if (intent && intent !== 'any' && intent in VIBES_BY_CONTEXT) {
        addWeight(VIBES_BY_CONTEXT[intent as keyof typeof VIBES_BY_CONTEXT], 4);
    }
    // Tourist level specific vibes
    if (touristLevel !== null) {
        const levelKey = touristLevel <= 2 ? 'famous' : touristLevel === 3 ? 'balanced' : touristLevel === 4 ? 'local' : 'hidden';
        if (levelKey in VIBES_BY_CONTEXT) addWeight(VIBES_BY_CONTEXT[levelKey as keyof typeof VIBES_BY_CONTEXT], 3);
    }
    // Budget specific vibes
    if (budget && budget !== 'any' && budget in VIBES_BY_CONTEXT) {
        addWeight(VIBES_BY_CONTEXT[budget as keyof typeof VIBES_BY_CONTEXT], 2);
    }
    // Universal vibes always get base weight
    addWeight(UNIVERSAL_VIBES, 2);
    // Add some randomness
    candidates.forEach(v => {
        candidateWeights[v] = (candidateWeights[v] || 0) + Math.random();
    });

    // Sort by weight and select with group deduplication
    const sortedCandidates = Object.entries(candidateWeights)
        .sort(([, a], [, b]) => b - a)
        .map(([vibe]) => vibe);

    const selectedVibes: string[] = [];
    const usedGroups = new Set<string>();

    for (const vibe of sortedCandidates) {
        if (selectedVibes.length >= count) break;
        const group = VIBE_TO_GROUP[vibe];
        if (group && usedGroups.has(group)) continue;
        selectedVibes.push(vibe);
        if (group) usedGroups.add(group);
    }

    // Fallback if not enough vibes
    if (selectedVibes.length < count) {
        const remaining = sortedCandidates.filter(v => !selectedVibes.includes(v));
        selectedVibes.push(...remaining.slice(0, count - selectedVibes.length));
    }

    return selectedVibes.sort(() => Math.random() - 0.5);
}

// ... Exports unchanged ...
export const BUDGET_RANGES = {
    free: { min: 0, max: 0, label: 'Free' },
    budget: { min: 1, max: 150, label: 'Budget' },
    moderate: { min: 150, max: 350, label: 'Moderate' },
    premium: { min: 350, max: Infinity, label: 'Premium' },
} as const;

export function isTouristLevel(level: number | null): boolean {
    return level !== null && level <= 2;
}

export function getBudgetDisplay(
    budget: keyof typeof BUDGET_RANGES,
    currency: 'ZAR' | 'EUR' | 'USD' = 'ZAR',
    rates: Record<string, number> = { ZAR: 1, EUR: 0.05, USD: 0.053 }
): string {
    const range = BUDGET_RANGES[budget];
    if (budget === 'free') return 'Free';
    const rate = rates[currency] || 1;
    const min = Math.round(range.min * rate);
    const max = range.max === Infinity ? Infinity : Math.round(range.max * rate);
    const symbol = currency === 'ZAR' ? 'R' : currency === 'EUR' ? '€' : '$';
    if (budget === 'budget') return `Under ${symbol}${max}`;
    if (budget === 'premium') return `${symbol}${min}+`;
    return `${symbol}${min} - ${symbol}${max}`;
}

export function shouldShowPriceDisclaimer(intent: string | null, touristLevel: number | null): boolean {
    if (isTouristLevel(touristLevel)) return true;
    if (intent === 'activity' || intent === 'nature' || intent === 'culture') return true;
    return false;
}

/**
 * Get vibes that are implied by the user's questionnaire selections.
 * These vibes should NOT appear in the "avoid" step as they conflict
 * with what the user explicitly requested.
 * 
 * Example: If user selected "Must-see" tourist level, offering "Famous" 
 * or "Must-see" as an avoid option would be contradictory.
 */
export function getImpliedVibesFromSelections(
    intent: string | null,
    touristLevel: number | null,
    budget: string | null
): string[] {
    const impliedVibes = new Set<string>();

    // Tourist level implies certain vibes shouldn't be avoided
    if (touristLevel !== null) {
        if (touristLevel <= 2) {
            // Must-see or Popular → don't allow avoiding famous/tourist vibes
            VIBES_BY_CONTEXT.famous.forEach(v => impliedVibes.add(v));
            if (touristLevel === 2) {
                VIBES_BY_CONTEXT.popular.forEach(v => impliedVibes.add(v));
            }
        } else if (touristLevel === 3) {
            // Mix of both → neutral, less strict
            VIBES_BY_CONTEXT.balanced.forEach(v => impliedVibes.add(v));
        } else if (touristLevel === 4) {
            // Off the path → don't allow avoiding local vibes
            VIBES_BY_CONTEXT.local.forEach(v => impliedVibes.add(v));
        } else if (touristLevel >= 5) {
            // Hidden gems → don't allow avoiding hidden/secret vibes
            VIBES_BY_CONTEXT.hidden.forEach(v => impliedVibes.add(v));
            VIBES_BY_CONTEXT.local.forEach(v => impliedVibes.add(v));
        }
    }

    // Budget implies certain vibes shouldn't be avoided
    if (budget && budget !== 'any' && budget in VIBES_BY_CONTEXT) {
        VIBES_BY_CONTEXT[budget as keyof typeof VIBES_BY_CONTEXT].forEach(v => impliedVibes.add(v));
    }

    // Intent implies certain vibes shouldn't be avoided
    if (intent && intent !== 'any' && intent in VIBES_BY_CONTEXT) {
        VIBES_BY_CONTEXT[intent as keyof typeof VIBES_BY_CONTEXT].forEach(v => impliedVibes.add(v));
    }

    return Array.from(impliedVibes);
}

/**
 * Get smart avoid options based on what the user already selected.
 * 
 * Key principles:
 * 1. Never show vibes they already selected (no conflicts)
 * 2. Never show synonyms of selected vibes (no contradictions)
 * 3. ONLY show vibes relevant to their intent (no food vibes for activity!)
 * 4. Show RELATED vibes that help refine their selection
 *    - e.g., picked "Water" → show "Beach", "Outdoor" to narrow down water TYPE
 * 5. Add some context-appropriate universal options
 * 
 * @param selectedVibes - Vibes the user has already selected as "good vibes"
 * @param intent - The user's intent (food_drink, activity, attraction)
 * @param count - Number of avoid options to return
 */
export function getContextualAvoidOptions(
    selectedVibes: string[],
    intent: string | null,
    count: number = 8
): string[] {
    const avoidCandidates = new Set<string>();
    const excludeFromAvoid = new Set<string>(selectedVibes);

    // Determine which vibes are ALLOWED based on intent
    // This prevents showing food vibes for activity intent, etc.
    const allowedVibes = new Set<string>([...UNIVERSAL_VIBES]);

    if (intent === 'food_drink' || intent === 'any' || !intent) {
        FOOD_VIBES.forEach(v => allowedVibes.add(v));
    }
    if (intent === 'activity' || intent === 'any' || !intent) {
        ACTIVITY_VIBES.forEach(v => allowedVibes.add(v));
    }
    if (intent === 'attraction' || intent === 'any' || !intent) {
        ATTRACTION_VIBES.forEach(v => allowedVibes.add(v));
    }

    // Also exclude synonyms of selected vibes
    selectedVibes.forEach(vibe => {
        const group = VIBE_TO_GROUP[vibe];
        if (group && SYNONYM_GROUPS[group]) {
            SYNONYM_GROUPS[group].forEach(synonym => excludeFromAvoid.add(synonym));
        }
    });

    // Helper to add vibe only if allowed by intent context
    const addIfAllowed = (vibe: string) => {
        if (allowedVibes.has(vibe) && !excludeFromAvoid.has(vibe)) {
            avoidCandidates.add(vibe);
        }
    };

    // 1. Add RELATED vibes based on what they selected (highest priority)
    // These are contextually relevant refinements
    selectedVibes.forEach(vibe => {
        const related = RELATED_VIBES[vibe];
        if (related) {
            related.forEach(r => addIfAllowed(r));
        }
    });

    // 2. Add universal vibes that make sense as refinements (always allowed)
    UNIVERSAL_VIBES.forEach(vibe => {
        if (!excludeFromAvoid.has(vibe)) {
            avoidCandidates.add(vibe);
        }
    });

    // 3. Add intent-specific vibes they didn't select
    if (intent === 'food_drink') {
        FOOD_VIBES.forEach(vibe => addIfAllowed(vibe));
    } else if (intent === 'activity') {
        ACTIVITY_VIBES.forEach(vibe => addIfAllowed(vibe));
    } else if (intent === 'attraction') {
        ATTRACTION_VIBES.forEach(vibe => addIfAllowed(vibe));
    }

    // Convert to array and prioritize related vibes
    const relatedSet = new Set<string>();
    selectedVibes.forEach(vibe => {
        const related = RELATED_VIBES[vibe];
        if (related) {
            related.forEach(r => {
                if (allowedVibes.has(r)) relatedSet.add(r);
            });
        }
    });

    // Sort: related vibes first, then universal, then rest
    const universalSet = new Set<string>(UNIVERSAL_VIBES);
    const sortedCandidates = Array.from(avoidCandidates)
        .filter(v => !excludeFromAvoid.has(v))
        .sort((a, b) => {
            // Priority: related (0) > universal (1) > other (2)
            const aPriority = relatedSet.has(a) ? 0 : universalSet.has(a) ? 1 : 2;
            const bPriority = relatedSet.has(b) ? 0 : universalSet.has(b) ? 1 : 2;
            return aPriority - bPriority;
        });

    // Take top N, then light shuffle for variety
    const result = sortedCandidates.slice(0, count);
    return result.sort(() => Math.random() - 0.5);
}

// Export the new curated vibe lists for use elsewhere
export { UNIVERSAL_VIBES, FOOD_VIBES, ACTIVITY_VIBES, ATTRACTION_VIBES };
