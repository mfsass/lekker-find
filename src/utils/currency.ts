
/**
 * Currency Utility
 * Handles conversion of ZAR price strings to other currencies.
 */

const SYMBOLS: Record<string, string> = {
    'ZAR': 'R',
    'EUR': '€',
    'USD': '$',
    'GBP': '£'
};

export function convertPriceString(
    priceStr: string,
    targetCurrency: 'ZAR' | 'EUR' | 'USD' | 'GBP',
    rates: Record<string, number>
): string {
    if (!priceStr || targetCurrency === 'ZAR' || priceStr === 'Free') {
        return priceStr;
    }

    // Rate validation
    const rate = rates[targetCurrency];
    if (!rate) return priceStr;

    const symbol = SYMBOLS[targetCurrency] || targetCurrency;

    // Regex to find R-prefixed numbers (e.g., R150, R 150, R1,200)
    // We look for 'R' followed by optional space, then digits/commas
    return priceStr.replace(/R\s?([\d,]+)/g, (match, numberPart) => {
        // Remove commas to parse integer
        const rawValue = parseInt(numberPart.replace(/,/g, ''), 10);
        if (isNaN(rawValue)) return match;

        // Convert
        const converted = rawValue * rate;

        // Rounding logic:
        // If < 10, keep 1 decimal (e.g. 7.5) unless it's 0
        // If > 10, round to integer
        let displayValue = '';
        if (converted < 10 && converted > 0) {
            // Round to 1 decimal place if it clarifies price, otherwise integer
            displayValue = converted.toFixed(1).replace('.0', '');
        } else {
            displayValue = Math.round(converted).toLocaleString();
        }

        return `${symbol}${displayValue}`;
    });
}
