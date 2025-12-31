// Authentic, funny, local South African phrases
// A mix of slang, iconic lyrics, items, and generalized vibes
// Completely unmistakably South African, curated for uniqueness
const LEKKER_WORDS = [
    // Iconic Anthems & Lyrics
    "Nkosi Sikelel'",
    "Shosholoza",
    "Sister Bethina",
    "Waka Waka",
    "Pata Pata",
    "Kaptein",
    "Weekend Special",
    "Vulindlela",
    "Nkalakatha",
    "Burnout",
    "Impi",
    "Mango Groove",
    "Jerusalema",

    // Unmistakably SA Items & Fashion
    "K-Way Jacket",
    "Puffer Jacket",
    "Vellies",
    "Plakkies",
    "Two Tone Shirt",
    "Shorts in Winter",
    "Springbok Jersey",
    "Sunlight Soap",
    "All Gold",
    "Mrs Balls",
    "Aromat",
    "Ouma Rusks",
    "Zam-Buk",
    "Grandpa Powder",
    "NikNaks",

    // Directions & Tour Guide
    "Left at the Circle",
    "Robot to Robot",
    "Just passed the Garage",
    "Yellow Lane",
    "Car Watcher",
    "Petrol Attendant",
    "Taxi Gaatjie",
    "Sho't Left",

    // Slang & Greetings
    "Now Now",
    "Just Now",
    "Aweh My Bru",
    "Lekker Vibes",
    "Pure Gees",
    "Ja Nee",
    "Eish! One Sec",
    "Yoh! Hang On",
    "Jinne!",
    "Haibo!",
    "Sho! Wena",
    "Duidelik",
    "Proper Things",
    "Bare Mooi",
    "Sharp Sharp",
    "Mooiloop",
    "Howzit",
    "Heita!",
    "Chommie",
    "My China",
    "Mzansi Magic",
    "Local is Lekker",
    "Mos",
    "Jolling",

    // Food & Drink 
    "Braai Time",
    "Shisa Nyama",
    "Gatsby Hunting",
    "Koesister Sunday",
    "Bunny Chow",
    "Biltong Time",
    "Droëwors Snack",
    "Melktert Mission",
    "Snoek Braai",
    "Fish & Chips",
    "Craft Beer",
    "Gin O'Clock",
    "Sundowners",
    "Ice Cold One",
    "Springbokkie",

    // Activities & Vibes
    "Catching a Tan",
    "Kloofing",
    "Hiking Trails",
    "Just Chilling",
    "Proper Jol",
    "On a Mission",
    "Dodging Loadshedding",
    "Woolies Run",
    "Finding Parking",
    "Kaapse Klopse",
    "Flower Season",
    "Penguin Spotting",
    "Baboon Watch",
    "Dodging the Wind",
    "Chasing Sunsets",
    "Mountain Views",
    "Ocean Breeze",
    "Vitamin Sea",
    "Forest Walks",
    "Road Tripping",
    "Checking the Surf",
    "Buying Ice",
    "Looking for Shade",
    "Running Late",
    "African Time",
    "Family Time",
    "Sunday Lunch",
    "Go Bokke!",
    "Bomb Squad",
    "Rugby Vibes"
];

export const getLoadingWords = (): string[] => {
    // Return a shuffled 12 words for the animation loop
    // We need exactly 12 words for the CSS animation to loop perfectly
    const shuffled = [...LEKKER_WORDS].sort(() => 0.5 - Math.random());

    // If we somehow don't have enough words, pad them (unlikely with above list)
    while (shuffled.length < 12) {
        shuffled.push(...LEKKER_WORDS);
    }

    return shuffled.slice(0, 12);
};