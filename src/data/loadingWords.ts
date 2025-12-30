// Base lists for personality levels (Tourist/Vibe/Local)

// Tourist/Welcoming: Distinctly Cape Town but safe
const WORDS_TOURIST = [
    "Lekker Vibes", "Mother City", "Table Mountain", "the Wind",
    "Braai Time", "Sundowners", "Ubuntu Spirit", "Beautiful Sunsets",
    "Rainbow Nation", "Local Flavour", "the Gees", "Summer Season",
    "12 Official Languages", "the Cold Water", "African Beats",
    "Wine Farm Days", "The Big Five", "Wine Farms"
];

// Local: Authentic Cape Town Slang (The real deal)
const WORDS_LOCAL = [
    "Aweh My Bru", "Duidelik!", "Hosh!", "Proper Gees", "Eish! One sec",
    "Now Now...", "Just Now...", "Wena!", "Chommie", "Howzit!",
    "Is Ja!", "Ja Nee", "Sharp Sharp", "Yoh!",
    "Haibo!", "Lekker Laanie", "Stiek Uit", "Jislaaik!", "Boet",
    "Robot is Green", "Gaatjie is shouting", "Loadshedding... again",
    "Bakkie is Packed", "Vellies and Vibes", "Mos"
];

// Intent-specific lists (Personalized Context)
const INTENT_WORDS: Record<string, string[]> = {
    food: [
        "Hunting a Gatsby", "Shisa Nyama Vibes", "Sunday Koesisters", // Koesisters (Spicy/Coconut) > Koeksisters in CPT
        "Slap Chips & Vinegar", "Snoek Braai Magic", "Biltong Stash",
        "Ouma Rusks", "Something Lekker", "Kalky's Fish & Chips",
        "Melktert Mission", "Spice Route", "Boerewors Rolls"
    ],
    drink: [
        "A Proper Dop", "Ice Cold Ones", "Brannas & Coke", "Gin & Tonic",
        "Cheers My Bru", "Craft Beers", "Ice Cold Savanna", "Springbokkies",
        "Klipdrift Premium", "Liquid Courage", "Stoney Ginger Beer", "Wine Tasting"
    ],
    activity: [
        "A Proper Jol", "Grooving", "The Mission", "Hiking Lion's Head",
        "Surfing Muizenberg", "Catching a Tan", "Making Memories",
        "Chapman's Peak Drive", "Epic Vibes", "Pure Fire", "Promenade Walk"
    ],
    nature: [
        "The Mountain is Out", // CPT specific: We look to see if the mountain is clear of clouds
        "Ocean Views", "Fynbos Smell", "Fresh Air",
        "Vitamin Sea", "West Coast Flowers", "Whale Watching", "Penguins at Boulders",
        "Signal Hill Sunset", "South Easter Wind", "Kloofing", "Forest Vibes"
    ],
    culture: [
        "District Six Stories", "Heritage", "11 Languages", "Local Legends",
        "Minstrels Parade", "Ubuntu", "Art & Soul", "Rhythm",
        "First Thursdays", "Township Tales", "Mzansi for sure", "Deep Roots"
    ],
    any: [
        "Hidden Gems", "Lekker Discovery", "Checking the Gogo's recipe", "Gathering the Gees",
        "The Journey", "Mzansi Secrets", "Everything Lekker", "Pure Magic",
        "Polishing the Vellies", "The Real Deal", "No Stress"
    ]
};

// Personality Phrases (The logic of the app speaking to you)
// I updated these to sound less "Tech" and more "Helpful South African"
const SMART_PHRASES = [
    "Making a plan...",       // Very SA: "Maak 'n plan"
    "Sorting you out...",     // Very SA: "I'll sort you out"
    "Just check this...",
    "Finding the vibe...",
    "Hold tight my bru...",
    "Cooking something up...",
    "Trust the process...",
    "Proper things...",       // "Proper" is big in CPT
    "Insider info...",
    "Almost there...",
    "Checking the map..."
];

export const getLoadingWords = (level: number | null, intent: string | null): string[] => {
    // 1. Determine base personality list
    let baseList: string[] = [];

    if (!level || level <= 2) {
        baseList = WORDS_TOURIST;
    } else if (level >= 4) {
        baseList = WORDS_LOCAL;
    } else {
        // Hybrid: The "Semi-Grater" (Semi-emigrated/local)
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
    // We mix Base (Vibe), Intent (Topic) and Smart (Action) to create a sentence-like flow.
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
        else addWord("Sharp Sharp!"); // The ultimate fallback
        i++;
    }

    return curatedSelection;
};