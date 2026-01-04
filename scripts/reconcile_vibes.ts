
import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ============================================================================
// CURATED VIBES (Target List)
// ============================================================================
const VALID_VIBES = new Set([
    'Hidden', 'Famous', 'Romantic', 'Family', 'Views',
    'Chill', 'Lively', 'Local', 'Unique', 'Cozy',
    'Brunch', 'Fine Dining', 'Street Food', 'International', 'Traditional',
    'Wine', 'Craft Beer', 'Coffee', 'Sweet Tooth', 'Evening', 'Halaal', 'Outdoor Dining',
    'Beach', 'Mountain', 'Water', 'Forest', 'Outdoor',
    'Urban', 'Sport', 'Wellness', 'Adventure', 'Wildlife', 'Learning', 'Sunset',
    'History', 'Art', 'Music', 'Theatre', 'Museum',
    'Interactive', 'Heritage', 'Photo-Ready', 'Markets', 'Architecture'
]);

// ============================================================================
// MAPPING (Source -> Target)
// ============================================================================
const VIBE_MAPPING: Record<string, string> = {
    // Top 20 Non-Conforming
    'Scenic': 'Views',
    'Social': 'Lively',
    'Active': 'Adventure', // or Sport? Adventure covers "active" well.
    'Nature': 'Outdoor', // "Nature" isn't in valid list, "Outdoor" is closest universal fit
    'Peaceful': 'Chill',
    'Authentic': 'Local',
    'Tourist': 'Famous',
    'Food': '', // Remove (redundant with category usually)
    'Coastal': 'Water', // Could be Beach, but Water is safer
    'Panoramic': 'Views',
    'Educational': 'Learning',
    'Historic': 'History',
    'Historical': 'History',
    'Artistic': 'Art',
    'Casual': 'Chill',
    'Wild': 'Outdoor', // Generic wild -> Outdoor
    'Trendy': 'Lively', // or Unique?
    'Industrial': 'Urban',
    'Quirky': 'Unique',
    'Vibrant': 'Lively',

    // Others found in audit (Long tail guesses)
    'Secluded': 'Hidden',
    'Secret': 'Hidden',
    'Ocean-view': 'Views',
    'Walk': 'Outdoor', // Activity
    'Hike': 'Mountain', // Often mountain hikes
    'Hiking': 'Mountain',
    'Surf': 'Sport',
    'Shopping': 'Markets', // closest
    'Flea Market': 'Markets',
    'Live Music': 'Music',
    'Performance': 'Theatre',
    'Playful': 'Family', // e.g. Boulders Beach "Playful" -> Family friendly? Or Lively?
    'Atmospheric': 'Cozy', // or Romantic?
    'Victorian': 'Architecture', // or History
    'Fun': 'Lively',
    'Buzzy': 'Lively',
    'Energetic': 'Lively',
    'Busy': 'Lively',
    'Quiet': 'Chill',
    'Serene': 'Chill',
    'Relaxed': 'Chill',
    'Classy': 'Fine Dining', // implies upscale
    'Fancy': 'Fine Dining',
    'Upscale': 'Fine Dining',
    'VIP': 'Fine Dining',
    'Posh': 'Fine Dining',
    'Stylish': 'Unique', // or Urban?
    'Roots': 'Local',
    'Home-style': 'Traditional',
    'Groups': 'Lively', // Social/Groups
    'Private': 'Hidden',
    'Undiscovered': 'Hidden',
    'Modern': 'Urban',
    'Easy-going': 'Chill',
    'Date-night': 'Romantic',
    'Cute': 'Romantic',
    'Magic': 'Unique',
    'Different': 'Unique',
    'Creative': 'Art',
    'Special': 'Unique',
    'Drink': '', // Redundant
    'Drinks': '',
    'Alcohol': '',
    'Bar': 'Evening',
    'Pub': 'Lively',
    'Cocktails': 'Evening',
    'Seaside': 'Water',
    'Ocean': 'Water',
    'Sea': 'Water',
    'River': 'Water',
    'Dam': 'Water',
    'Lake': 'Water',
    'Swimming': 'Water',
    'Pool': 'Water',
    'Running': 'Sport',
    'Cycling': 'Sport',
    'Biking': 'Sport',
    'Gym': 'Sport',
    'Fitness': 'Sport',
    'Yoga': 'Wellness',
    'Spa': 'Wellness',
    'Massage': 'Wellness',
    'Relaxing': 'Wellness', // or Chill? Wellness fits spa context
    'Animals': 'Wildlife',
    'Birds': 'Wildlife',
    'Penguins': 'Wildlife',
    'Safari': 'Wildlife',
    'Game Drive': 'Wildlife',
    'Zoo': 'Wildlife',
    'Aquarium': 'Wildlife',
    'Paddock': 'Wildlife',
    'Vineyard': 'Wine',
    'Wine Farm': 'Wine',
    'Tasting': 'Wine', // usually
    'Beer': 'Craft Beer',
    'Brewery': 'Craft Beer',
    'Taproom': 'Craft Beer',
    'Cafe': 'Coffee',
    'Coffee Shop': 'Coffee',
    'Roastery': 'Coffee',
    'Bakery': 'Sweet Tooth',
    'Dessert': 'Sweet Tooth',
    'Ice Cream': 'Sweet Tooth',
    'Chocolate': 'Sweet Tooth',
    'Halal': 'Halaal', // Spelling fix
    'Muslim-friendly': 'Halaal',
    'Sunset-view': 'Sunset',
    'Sundowners': 'Sunset',
    'Golden Hour': 'Sunset',
    'Culture': 'History', // or Heritage
    'Cultural': 'Heritage',
    'Tour': 'Learning',
    'Guided': 'Learning',
    'Workshop': 'Learning',
    'Class': 'Learning',
    'Stroll': 'Outdoor',
    'Gallery': 'Art',
    'Exhibition': 'Art',
    'Stage': 'Theatre',
    'Concert': 'Music',
    'Gig': 'Music',
    'Show': 'Theatre',
    'Cinema': 'Theatre', // approximation
    'Movie': 'Theatre',
    'Photography': 'Photo-Ready',
    'Instagram': 'Photo-Ready',
    'Insta-worthy': 'Photo-Ready',
    'Photogenic': 'Photo-Ready',
    'Shop': 'Markets', // or generic?
    'Store': 'Markets',
    'Crafts': 'Markets',
    'Souvenirs': 'Markets',
    'Design': 'Art', // or Architecture
    'Building': 'Architecture',
    'Monument': 'History',
    'Landmark': 'Famous',
    'Iconic': 'Famous',

    // Pass 2 Mappings (Refinement)
    'Musical': 'Music',
    'Intimate': 'Cozy',
    'Artisanal': 'Local',
    'Thrilling': 'Adventure',
    'Natural': 'Outdoor',
    'Chic': 'Unique', // or Lively
    'Sophisticated': 'Fine Dining',
    'Calm': 'Chill',
    'Sweet': 'Sweet Tooth',
    'Retro': 'Unique',
    'Italian': 'International',
    'Laid-back': 'Chill',
    'Lush': 'Outdoor',
    'Minimalist': 'Unique',
    'Bustling': 'Lively',
    'Adventurous': 'Adventure',
    'Elegant': 'Fine Dining',
    'Grungy': 'Urban',
    'Military': 'History',
};

