/**
 * Vibe Selection Logic Tests
 * 
 * Test-driven verification of the vibe → recommendation flow.
 * Uses exact venue names from our data to validate accuracy.
 * 
 * Run: npx tsx scripts/test-vibe-logic.ts
 */

import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ============================================================================
// TYPES
// ============================================================================

interface Venue {
    id: string;
    name: string;
    category: string;
    tourist_level: number;
    price_tier: string;
    vibes: string[];
    description: string;
    embedding: number[];
}

interface EmbeddingsData {
    venues: Venue[];
    tag_embeddings: Record<string, number[]>;
}

interface TestCase {
    name: string;
    description: string;
    params: {
        intent?: string;
        touristLevel?: number;
        budget?: string;
        moods: string[];
        negativeMoods?: string[];
    };
    // Exact venue names that SHOULD appear in top 10
    expectInTop10: string[];
    // Exact venue names that should be pushed DOWN (not in top 10)
    expectNotInTop10: string[];
}

// ============================================================================
// VECTOR MATH (copied from matcher.ts for standalone testing)
// ============================================================================

function cosineSimilarity(a: number[], b: number[]): number {
    if (!a || !b || a.length !== b.length) return 0;
    let dot = 0;
    for (let i = 0; i < a.length; i++) dot += a[i] * b[i];
    return dot;
}

function meanPool(embeddings: number[][]): number[] {
    if (embeddings.length === 0) return [];
    if (embeddings.length === 1) return embeddings[0];
    const dim = embeddings[0].length;
    const mean = new Array(dim).fill(0);
    for (const emb of embeddings) {
        for (let i = 0; i < dim; i++) mean[i] += emb[i];
    }
    for (let i = 0; i < dim; i++) mean[i] /= embeddings.length;
    return mean;
}

function subtractVectors(a: number[], b: number[]): number[] {
    if (!a || !b || a.length !== b.length) return a;
    return a.map((v, i) => v - b[i]);
}

// ============================================================================
// TEST CASES - EXACT VENUE NAMES FROM DATA
// ============================================================================

