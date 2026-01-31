import { test, expect } from '@playwright/test';

test.describe('Surprise Me Flow', () => {
    test('should jump straight to results', async ({ page }) => {
        await page.goto('/');

        // Wait for data to load so button enables
        const surpriseBtn = page.getByRole('button', { name: 'Surprise me' });
        await expect(surpriseBtn).toBeEnabled({ timeout: 20000 });
        await surpriseBtn.click();

        // Results (Loading screen appears, can take up to 5-10s)
        await expect(page.locator('.results-container')).toBeVisible({ timeout: 30000 });

        // Verify we have cards
        await expect(page.locator('.results-card').first()).toBeVisible({ timeout: 10000 });

        // Verify diverse results (at least 1 card exists)
        const venueName = await page.locator('.results-venue-name').first().innerText();
        expect(venueName.length).toBeGreaterThan(0);
    });
});