// ============================================================================
// MAIN SCRIPT
// ============================================================================

interface Venue {
    id: string;
    name: string;
    vibes: string[];
}

interface Data {
    venues: Venue[];
    [key: string]: any; // preserve other keys
}

function reconcile() {
    console.log('🔄 RECONCILING VIBES...\n');

    try {
        const dataPath = join(__dirname, '..', 'public', 'lekker-find-data.json');
        const raw = readFileSync(dataPath, 'utf-8');
        const data: Data = JSON.parse(raw);

        let totalChanges = 0;
        let venuesUpdated = 0;

        data.venues.forEach(venue => {
            const originalVibes = new Set(venue.vibes);
            const newVibes = new Set<string>();
            let changed = false;

            originalVibes.forEach(v => {
                const normalized = v.trim();

                if (VALID_VIBES.has(normalized)) {
                    // Current vibe is valid, keep it
                    newVibes.add(normalized);
                } else if (VIBE_MAPPING[normalized] !== undefined) {
                    // Found a mapping
                    const mapped = VIBE_MAPPING[normalized];
                    if (mapped) { // If mapped to "" (empty string), it's removed
                        newVibes.add(mapped);
                    }
                    changed = true;
                    totalChanges++;
                } else {
                    // No mapping, keep original but warn? 
                    // For now, let's keep it to avoid losing data, 
                    // but we know it won't work with filters.
                    // Actually, better to Remove or Keep? 
                    // User said "regenerate... narrowed vibe selection".
                    // Let's KEEP it for now to avoid aggressive deletion, 
                    // but usually we'd want to drop it if we're strict.
                    // Given the goal is "consolidate", keeping noise is bad.
                    // BUT dropping it might leave venue with 0 vibes.
                    // Let's KEEP UNMAPPED vibes for manual review, but Log them.
                    newVibes.add(normalized);
                }
            });

            // Specific "Rescue" Logic for 0-vibe venues (implied from Name/Category?)
            // This is "Pattern Matching" mentioned in Hybrid Search best practices
            if (newVibes.size === 0 || Array.from(newVibes).every(v => !VALID_VIBES.has(v))) {
                const lowerName = venue.name.toLowerCase();
                if (lowerName.includes('beach')) newVibes.add('Beach');
                if (lowerName.includes('market')) newVibes.add('Markets');
                if (lowerName.includes('farm')) newVibes.add('Outdoor');
                if (lowerName.includes('wine')) newVibes.add('Wine');
                if (lowerName.includes('bar')) newVibes.add('Evening');
                if (lowerName.includes('cafe')) newVibes.add('Coffee');
            }

            // Deduplicate and save
            if (changed || newVibes.size !== venue.vibes.length) {
                // Check if the set of strings is actually different
                const sortedNew = Array.from(newVibes).sort();
                const sortedOld = venue.vibes.sort();
                if (JSON.stringify(sortedNew) !== JSON.stringify(sortedOld)) {
                    venue.vibes = sortedNew;
                    venuesUpdated++;
                }
            }
        });

        console.log(`Updated ${venuesUpdated} venues.`);
        console.log(`Total vibe replacements/cleanups: ${totalChanges}`);

        // Write back
        // Format with 2 spaces to match existing file roughly (or prettify)
        writeFileSync(dataPath, JSON.stringify(data, null, 2));
        console.log('✅ Updated public/lekker-find-data.json');

    } catch (err) {
        console.error('Error reconciling:', err);
    }
}

reconcile();
