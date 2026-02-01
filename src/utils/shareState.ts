/**
 * Share State Utility
 * ===================
 * 
 * Encodes/decodes filter selections to/from URL search params.
 * Compact format optimized for WhatsApp sharing (avoids truncation).
 * 
 * Format: ?q=intent.touristLevel.budget.moods.-avoidedMoods
 * Example: ?q=fd.3.b.romantic,hidden.-busy
 */

// Intent shortcodes
const INTENT_MAP: Record<string, string> = {
    'food_drink': 'fd',
    'activity': 'a',
    'attraction': 'at',
    'any': 'any',
};

const INTENT_REVERSE: Record<string, string> = {
    'fd': 'food_drink',
    'a': 'activity',
    'at': 'attraction',
    'any': 'any',
};

// Budget shortcodes
const BUDGET_MAP: Record<string, string> = {
    'free': 'f',
    'budget': 'b',
    'moderate': 'm',
    'premium': 'p',
    'any': 'any',
};

const BUDGET_REVERSE: Record<string, string> = {
    'f': 'free',
    'b': 'budget',
    'm': 'moderate',
    'p': 'premium',
    'any': 'any',
};

export interface ShareState {
    intent?: string | null;
    touristLevel?: number | null;
    budget?: string | null;
    moods?: string[];
    avoidedMoods?: string[];
    index?: number; // Current card index
    venueId?: string; // Specific venue ID for single-item sharing
}

/**
 * Encode filter state to compact URL param
 * Format: intent.touristLevel.budget.moods.-avoidedMoods.i{index}
 */
export function encodeShareState(state: ShareState): string {
    const parts: string[] = [];

    // Intent (required for valid share)
    parts.push(state.intent ? (INTENT_MAP[state.intent] || state.intent) : 'any');

    // Tourist level (1-5)
    parts.push(state.touristLevel?.toString() || '3');

    // Budget
    parts.push(state.budget ? (BUDGET_MAP[state.budget] || state.budget) : 'any');

    // Moods (comma-separated, lowercase)
    if (state.moods && state.moods.length > 0) {
        parts.push(state.moods.map(m => m.toLowerCase().replace(/\s+/g, '')).join(','));
    } else {
        parts.push('_'); // Placeholder for empty moods
    }

    // Avoided moods (prefixed with minus, comma-separated)
    if (state.avoidedMoods && state.avoidedMoods.length > 0) {
        parts.push('-' + state.avoidedMoods.map(m => m.toLowerCase().replace(/\s+/g, '')).join(','));
    }

    // Index (optional, prefixed with i)
    if (state.index !== undefined && state.index > 0) {
        parts.push(`i${state.index}`);
    }

    // Venue ID (optional, prefixed with v)
    if (state.venueId) {
        parts.push(`v${state.venueId}`);
    }

    return parts.join('.');
}

/**
 * Decode URL param to filter state
 */
export function decodeShareState(param: string): ShareState | null {
    if (!param) return null;

    try {
        const parts = param.split('.');

        if (parts.length < 3) return null;

        const state: ShareState = {
            intent: INTENT_REVERSE[parts[0]] || parts[0] || null,
            touristLevel: parseInt(parts[1]) || null,
            budget: BUDGET_REVERSE[parts[2]] || parts[2] || null,
            moods: [],
            avoidedMoods: [],
            index: 0
        };

        // Parse remaining parts (moods, avoid, index)
        for (let i = 3; i < parts.length; i++) {
            const part = parts[i];

            if (part === '_') continue;

            if (part.startsWith('i')) {
                // Index
                state.index = parseInt(part.slice(1)) || 0;
            } else if (part.startsWith('v')) {
                // Venue ID
                state.venueId = part.slice(1);
            } else if (part.startsWith('-')) {
                // Avoided moods
                state.avoidedMoods = part.slice(1).split(',').map(m => capitalizeWords(m));
            } else {
                // Moods
                state.moods = part.split(',').map(m => capitalizeWords(m));
            }
        }

        return state;
    } catch {
        console.error('Failed to decode share state:', param);
        return null;
    }
}

/**
 * Capitalize first letter of each word (for mood tags)
 */
function capitalizeWords(str: string): string {
    return str.replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Generate shareable URL with encoded state
 */
export function getShareUrl(state: ShareState): string {
    const encoded = encodeShareState(state);
    const baseUrl = typeof window !== 'undefined'
        ? `${window.location.origin}${window.location.pathname}`
        : 'https://lekker-find.co.za';

    return `${baseUrl}?q=${encoded}`;
}

/**
 * Parse URL on page load to check for shared state
 */
export function parseUrlState(): ShareState | null {
    if (typeof window === 'undefined') return null;

    const params = new URLSearchParams(window.location.search);
    const q = params.get('q');

    if (!q) return null;

    return decodeShareState(q);
}

/**
 * Clear share params from URL without reload
 */
export function clearShareParams(): void {
    if (typeof window === 'undefined') return;

    const url = new URL(window.location.href);
    url.searchParams.delete('q');
    window.history.replaceState({}, '', url.pathname);
}
