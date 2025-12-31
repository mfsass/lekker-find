/**
 * Remove Duplicate Venues Script (Using Embeddings + Manual List)
 * 
 * This script finds duplicate venues using cosine similarity of embeddings
 * to detect semantically similar entries, plus a manual list for name-based
 * duplicates that embeddings miss. Removes duplicates from both JSON and CSV.
 * 
 * Usage: 
 *   node scripts/remove-duplicates.cjs --find          # Find duplicates
 *   node scripts/remove-duplicates.cjs --dry-run       # Preview removal
 *   node scripts/remove-duplicates.cjs                 # Execute removal
 */

const fs = require('fs');
const path = require('path');

const FIND_ONLY = process.argv.includes('--find');
const DRY_RUN = process.argv.includes('--dry-run');

// Similarity threshold - venues above this are considered potential duplicates
const SIMILARITY_THRESHOLD = 0.92;

// Manual duplicates that embeddings miss (e.g., different categories but same place)
const MANUAL_DUPLICATES = [
    'Kloof Corner Hike', // Duplicate of "Kloof Corner" - same location, different category
];

const JSON_PATH = path.join(__dirname, '..', 'public', 'lekker-find-data.json');
const CSV_PATH = path.join(__dirname, '..', 'data-262-2025-12-26.csv');

/**
 * Calculate cosine similarity between two embedding vectors
 */
