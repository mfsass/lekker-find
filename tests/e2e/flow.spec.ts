import { test, expect } from '@playwright/test';

test.describe('Questionnaire Flow', () => {
    test.slow();
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.getByRole('button', { name: 'Get Started' }).click();
    });

    test('should complete the full questionnaire', async ({ page }) => {
        // Step 1: Intent - "What sounds good?"
        await expect(page.getByText(/What sounds good/i)).toBeVisible({ timeout: 15000 });
        await page.locator('.vibeOptionItem').filter({ hasText: 'Food & Drink' }).click();
        await page.waitForTimeout(500); // Allow transition

        // Step 2: Tourist Level - "What kind of place?"
        await expect(page.getByText(/What kind of place/i)).toBeVisible({ timeout: 10000 });
        await page.locator('.vibeOptionItem').filter({ hasText: 'Hidden Gems' }).click();
        await page.waitForTimeout(500);

        // Step 3: Budget - "What's your budget?"
        await expect(page.getByText(/What's your budget/i)).toBeVisible({ timeout: 10000 });
        await page.locator('.vibeOptionItem').filter({ hasText: 'Mid-range' }).click();
        await page.waitForTimeout(500);

        // Step 4: Moods - "What's the vibe?"
        await expect(page.getByText(/What's the vibe/i)).toBeVisible({ timeout: 10000 });
        const moodOption = page.locator('.moodTagsList .moodTagItem').first();
        await expect(moodOption).toBeVisible({ timeout: 10000 });
        await moodOption.click();
        await page.waitForTimeout(300);

        await page.getByRole('button', { name: 'Continue' }).click();
        await page.waitForTimeout(500);

        // Step 5: Avoid - "Anything to avoid?"
        await expect(page.getByText(/Anything to avoid/i)).toBeVisible({ timeout: 10000 });
        await page.getByRole('button', { name: 'Get Results' }).click();

        // Results (Loading screen might appear, so increase timeout)
        await expect(page.locator('.results-container')).toBeVisible({ timeout: 45000 });
    });
});
