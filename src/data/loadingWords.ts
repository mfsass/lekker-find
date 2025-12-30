
// Base lists for personality levels (Tourist/Vibe/Local)

// Tourist/Welcoming: Distinctly South African but easy to grasp
const WORDS_TOURIST = [
    "Lekker Vibes", "Mzansi Magic", "The Mother City", "Cape Town Calling",
    "Braai Time", "Sundowners", "Ubuntu Spirit", "Summer Sunsets",
    "Rainbow Nation", "Local Flava", "Good Gees", "SA Soul",
    "Table Mountain Magic", "Coastal Dreams", "African Beats",
    "Garden Route Gems", "Winelands Wonder", "Bushveld Breeze"
];

// Local: Authentic Slang & Relatable South Africanisms
const WORDS_LOCAL = [
    "Aweh My Bru", "Sho! Check this", "Hosh!", "Proper Gees", "Eish! One sec",
    "Now Now...", "Just Now...", "Wena!", "Chommie Vibes", "Howzit!",
    "Satafrika", "Ja Nee", "Sharp Sharp", "Yoh!",
    "Haibo!", "Lekker Laanie", "Smaak it", "Jislaaik!", "Boet",
    "Robot is Green", "Taxis are Flying", "Loadshedding? Never.",
    "Bakkie is Packed", "Vellies are On"
];

// Intent-specific lists (Personalized Context)
const INTENT_WORDS: Record<string, string[]> = {
    food: [
        "Proper Braai Chow", "Bunny Chow Search", "Shisa Nyama Vibes", "Koesisters & Coffee",
        "Slap Chips & Vinegar", "Snoek Braai Magic", "Biltong & Droëwors", "Ouma Rusks",
        "Feasts", "Something Lekker", "Street Food Gems", "Milk Tart Dreams"
    ],
    drink: [
        "A Proper Dop", "Ice Cold Ones", "Brannas & Coke", "Sundowner Gin",
        "Cheers My Bru", "Craft Brews", "Ice Cold Savanna", "Springbokkie Shots",
        "Klipdrift on Ice", "Liquid Courage", "Stoney Ginger Beer", "Rooibos Tea"
    ],
    activity: [
        "A Proper Jol", "Grooving in Kasi", "The Mission", "Hiking Lion's Head",
        "Surfing Muizenberg", "Good Times", "Making Memories",
        "Karoo Roadtrip", "Epic Vibes", "Pure Fire"
    ],
    nature: [
        "The Berg is Calling", "Ocean Views", "Fynbos Magic", "Fresh Air",
        "Vitamin Sea", "Wild Coast", "Whale Watching", "Penguins & Kelp",
        "Golden Hour at Signal Hill", "Sea Breeze", "Mountain Magic", "Bushveld Bliss"
    ],
    culture: [
        "Kasi Spirit", "Heritage Day Every Day", "12 Official Languages", "Stories",
        "Kaapse Klopse Beats", "Ubuntu", "Art & Soul", "Rhythm", "Deep Context",
        "Local Legends", "Township Tales", "The Real Mzansi"
    ],
    any: [
        "Hidden Gems", "Lekker Discovery", "Checking the Gogo's recipe", "Gathering the Gees",
        "The Journey", "Mzansi Secrets", "Everything Lekker", "Pure Magic",
        "Polishing the Safari wheels", "The Real Deal"
    ]
};

// Personality Phrases
const SMART_PHRASES = [
    "Finding your Vibe...", "The Perfect Spot...", "Curated For You...",
    "Something Special...", "Local Intel...", "Trust The Process...",
    "Chef's Kiss...", "You're Gonna Love This...", "Insider Tip...",
    "Nearly there, my Bru...", "Finding the real Magic..."
];

export const getLoadingWords = (level: number | null, intent: string | null): string[] => {
    // 1. Determine base personality list
    let baseList: string[] = [];

    if (!level || level <= 2) {
        baseList = WORDS_TOURIST;
    } else if (level >= 4) {
        baseList = WORDS_LOCAL;
    } else {
        baseList = [...WORDS_TOURIST.slice(0, 8), ...WORDS_LOCAL.slice(0, 8)];
    }

    // 2. Determine 'Intent' list
    const safeIntent = (intent && intent in INTENT_WORDS) ? intent : 'any';
    const intentList = INTENT_WORDS[safeIntent];

    // 3. Build selection (target 12 words for a diverse journey)
    const shuffledIntent = [...intentList].sort(() => 0.5 - Math.random());
    const shuffledBase = [...baseList].sort(() => 0.5 - Math.random());
    const shuffledSmart = [...SMART_PHRASES].sort(() => 0.5 - Math.random());

    const usedWords = new Set<string>();
    const curatedSelection: string[] = [];

    const addWord = (word: string) => {
        if (!usedWords.has(word) && curatedSelection.length < 12) {
            curatedSelection.push(word);
            usedWords.add(word);
        }
    };

    // Construct a 12-word journey:

    // Mix them up in a structured but diverse way
    for (let i = 0; i < 4; i++) {
        if (shuffledBase[i]) addWord(shuffledBase[i]);
        if (shuffledIntent[i]) addWord(shuffledIntent[i]);
        if (shuffledSmart[i]) addWord(shuffledSmart[i]);
    }

    // Fill to 12 if we missed any due to duplicates or short lists
    let i = 4;
    while (curatedSelection.length < 12) {
        if (shuffledBase[i]) addWord(shuffledBase[i]);
        else if (shuffledIntent[i]) addWord(shuffledIntent[i]);
        else if (shuffledSmart[i]) addWord(shuffledSmart[i]);
        else addWord("Sharp Sharp!"); // Fallback
        i++;
    }

    return curatedSelection;
};
