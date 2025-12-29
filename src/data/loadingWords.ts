
// Base lists for tourist levels (Vibe/Slang/Language)

// Tourist: Welcoming, Youthful, Distinctly South African
const WORDS_TOURIST = [
    "Lekker Vibes", "Mzansi Magic", "The Mother City", "Cape Town Calling",
    "Braai Time", "Sundowners", "Ubuntu Spirit", "Summer Vibes",
    "Rainbow Nation", "Local Flava", "Good Gees", "SA Soul",
    "Table Mountain", "Coastal Dreams", "African Beats"
];

// Local: Authentic Youth Slang, "Inside" Language
const WORDS_LOCAL = [
    "Aweh", "Sho", "Hosh", "My Bru", "Gees", "Eish",
    "Now Now", "Just Now", "Wena", "Chommie", "Howzit",
    "Satafrika", "Ja Nee", "Vibez", "Molo", "Sharp Sharp", "Yoh",
    "Haibo", "Lekker Laanie", "Smaak", "Jislaaik", "Boet"
];

// Intent-specific lists (Youthful & Local Context)
const INTENT_WORDS: Record<string, string[]> = {
    food: [
        "Proper Chow", "Gatsbies", "Shisa Nyama", "Koesisters",
        "Slap Chips", "Snoek Braai", "Biltong", "Ouma Rusks",
        "Feasts", "Something Lekker", "Street Food", "Bunny Chow"
    ],
    drink: [
        "A Dop", "Cold Ones", "Klippies", "Sundowners",
        "Cheers Bru", "Craft Brews", "Ice Cold", "Jäger Bombs",
        "Brannas & Coke", "Liquid Courage", "Thirst Trap", "Brewskis"
    ],
    activity: [
        "A Jol", "Groove", "The Mission", "Action", "Adrenaline",
        "Good Times", "Thrills", "Adventure", "Making Memories",
        "Roadtrip", "Epic Vibes", "Pure Fire"
    ],
    nature: [
        "The Berg", "Ocean Views", "Fynbos", "Fresh Air",
        "Vitamin Sea", "Wilderness", "Kelp Forests", "Penguins",
        "Golden Hour", "Sea Breeze", "Mountain Magic", "Wild Coast"
    ],
    culture: [
        "Kasi Vibes", "Roots", "Heritage", "Stories", "12 Languages",
        "Kaapse Klopse", "Ubuntu", "Art & Soul", "Rhythm", "Deep Context",
        "Local Legends", "Township Tales"
    ],
    any: [
        "Hidden Gems", "Lekker Discovery", "Surprise", "Exploring",
        "The Journey", "Mzansi Secrets", "Everything Lekker", "Pure Magic",
        "Your Spot", "The Real Deal"
    ]
};

// "Smart" modifiers or phrases that feel personal/unique/youthful
const SMART_PHRASES = [
    "Your Vibe", "The Perfect Spot", "Curated For You",
    "Something Special", "Local Intel", "Trust The Process",
    "Chef's Kiss", "You're Gonna Love This", "Insider Tip",
    "Pure Gold", "Hand-Picked"
];

export const getLoadingWords = (level: number | null, intent: string | null): string[] => {
    // 1. Determine base 'Vibe' list
    let baseList: string[] = [];

    if (!level || level <= 2) {
        baseList = WORDS_TOURIST;
    } else if (level >= 4) {
        baseList = WORDS_LOCAL;
    } else {
        // Balanced: Mix of tourist nice + local spice
        baseList = [...WORDS_TOURIST.slice(0, 5), ...WORDS_LOCAL.slice(0, 5)];
    }

    // 2. Determine 'Intent' list
    const safeIntent = (intent && intent in INTENT_WORDS) ? intent : 'any';
    const intentList = INTENT_WORDS[safeIntent];

    // 3. Build selection ensuring no duplicates
    const shuffledIntent = [...intentList].sort(() => 0.5 - Math.random());
    const shuffledBase = [...baseList].sort(() => 0.5 - Math.random());
    const shuffledSmart = [...SMART_PHRASES].sort(() => 0.5 - Math.random());

    // Construct journey with uniqueness check
    const usedWords = new Set<string>();
    const curatedSelection: string[] = [];

    const addWord = (word: string) => {
        if (!usedWords.has(word)) {
            curatedSelection.push(word);
            usedWords.add(word);
        }
    };

    // Vibe -> Intent -> Intent -> Local Flavor -> Conclusion
    addWord(shuffledBase[0] || 'Lekker Vibes');
    addWord(shuffledIntent[0] || shuffledBase[1] || 'Adventure');
    addWord(shuffledIntent[1] || shuffledBase[2] || 'Good Times');
    addWord(shuffledBase[3] || shuffledIntent[2] || 'The Mother City');
    addWord(shuffledSmart[0] || 'Your Vibe');

    return curatedSelection;
};
