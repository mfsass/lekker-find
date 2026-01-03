import { Venue } from './matcher';

// Fallback images by category (Unsplash URLs)
export const FALLBACK_IMAGES: Record<string, string> = {
    food: 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=80',
    drink: 'https://images.unsplash.com/photo-1514362545857-3bc16549766b?auto=format&fit=crop&w=1200&q=80',
    nature: 'https://images.unsplash.com/photo-1580060839134-75a5edca2e99?auto=format&fit=crop&w=1200&q=80',
    activity: 'https://images.unsplash.com/photo-1502680390469-be75c86b636f?auto=format&fit=crop&w=1200&q=80',
    culture: 'https://images.unsplash.com/photo-1576485290814-1c72aa4bbb8e?auto=format&fit=crop&w=1200&q=80',
};

/**
 * Get the best available image URL for a venue.
 * Priority:
 * 1. External image_url (if valid URL)
 * 2. Local venue image based on stable ID (venue-name-hash.jpg)
 * 3. Category fallback
 */
export function getVenueImage(venue: Venue): string {
    if (venue.image_url && (venue.image_url.startsWith('http') || venue.image_url.startsWith('/'))) {
        return venue.image_url;
    }

    // Use local image based on venue id (stable name-based ID)
    // The new format is: venue-name-hash.jpg (e.g., "woolleys-tidal-pool-5561.jpg")
    if (venue.id) {
        return `/images/venues/${venue.id}.jpg`;
    }

    const category = venue.category?.toLowerCase() || 'nature';
    return FALLBACK_IMAGES[category] || FALLBACK_IMAGES.nature;
}
