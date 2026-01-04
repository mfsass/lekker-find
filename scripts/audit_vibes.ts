
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ============================================================================
// CURATED VIBES (Copied from src/data/vibes.ts)
// ============================================================================

const UNIVERSAL_VIBES = [
    'Hidden', 'Famous', 'Romantic', 'Family', 'Views',
    'Chill', 'Lively', 'Local', 'Unique', 'Cozy'
] as const;

const FOOD_VIBES = [
    'Brunch', 'Fine Dining', 'Street Food', 'International', 'Traditional',
    'Wine', 'Craft Beer', 'Coffee', 'Sweet Tooth', 'Evening', 'Halaal', 'Outdoor Dining'
] as const;

const ACTIVITY_VIBES = [
    'Beach', 'Mountain', 'Water', 'Forest', 'Outdoor',
    'Urban', 'Sport', 'Wellness', 'Adventure', 'Wildlife', 'Learning', 'Sunset'
] as const;

const ATTRACTION_VIBES = [
    'History', 'Art', 'Music', 'Theatre', 'Museum',
    'Interactive', 'Heritage', 'Photo-Ready', 'Markets', 'Architecture'
] as const;

const ALL_CURATED_VIBES = new Set([
    ...UNIVERSAL_VIBES,
    ...FOOD_VIBES,
    ...ACTIVITY_VIBES,
    ...ATTRACTION_VIBES
]);

// ============================================================================
// AUDIT
// ============================================================================

interface Venue {
    id: string;
    name: string;
    vibes: string[];
}

interface Data {
    venues: Venue[];
}

function runAudit() {
    console.log('🔍 AUDITING VIBE QUALITY...\n');

    try {
        const dataPath = join(__dirname, '..', 'public', 'lekker-find-data.json');
        const raw = readFileSync(dataPath, 'utf-8');
        const data: Data = JSON.parse(raw);

        console.log(`Loaded ${data.venues.length} venues.`);
        console.log(`Curated Vibe List contains ${ALL_CURATED_VIBES.size} valid vibes.\n`);

        const allVibeCounts: Record<string, number> = {};
        const unknownVibes: Record<string, number> = {};
        const venuesWithZeroValid: string[] = [];

        data.venues.forEach(venue => {
            let validCount = 0;
            venue.vibes.forEach(v => {
                // Normalize for counting
                const normalized = v.trim();
                allVibeCounts[normalized] = (allVibeCounts[normalized] || 0) + 1;

                // Check strict match (case sensitive usually, but let's check exact string)
                if (ALL_CURATED_VIBES.has(v as any)) {
                    validCount++;
                } else {
                    unknownVibes[normalized] = (unknownVibes[normalized] || 0) + 1;
                }
            });

            if (validCount === 0) {
                venuesWithZeroValid.push(venue.name);
            }
        });

        const totalUniqueVibes = Object.keys(allVibeCounts).length;
        const totalUnknownUnique = Object.keys(unknownVibes).length;

        console.log(`Total Unique Vibes in Data: ${totalUniqueVibes}`);
        console.log(`Total "Unknown" Vibes (not in curated list): ${totalUnknownUnique}`);
        console.log(`Venues with 0 valid vibes: ${venuesWithZeroValid.length}`);

        if (venuesWithZeroValid.length > 0) {
            console.log('Examples of venues with 0 valid vibes:');
            venuesWithZeroValid.slice(0, 5).forEach(v => console.log(` - ${v}`));
        }

        console.log('\n--- TOP 20 NON-CONFORMING VIBES ---');
        console.log('(These need mapping or adding to curated list)');

        const sortedUnknown = Object.entries(unknownVibes)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 20);

        sortedUnknown.forEach(([vibe, count]) => {
            console.log(` - "${vibe}": ${count} occurrences`);
        });

    } catch (err) {
        console.error('Error running audit:', err);
    }
}

runAudit();