function cosineSimilarity(a, b) {
    if (a.length !== b.length) return 0;

    let dotProduct = 0;
    let normA = 0;
    let normB = 0;

    for (let i = 0; i < a.length; i++) {
        dotProduct += a[i] * b[i];
        normA += a[i] * a[i];
        normB += b[i] * b[i];
    }

    if (normA === 0 || normB === 0) return 0;
    return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

/**
 * Find all duplicate pairs using embedding similarity
 */
function findDuplicates(venues) {
    console.log('\n🔍 Scanning for duplicates using embedding similarity...');
    console.log(`   Threshold: ${SIMILARITY_THRESHOLD} (${(SIMILARITY_THRESHOLD * 100).toFixed(0)}% similar)`);

    const duplicates = [];

    for (let i = 0; i < venues.length; i++) {
        for (let j = i + 1; j < venues.length; j++) {
            const similarity = cosineSimilarity(venues[i].embedding, venues[j].embedding);

            if (similarity >= SIMILARITY_THRESHOLD) {
                duplicates.push({
                    venue1: { id: venues[i].id, name: venues[i].name, category: venues[i].category },
                    venue2: { id: venues[j].id, name: venues[j].name, category: venues[j].category },
                    similarity: similarity,
                    // Keep the first occurrence, remove the second
                    keep: venues[i].name,
                    remove: venues[j].name
                });
            }
        }
    }

    // Sort by similarity descending
    duplicates.sort((a, b) => b.similarity - a.similarity);

    return duplicates;
}

/**
 * Display found duplicates
 */
function displayDuplicates(duplicates) {
    if (duplicates.length === 0) {
        console.log('\n✅ No duplicates found above threshold!');
        return;
    }

    console.log(`\n⚠️  Found ${duplicates.length} potential duplicate pair(s):\n`);

    duplicates.forEach((dup, idx) => {
        const pct = (dup.similarity * 100).toFixed(1);
        console.log(`${idx + 1}. [${pct}% similar]`);
        console.log(`   KEEP:   ${dup.venue1.id} - "${dup.venue1.name}" (${dup.venue1.category})`);
        console.log(`   REMOVE: ${dup.venue2.id} - "${dup.venue2.name}" (${dup.venue2.category})`);
        console.log('');
    });
}

function removeFromJSON(namesToRemove) {
    console.log('\n📋 Processing JSON file...');

    const jsonData = JSON.parse(fs.readFileSync(JSON_PATH, 'utf-8'));
    const originalCount = jsonData.venues.length;

    const lowerNamesToRemove = namesToRemove.map(n => n.toLowerCase());

    const removedVenues = [];
    jsonData.venues = jsonData.venues.filter(venue => {
        const shouldRemove = lowerNamesToRemove.includes(venue.name.toLowerCase());
        if (shouldRemove) {
            removedVenues.push({ id: venue.id, name: venue.name });
        }
        return !shouldRemove;
    });

    const newCount = jsonData.venues.length;

    console.log(`   Original venues: ${originalCount}`);
    console.log(`   Removed venues: ${removedVenues.length}`);
    removedVenues.forEach(v => console.log(`     - ${v.id}: ${v.name}`));
    console.log(`   New count: ${newCount}`);

    if (!DRY_RUN && !FIND_ONLY) {
        // Re-index venue IDs to maintain sequential order
        jsonData.venues = jsonData.venues.map((venue, index) => ({
            ...venue,
            id: `v${index}`
        }));

        fs.writeFileSync(JSON_PATH, JSON.stringify(jsonData));
        console.log('   ✅ JSON file updated');
    } else {
        console.log('   🔍 Preview only - no changes made');
    }

    return removedVenues;
}

function removeFromCSV(namesToRemove) {
    console.log('\n📋 Processing CSV file...');

    const csvContent = fs.readFileSync(CSV_PATH, 'utf-8');
    const lines = csvContent.split('\n');
    const header = lines[0];
    const dataLines = lines.slice(1).filter(line => line.trim());

    const originalCount = dataLines.length;
    const lowerNamesToRemove = namesToRemove.map(n => n.toLowerCase());

    const removedLines = [];
    const filteredLines = dataLines.filter(line => {
        // CSV first column is Name - handle quoted values
        let name = line.split(',')[0];
        // Remove quotes if present
        if (name.startsWith('"') && name.includes('"')) {
            name = name.slice(1, name.indexOf('"', 1));
        }

        const shouldRemove = lowerNamesToRemove.includes(name.toLowerCase());
        if (shouldRemove) {
            removedLines.push(name);
        }
        return !shouldRemove;
    });

    const newCount = filteredLines.length;

    console.log(`   Original rows: ${originalCount}`);
    console.log(`   Removed rows: ${removedLines.length}`);
    removedLines.forEach(name => console.log(`     - ${name}`));
    console.log(`   New count: ${newCount}`);

    if (!DRY_RUN && !FIND_ONLY) {
        const newCsvContent = [header, ...filteredLines].join('\n');
        fs.writeFileSync(CSV_PATH, newCsvContent);
        console.log('   ✅ CSV file updated');
    } else {
        console.log('   🔍 Preview only - no changes made');
    }

    return removedLines;
}

function main() {
    console.log('🧹 Duplicate Venue Removal Script (Embedding-based)');
    console.log('====================================================');

    if (FIND_ONLY) {
        console.log('📋 MODE: Find duplicates only');
    } else if (DRY_RUN) {
        console.log('📋 MODE: Dry run (preview changes)');
    } else {
        console.log('📋 MODE: Execute removal');
    }

    // Load JSON data
    const jsonData = JSON.parse(fs.readFileSync(JSON_PATH, 'utf-8'));
    console.log(`\n📊 Loaded ${jsonData.venues.length} venues`);

    // Find duplicates using embeddings
    const duplicates = findDuplicates(jsonData.venues);
    displayDuplicates(duplicates);

    // Add manual duplicates
    if (MANUAL_DUPLICATES.length > 0) {
        console.log(`\n📝 Manual duplicates to remove: ${MANUAL_DUPLICATES.length}`);
        MANUAL_DUPLICATES.forEach(name => console.log(`   - ${name}`));
    }

    // Combine embedding-found + manual duplicates
    const embeddingNames = duplicates.map(d => d.remove);
    const allNamesToRemove = [...new Set([...embeddingNames, ...MANUAL_DUPLICATES])];

    if (FIND_ONLY) {
        console.log(`\n📊 Total duplicates to remove: ${allNamesToRemove.length}`);
        return;
    }

    if (allNamesToRemove.length === 0) {
        console.log('\n✅ No duplicates to remove!');
        return;
    }

    console.log('\n🗑️  All venues to be removed:');
    allNamesToRemove.forEach(name => console.log(`   - ${name}`));

    const jsonRemoved = removeFromJSON(allNamesToRemove);
    const csvRemoved = removeFromCSV(allNamesToRemove);

    console.log('\n====================================================');
    console.log('📊 Summary:');
    console.log(`   JSON venues removed: ${jsonRemoved.length}`);
    console.log(`   CSV rows removed: ${csvRemoved.length}`);

    if (DRY_RUN) {
        console.log('\n💡 Run without --dry-run to apply changes');
    } else if (!FIND_ONLY) {
        console.log('\n✅ All duplicates removed successfully!');
    }
}

main();
