/**
 * Vibe/Mood Master List - The Lekker 15 Pillars
 * 
 * Consolidated taxonomy for better personalization and simple UI.
 * Each Pillar maps to a specific embedding key for semantic matching.
 */

// 1. The 17 Pillars (Expanded for Intelligence)
export const PILLARS = [
    'Scenic', 'Social', 'Intimate', 'Active', 'Chill',
    'Elegant', 'Authentic', 'Artsy', 'Industrial', 'Family',
    'Foodie', 'Healthy', 'Wine', 'Beach', 'Coffee', 'Nightlife',
    'Music'
] as const;

export type Pillar = typeof PILLARS[number];

// 2. Embedding Key Map
// Maps the UI Pillar to the closest available embedding in our vector database
export const VIBE_EMBEDDING_MAP: Record<Pillar, string> = {
    'Scenic': 'Scenic',
    'Social': 'Social',
    'Intimate': 'Romantic',
    'Active': 'Active',
    'Chill': 'Chill',
    'Elegant': 'Classy',
    'Authentic': 'Local',
    'Artsy': 'Artsy',
    'Industrial': 'Modern',
    'Family': 'Family',
    'Foodie': 'Foodie',
    'Healthy': 'Healthy',   // New: Restores Vegan/Fresh intelligence
    'Wine': 'Wine',
    'Beach': 'Beach',
    'Coffee': 'Breakfast',
    'Nightlife': 'Festive',
    'Music': 'Music'        // New: Restores Jazz/Live intelligence
};

// 3. Categories for Contextual Display
export const UNIVERSAL_VIBES: Pillar[] = [
    'Scenic', 'Social', 'Intimate', 'Chill', 'Authentic'
];

export const FOOD_VIBES: Pillar[] = [
    'Foodie', 'Healthy', 'Wine', 'Coffee', 'Elegant', 'Nightlife'
];

export const ACTIVITY_VIBES: Pillar[] = [
    'Active', 'Beach', 'Family', 'Scenic', 'Music'
];

export const ATTRACTION_VIBES: Pillar[] = [
    'Artsy', 'Industrial', 'Authentic', 'Family', 'Music'
];

// 4. Intent Mapping logic (simplified)
export function getContextualMoods(
    intent: string | null,
    _touristLevel: number | null,
    _budget: string | null,
    count: number = 12,
    avoidList: string[] = []
): string[] {
    const banned = new Set(avoidList);
    let candidates: Pillar[] = [];

    // Base Selection by Intent
    if (intent === 'food_drink') {
        candidates = [...FOOD_VIBES, ...UNIVERSAL_VIBES];
    } else if (intent === 'activity') {
        candidates = [...ACTIVITY_VIBES, ...UNIVERSAL_VIBES];
    } else if (intent === 'attraction') {
        candidates = [...ATTRACTION_VIBES, ...UNIVERSAL_VIBES];
    } else {
        candidates = [...PILLARS];
    }

    // Deduplicate
    candidates = Array.from(new Set(candidates));

    // Filter Banned
    candidates = candidates.filter(v => !banned.has(v));

    // Sort/Shuffle
    // Prioritize context-specifics?
    // For now, random shuffle is good enough for discovery
    return candidates.sort(() => Math.random() - 0.5).slice(0, count);
}

// 5. Avoid Logic
// Strict Context: Only suggest avoiding things that are actually in the category.
// e.g. If Intent=Nature, do NOT suggest avoiding "Wine" (as it's not there anyway).
export function getContextualAvoidOptions(
    selectedVibes: string[],
    intent: string | null,
    count: number = 6
): string[] {
    const selected = new Set(selectedVibes);
    let allowed: Pillar[] = [];

    // 1. Determine Allowed Universe (Same logic as Selection)
    if (intent === 'food_drink') {
        allowed = [...FOOD_VIBES, ...UNIVERSAL_VIBES];
    } else if (intent === 'activity') {
        allowed = [...ACTIVITY_VIBES, ...UNIVERSAL_VIBES];
    } else if (intent === 'attraction') {
        allowed = [...ATTRACTION_VIBES, ...UNIVERSAL_VIBES];
    } else {
        allowed = [...PILLARS];
    }

    // 2. Filter out already selected vibes
    const options = allowed.filter(p => !selected.has(p));

    // 3. Sort/Shuffle
    // In the future, we can add "Antagonist" logic here (e.g. if 'Chill' selected, priorize 'Active' for avoid)
    return options.sort(() => Math.random() - 0.5).slice(0, count);
}

// Exports for compatibility
export const ALL_VIBES = PILLARS;

// UI Helpers
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

export function getImpliedVibesFromSelections(
    _intent: string | null,
    _touristLevel: number | null,
    _budget: string | null
): string[] {
    return []; // Simplified for now
}