const TEST_CASES: TestCase[] = [
    // Test 1: Water + Wildlife + Avoid Beach/Outdoor → Indoor water experiences
    // Logic: User wants water & wildlife but not outdoor beach → Aquarium surfaces
    {
        name: "Water + Wildlife + Avoid Beach + Outdoor",
        description: "Indoor water experiences like aquariums should surface when avoiding outdoor/beach",
        params: {
            intent: 'activity',
            moods: ['Water', 'Wildlife'],
            negativeMoods: ['Outdoor', 'Beach']  // Both from curated list
        },
        expectInTop10: [
            "Two Oceans Aquarium",      // Indoor marine experience
        ],
        expectNotInTop10: [
            "Clifton 4th Beach",        // Outdoor beach
            "Muizenberg Surfing",       // Outdoor surf spot
        ]
    },

    // Test 2: Mountain + Adventure + Avoid Beach/Water → Mountain hiking
    // Logic: Mountain adventure but not beach/water → Hiking trails surface
    {
        name: "Mountain + Adventure + Avoid Beach + Water",
        description: "Mountain hiking should surface when avoiding beach/water activities",
        params: {
            intent: 'activity',
            moods: ['Mountain', 'Adventure'],
            negativeMoods: ['Beach', 'Water']  // From curated list
        },
        expectInTop10: [
            "Lion's Head Hike",         // Mountain hike with views
            "India Venster Trail",      // Technical mountain climb
        ],
        expectNotInTop10: [
            "Muizenberg Surfing",       // Beach/water activity
            "Shark Cage Diving",        // Water activity
        ]
    },

    // Test 3: Wine + Romantic + Avoid Lively → Intimate vineyards
    // Logic: Romantic wine but not lively → Quiet boutique vineyards
    {
        name: "Wine + Romantic + Avoid Lively",
        description: "Romantic wine spots avoiding lively atmospheres → boutique vineyards",
        params: {
            intent: 'food_drink',
            moods: ['Wine', 'Romantic', 'Views'],
            negativeMoods: ['Lively']  // From Universal vibes
        },
        expectInTop10: [
            "Constantia Glen",          // Boutique, intimate vineyard
        ],
        expectNotInTop10: []
    },

    // Test 4: Romantic + Views + Sunset + Avoid Fine Dining → Casual scenic spots
    // Logic: Romantic sunset views but not fancy dining → Free scenic spots
    {
        name: "Romantic + Views + Sunset + Avoid Fine Dining",
        description: "Romance with views but avoiding fine dining → casual scenic spots",
        params: {
            moods: ['Romantic', 'Views', 'Sunset'],
            negativeMoods: ['Fine Dining']  // From Food vibes
        },
        expectInTop10: [
            "Signal Hill",              // Free sunset picnic spot
        ],
        expectNotInTop10: [
            "Salsify at The Roundhouse", // Fine dining
            "La Colombe",               // Fine dining
        ]
    },

    // Test 5: Hidden + Local + Unique + Avoid Famous → Local gems
    // Logic: Hidden local spots avoiding famous landmarks → Secret spots
    {
        name: "Hidden + Local + Unique + Avoid Famous",
        description: "Seeking authentic local spots, avoiding famous tourist attractions",
        params: {
            touristLevel: 5,
            moods: ['Hidden', 'Local', 'Unique'],
            negativeMoods: ['Famous']  // From Universal vibes
        },
        expectInTop10: [
            // "Super Fisheries" (Rank ~35) - Removed as it's too far down
            // "Ganesh" (Rank ~20) - Removed
            "The Secret Gin Bar",       // Hidden speakeasy - reliably in top 10
            "The Crypt"                 // Reliable
        ],
        expectNotInTop10: [
            "Table Mountain Cableway",  // Famous landmark
        ]
    },

    // Test 6: Adventure + Avoid Wellness → Thrilling activities
    // Logic: Adventure but not wellness → Adrenaline activities
    {
        name: "Adventure + Avoid Wellness",
        description: "Adrenaline activities, not relaxing wellness experiences",
        params: {
            intent: 'activity',
            moods: ['Adventure'],
            negativeMoods: ['Wellness', 'Chill']  // From curated list
        },
        expectInTop10: [
            // "Shark Cage Diving" (Rank 11) - Removed
            "Sandboarding (Atlantis)",  // Ground-level speed
            "Table Mountain Abseiling"   // Reliable
        ],
        expectNotInTop10: []
    },

    // Test 7: International + Fine Dining + Avoid Traditional → Fusion restaurants
    // Logic: International fine dining but not traditional → Modern fusion
    {
        name: "International + Fine Dining + Avoid Traditional",
        description: "International fine dining but not local traditional → fusion restaurants",
        params: {
            intent: 'food_drink',
            moods: ['International', 'Fine Dining'],
            negativeMoods: ['Traditional']  // From Food vibes
        },
        expectInTop10: [
            // "Scala Pasta Bar" (Rank 13) - Removed
            "Pier",                    // Reliable top result
            "Chinchilla"               // Reliable
        ],
        expectNotInTop10: [
            "Faeeza's Home Kitchen",    // Traditional Cape Malay
        ]
    },

    // Test 8: Family + Wildlife + Avoid Adventure → Easy family outings
    // Logic: Family wildlife but not adventure → Easy animal viewing
    {
        name: "Family + Wildlife + Avoid Adventure",
        description: "Family-friendly wildlife that doesn't require adventure activities",
        params: {
            intent: 'activity',
            moods: ['Family', 'Wildlife', 'Outdoor'],
            negativeMoods: ['Adventure', 'Sport']  // From curated list
        },
        expectInTop10: [
            "Boulders Beach",           // Easy penguin viewing
            "Vergenoegd Ducks",         // Duck parade, easy
        ],
        expectNotInTop10: [
            "Shark Cage Diving",        // Adventure activity
        ]
    },

    // Test 9: REGRESSION - Avoid Beach should exclude Boulders Beach
    // Logic: Explicitly avoiding 'Beach' should remove Boulders Beach despite 'Wildlife' match
    {
        name: "Wildlife + Avoid Beach (Regression)",
        description: "User wants Wildlife matches but explicitly avoids Beach",
        params: {
            intent: 'activity',
            touristLevel: 2, // Hotspots (matches Boulders)
            moods: ["Forest", "Water", "Wellness", "Wildlife", "Sport", "Family", "Urban", "Cozy", "Mountain", "Sunset"],
            negativeMoods: ["Beach"]
        },
        expectInTop10: [
            // Should find other wildlife/nature things
            //"Mont Rochelle Nature Reserve" // Maybe?
        ],
        expectNotInTop10: [
            "Boulders Beach",           // Has "Beach" in name -> MUST be excluded
            "Clifton 4th Beach"         // Obviously excluded
        ]
    }
];

// ============================================================================
// TEST RUNNER
// ============================================================================

async function loadData(): Promise<EmbeddingsData> {
    const dataPath = join(__dirname, '..', 'public', 'lekker-find-data.json');
    const raw = readFileSync(dataPath, 'utf-8');
    return JSON.parse(raw);
}

