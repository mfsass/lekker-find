import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config({ path: path.join(process.cwd(), '.env') });

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DATA_FILE = path.join(__dirname, '../public/lekker-find-data.json');
const PUBLIC_DIR = path.join(__dirname, '../public');
const PHOTOS_BASE_URL = 'https://places.googleapis.com/v1';
const API_KEY = process.env.VITE_GOOGLE_MAPS_API_KEY || process.env.MAPS_API_KEY;

if (!API_KEY) {
    console.error('Error: MAPS_API_KEY or VITE_GOOGLE_MAPS_API_KEY not found in .env');
    process.exit(1);
}

async function fetchPlacePhoto(placeId) {
    // 1. Get Place Details (Photos)
    const detailsUrl = `${PHOTOS_BASE_URL}/places/${placeId}?fields=photos&key=${API_KEY}`;

    // Mandated Field Mask by Google Places API (New)
    // Rule: X-Goog-FieldMask: places.photos
    const headers = {
        'X-Goog-FieldMask': 'places.photos',
        'Content-Type': 'application/json'
    };

    try {
        const response = await fetch(detailsUrl, { headers });
        if (!response.ok) {
            throw new Error(`Details API Error: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();

        if (!data.photos || data.photos.length === 0) {
            console.warn(`No photos found for place_id: ${placeId}`);
            return null;
        }

        // 2. Construct Photo Media URL (skip download request if we just want the link, but instructions say duplicate image file locally)
        // We will download the first photo.
        // Format: https://places.googleapis.com/v1/{name}/media?key=API_KEY&maxHeightPx=...&maxWidthPx=...
        const photoName = data.photos[0].name; // resource name like "places/PLACE_ID/photos/PHOTO_ID"
        const downloadUrl = `${PHOTOS_BASE_URL}/${photoName}/media?key=${API_KEY}&maxHeightPx=1600&maxWidthPx=1600`;

        return {
            downloadUrl,
            attribution: data.photos[0].authorAttributions?.[0]?.displayName || 'Google Maps'
        };

    } catch (error) {
        console.error(`Failed to fetch details for ${placeId}:`, error.message);
        return null;
    }
}

async function downloadImage(url, tempDest) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Image Download Error: ${response.status} ${response.statusText}`);
    }
    const arrayBuffer = await response.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    fs.writeFileSync(tempDest, buffer);
}

// Main execution
(async () => {
    try {
        const rawData = fs.readFileSync(DATA_FILE, 'utf8');
        const data = JSON.parse(rawData);
        let updatedCount = 0;

        console.log(`Scanning ${data.venues.length} venues...`);

        for (const venue of data.venues) {
            // Normalize path
            const relPath = venue.image_url.startsWith('/') ? venue.image_url.slice(1) : venue.image_url;
            const absolutePath = path.join(PUBLIC_DIR, relPath);

            if (!fs.existsSync(absolutePath)) {
                console.log(`\n[Missing] ${venue.name} (${venue.id})`);
                console.log(` - Expected at: ${absolutePath}`);

                if (!venue.place_id) {
                    console.warn(' - Skipping: No place_id available.');
                    continue;
                }

                console.log(' - Fetching from Google Places API...');
                const photoData = await fetchPlacePhoto(venue.place_id);

                if (photoData) {
                    // Create directory if it doesn't exist (e.g. venues/)
                    const dir = path.dirname(absolutePath);
                    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

                    await downloadImage(photoData.downloadUrl, absolutePath);

                    // Update attribution if possible (optional, but good practice)
                    if (photoData.attribution) {
                        venue.image_attribution = photoData.attribution;
                    }

                    console.log(' - FIXED: Image downloaded.');
                    updatedCount++;
                } else {
                    console.warn(' - FAILED: Could not retrieve photo from API.');
                }
            }
        }

        if (updatedCount > 0) {
            console.log(`\nWriting updated data (${updatedCount} changes)...`);
            fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2), 'utf8');
            console.log('Done.');
        } else {
            console.log('\nNo changes made.');
        }

    } catch (e) {
        console.error('Fatal Error:', e);
    }
})();
