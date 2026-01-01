import { Venue } from './matcher';

// Fallback images by category (Unsplash URLs)
export const FALLBACK_IMAGES: Record<string, string> = {
    food: 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=80',
    drink: 'https://images.unsplash.com/photo-1514362545857-3bc16549766b?auto=format&fit=crop&w=1200&q=80',
    nature: 'https://images.unsplash.com/photo-1580060839134-75a5edca2e99?auto=format&fit=crop&w=1200&q=80',
    activity: 'https://images.unsplash.com/photo-1502680390469-be75c86b636f?auto=format&fit=crop&w=1200&q=80',
    culture: 'https://images.unsplash.com/photo-1576485290814-1c72aa4bbb8e?auto=format&fit=crop&w=1200&q=80',
};

// Cache-busting for local images to stay in sync with refreshed data
const { VITE_IMAGE_VERSION, MODE, VITE_APP_VERSION } = import.meta.env;
const LOCAL_IMAGE_VERSION = VITE_IMAGE_VERSION ?? VITE_APP_VERSION ?? MODE ?? '1';
const CACHE_PARAM = 'img_v';

/**
 * Append a cache-busting query parameter to a URL.
 */
function withCacheBust(url: string): string {
    if (url.includes(`${CACHE_PARAM}=`)) {
        return url;
    }
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}${CACHE_PARAM}=${LOCAL_IMAGE_VERSION}`;
}

/**
 * Get the best available image URL for a venue.
 * Priority:
 * 1. External image_url (if valid URL)
 * 2. Local venue image based on ID (v123.jpg)
 * 3. Category fallback
 */
export function getVenueImage(venue: Venue): string {
    if (venue.image_url && (venue.image_url.startsWith('http') || venue.image_url.startsWith('/'))) {
        // Bust cache for local assets so updated data matches images
        if (venue.image_url.startsWith('/images/venues/')) {
            return withCacheBust(venue.image_url);
        }
        return venue.image_url;
    }

    // Use local image based on venue id (e.g., v0.jpg, v1.jpg)
    // The id format is "v{idx}" so we extract the number
    const idMatch = venue.id?.match(/v(\d+)/);
    if (idMatch) {
        return withCacheBust(`/images/venues/v${idMatch[1]}.jpg`);
    }

    const category = venue.category?.toLowerCase() || 'nature';
    return FALLBACK_IMAGES[category] || FALLBACK_IMAGES.nature;
}