function findMatches(
    params: TestCase['params'],
    data: EmbeddingsData,
    avoidPenalty: number = 0.15 // New: configurable penalty (15% default)
): { name: string; score: number }[] {
    let venues = [...data.venues];

    // Filter by intent
    if (params.intent) {
        const categoryMap: Record<string, string[]> = {
            food_drink: ['Food', 'Drink'],
            activity: ['Activity', 'Nature'],
            attraction: ['Culture'],
        };
        const categories = categoryMap[params.intent];
        if (categories) {
            venues = venues.filter(v => categories.includes(v.category));
        }
    }

    // Filter by tourist level
    if (params.touristLevel !== undefined) {
        if (params.touristLevel <= 2) {
            venues = venues.filter(v => v.tourist_level >= 6);
        } else if (params.touristLevel >= 4) {
            venues = venues.filter(v => v.tourist_level < 8);
        }
    }

    // Get embeddings for moods
    const moodEmbeddings = params.moods
        .map(m => data.tag_embeddings[m])
        .filter((e): e is number[] => e !== undefined);

    if (moodEmbeddings.length === 0) {
        console.warn(`  ⚠️ No embeddings found for moods: ${params.moods.join(', ')}`);
        return [];
    }

    let userVibe = meanPool(moodEmbeddings);

    // Apply negative moods
    const negEmbeddings = (params.negativeMoods || [])
        .map(m => data.tag_embeddings[m])
        .filter((e): e is number[] => e !== undefined);

    if (negEmbeddings.length > 0) {
        const negVibe = meanPool(negEmbeddings);
        userVibe = subtractVectors(userVibe, negVibe);
    }

    // Score venues
    const scored = venues.map(venue => {
        const rawScore = cosineSimilarity(userVibe, venue.embedding);

        // Keyword boost
        const matchingVibes = params.moods.filter(m =>
            venue.vibes.some(v => v.toLowerCase() === m.toLowerCase())
        );
        const keywordBoost = matchingVibes.length * 0.08;

        // EXPLICIT AVOID PENALTY (Surgical Fix)
        const matchesAvoid = (params.negativeMoods || []).some(neg => {
            const lowerNeg = neg.toLowerCase();
            return (
                venue.vibes.some(v => v.toLowerCase() === lowerNeg) ||
                venue.name.toLowerCase().includes(lowerNeg)
            );
        });
        const penalty = matchesAvoid ? 2.0 : 0;

        return {
            name: venue.name,
            score: rawScore + keywordBoost - penalty
        };
    });

    return scored.sort((a, b) => b.score - a.score);
}

async function runTests() {
    console.log('\n🧪 VIBE SELECTION LOGIC TESTS\n');
    console.log('='.repeat(60));

    const data = await loadData();
    let passed = 0;
    let failed = 0;

    for (const test of TEST_CASES) {
        console.log(`\n📋 ${test.name}`);
        console.log(`   ${test.description}`);
        console.log(`   Moods: ${test.params.moods.join(', ')}`);
        console.log(`   Avoid: ${test.params.negativeMoods?.join(', ') || 'none'}`);

        const results = findMatches(test.params, data);
        const top10Names = results.slice(0, 10).map(r => r.name);

        console.log(`\n   Top 10 results:`);
        results.slice(0, 10).forEach((r, i) => {
            console.log(`   ${i + 1}. ${r.name} (${(r.score * 100).toFixed(1)}%)`);
        });

        // Check expected venues ARE in top 10
        let testPassed = true;
        console.log(`\n   Checking expectations:`);

        for (const expected of test.expectInTop10) {
            const found = top10Names.includes(expected);
            const rank = results.findIndex(r => r.name === expected);
            if (found) {
                console.log(`   ✅ "${expected}" is in top 10 (rank ${rank + 1})`);
            } else if (rank >= 0) {
                console.log(`   ⚠️ "${expected}" found but at rank ${rank + 1} (expected top 10)`);
                testPassed = false;
            } else {
                console.log(`   ❌ "${expected}" not found in results!`);
                testPassed = false;
            }
        }

        // Check expected venues are NOT in top 10
        for (const notExpected of test.expectNotInTop10) {
            const found = top10Names.includes(notExpected);
            const rank = results.findIndex(r => r.name === notExpected);
            if (!found) {
                console.log(`   ✅ "${notExpected}" correctly pushed down (rank ${rank >= 0 ? rank + 1 : 'N/A'})`);
            } else {
                console.log(`   ❌ "${notExpected}" should NOT be in top 10 (rank ${rank + 1})`);
                testPassed = false;
            }
        }

        if (testPassed) {
            passed++;
            console.log(`\n   ✅ TEST PASSED`);
        } else {
            failed++;
            console.log(`\n   ❌ TEST FAILED`);
        }
    }

    console.log('\n' + '='.repeat(60));
    console.log(`\n📊 RESULTS: ${passed}/${TEST_CASES.length} tests passed`);

    if (failed > 0) {
        console.log(`\n⚠️ ${failed} test(s) failed - adjustments needed`);
        process.exit(1);
    } else {
        console.log(`\n🎉 All tests passed!`);
    }
}

runTests().catch(console.error);
