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


// 2. Refined Context Lists (Simplified English)
const VIBES_BY_CONTEXT = {
    // Intent-specific vibes
    food: ['Handmade', 'Tasty', 'Comfort', 'Healthy', 'Treat', 'Street-food', 'Fresh', 'Trendy', 'Traditional', 'Simple'], // Artisanal->Handmade, Indulgent->Treat
    drink: ['Craft', 'Cocktails', 'Hidden-bar', 'Rooftop', 'Sunset', 'Tasting', 'Dive-bar', 'Classy', 'Social', 'Wine'],
    activity: ['Adventure', 'Exciting', 'Active', 'Learning', 'Wellness', 'Workshop', 'Outdoor', 'Culture', 'Fun'],
    nature: ['Mountain', 'Beach', 'Forest', 'Garden', 'Wild', 'Hiking', 'Picnic', 'Sunset', 'Sea-life', 'Open-air'],
    culture: ['History', 'Museum', 'Art', 'Music', 'Theatre', 'Heritage', 'Soul', 'Design', 'Stories'],

    // Tourist level specific vibes
    famous: ['Famous', 'Must-see', 'Tourist-friendly', 'Classic', 'Landmark', 'Busy', 'Photo-ready'], // Iconic->Famous
    popular: ['Popular', 'Modern', 'Stylish', 'Crowded', 'Well-known'],
    balanced: ['Mix', 'Easy', 'Diverse', 'Reliable', 'Good-value'],
    local: ['Neighborhood', 'Raw', 'Kasi-vibe', 'Roots', 'Home-grown', 'Real'],
    hidden: ['Secret-spot', 'Alleyway', 'No-signage', 'Locals-only', 'Hard-to-find'],

    // Budget specific vibes
    free: ['Public', 'Walking', 'Free', 'Nature', 'Park'],
    budget: ['Cheap', 'Good-value', 'Simple', 'Student', 'Canteen'], // Value->Good-value
    moderate: ['Casual', 'Cafe', 'Nice', 'Standard'],
    premium: ['Fine-dining', 'VIP', 'Luxury', 'Boutique', 'Private']
} as const;

// 3. Negative Exclusion Rules (Same as before)
const EXCLUSIONS: Record<string, string[]> = {
    activity: ['Tasty', 'Tasting', 'Fine-dining', 'Wine', 'Cocktails'],
    food: ['Hiking', 'Active', 'Extreme', 'Museum', 'Theatre'],
    drink: ['Hiking', 'Active', 'Family', 'Playground', 'Wellness'],
    budget: ['VIP', 'Luxury', 'Fine-dining', 'Exclusive', 'Upscale', 'Treat', 'Boutique', 'Private'],
    free: ['VIP', 'Luxury', 'Fine-dining', 'Shopping', 'Paid', 'Expensive', 'Treat', 'Drinks'],
    local: ['Tourist-friendly', 'Famous', 'Must-see', 'Crowded', 'Bus-tour'],
    famous: ['Hidden', 'Secret', 'Locals-only', 'No-signage', 'Rough-diamond']
};


// Simplified ALL_VIBES
export const ALL_VIBES = [
    // Simple Atmosphere
    'Chill', 'Lively', 'Peaceful', 'Fun', 'Romantic', 'Cozy', 'Happy', 'Relaxed',
    'Buzzy', 'Quiet', 'Warm', 'Festive', 'Moody',
    // Simple Style  
    'Trendy', 'Cool', 'Funky', 'Old-school', 'Modern', 'Rustic', 'Boho', 'Classy',
    'Handmade', 'Simple', 'Mixed', 'Retro', 'Stylish',
    // Simple Experience
    'Adventure', 'Exciting', 'Secret', 'Hidden', 'Famous', 'Real', 'Local', 'Unique',
    'VIP', 'Deep', 'Interactive', 'Inspiring', 'Soulful', 'Genuine',
    // Simple Setting
    'Scenic', 'Big-views', 'Coastal', 'City', 'Nature', 'Forest', 'Sunset', 'Vineyard',
    'Waterfront', 'Mountain', 'Garden', 'Rooftop', 'Beach', 'Country',
    // Simple Social
    'Social', 'Family', 'Casual', 'Friendly', 'Welcoming', 'Community',
    // Simple Food & Drink
    'Tasty', 'Healthy', 'Treat', 'Craft-Beer', 'Wine', 'Foodie', 'Street-food', 'Fresh',
    // Simple Cultural
    'Artsy', 'Music', 'History', 'Culture', 'Learning', 'Heritage',
    // Simple Activity
    'Active', 'Playful', 'Creative', 'Wellness', 'Extreme',
    // Specifics
    'Comfort', 'Tasting', 'Dive-bar', 'Sea-life', 'Picnic', 'Must-see', 'Landmark', 'Photo-ready',
    'Minimal', 'Good-value', 'Private', 'Boutique', 'Neighborhood', 'Kasi-vibe', 'Roots',
    'Home-grown', 'Secret-spot', 'No-signage', 'Locals-only'
] as const;


/**
 * Get context-aware mood suggestions based on user selections.
 */
export function getContextualMoods(
    intent: string | null,
    touristLevel: number | null,
    budget: string | null,
    count: number = 12,
    avoidList: string[] = [] // New Param: List of vibes to explicitly avoid (for Refresh)
): string[] {
    const candidateWeights: Record<string, number> = {};
    const bannedVibes = new Set<string>([...avoidList]); // Init with avoid list

    // 0. Build Exclusion Set
    if (intent && EXCLUSIONS[intent]) EXCLUSIONS[intent].forEach(v => bannedVibes.add(v));
    if (budget && EXCLUSIONS[budget]) EXCLUSIONS[budget].forEach(v => bannedVibes.add(v));
    if (touristLevel) {
        const levelKey = touristLevel <= 2 ? 'famous' : touristLevel >= 4 ? 'local' : null;
        if (levelKey && EXCLUSIONS[levelKey]) EXCLUSIONS[levelKey].forEach(v => bannedVibes.add(v));
    }

    const addWeight = (list: readonly string[], weight: number) => {
        list.forEach(v => {
            if (bannedVibes.has(v)) return;
            candidateWeights[v] = (candidateWeights[v] || 0) + weight;
        });
    };

    // 1. Context Weights
    if (intent && intent !== 'any' && intent in VIBES_BY_CONTEXT) {
        addWeight(VIBES_BY_CONTEXT[intent as keyof typeof VIBES_BY_CONTEXT], 4);
    }
    if (touristLevel !== null) {
        const levelKey = touristLevel <= 2 ? 'famous' : touristLevel === 3 ? 'balanced' : touristLevel === 4 ? 'local' : 'hidden';
        if (levelKey in VIBES_BY_CONTEXT) addWeight(VIBES_BY_CONTEXT[levelKey as keyof typeof VIBES_BY_CONTEXT], 3);
    }
    if (budget && budget !== 'any' && budget in VIBES_BY_CONTEXT) {
        addWeight(VIBES_BY_CONTEXT[budget as keyof typeof VIBES_BY_CONTEXT], 2);
    }

    // 2. Diversity
    const randomFresh = [...ALL_VIBES].sort(() => Math.random() - 0.5).slice(0, 20);
    addWeight(randomFresh, 1);

    // 3. Select with Group Deduplication
    const sortedCandidates = Object.entries(candidateWeights)
        .sort(([, weightA], [, weightB]) => weightB - weightA)
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

    // 4. Fallback
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
