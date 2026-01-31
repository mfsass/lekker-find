import { test, expect } from '@playwright/test';

test.describe('Result Accuracy', () => {
    test.slow();
    test('should show relevant results for a specific vibe', async ({ page }) => {
        await page.goto('/');
        await page.getByRole('button', { name: 'Get Started' }).click();

        // Step 1: Intent
        await expect(page.getByText(/What sounds good/i)).toBeVisible({ timeout: 15000 });
        await page.locator('.vibeOptionItem').filter({ hasText: 'Food & Drink' }).click();
        await page.waitForTimeout(500);

        // Step 2: Tourist Level
        await expect(page.getByText(/What kind of place/i)).toBeVisible({ timeout: 10000 });
        await page.locator('.vibeOptionItem').filter({ hasText: 'Hidden Gems' }).click();
        await page.waitForTimeout(500);

        // Step 3: Budget
        await expect(page.getByText(/What's your budget/i)).toBeVisible({ timeout: 10000 });
        await page.locator('.vibeOptionItem').filter({ hasText: 'Mid-range' }).click();
        await page.waitForTimeout(500);

        // Step 4: Moods
        await expect(page.getByText(/What's the vibe/i)).toBeVisible({ timeout: 10000 });
        const moodTag = page.locator('.moodTagItem').first();
        await expect(moodTag).toBeVisible({ timeout: 10000 });
        await moodTag.click();
        await page.waitForTimeout(300);

        await page.getByRole('button', { name: 'Continue' }).click();
        await page.waitForTimeout(500);

        // Step 5: Anything to avoid?
        await expect(page.getByText(/Anything to avoid/i)).toBeVisible({ timeout: 10000 });
        await page.getByRole('button', { name: 'Get Results' }).click();

        // Wait for results
        await expect(page.locator('.results-container')).toBeVisible({ timeout: 45000 });

        // Check match percentage exists
        const badge = page.locator('.results-match-badge').first();
        await expect(badge).toBeVisible({ timeout: 15000 });
    });
});
