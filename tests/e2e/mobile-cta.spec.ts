
import { test, expect } from '@playwright/test';

test.describe('Mobile CTA Responsiveness', () => {
    test.use({ viewport: { width: 375, height: 667 } }); // iPhone 8 dimensions

    test('Surprise Me button should work with a single click and not require double click', async ({ page }) => {
        await page.goto('/');

        const surpriseBtn = page.getByRole('button', { name: 'Surprise me' });
        await expect(surpriseBtn).toBeEnabled({ timeout: 20000 });

        // Small pause to ensure layout stability
        await page.waitForTimeout(500);
        await surpriseBtn.click({ force: true });

        // Verify we moved to results step
        await expect(page.locator('.results-container')).toBeVisible({ timeout: 45000 });

        // Verify we are actually seeing cards
        await expect(page.locator('.results-card').first()).toBeVisible({ timeout: 20000 });
    });

    test('Get Started button should work with a single click', async ({ page }) => {
        await page.goto('/');

        const getStartedBtn = page.getByRole('button', { name: 'Get Started' });
        await expect(getStartedBtn).toBeVisible();

        await page.waitForTimeout(500);
        await getStartedBtn.click({ force: true });

        // Verify we moved to the first question
        await expect(page.locator('.question-title')).toBeVisible({ timeout: 15000 });
        await expect(page.locator('.question-title')).toContainText('What sounds good?');
    });

    test('Vibe options should work with a single click', async ({ page }) => {
        await page.goto('/');

        // Go to questions
        await page.getByRole('button', { name: 'Get Started' }).click({ force: true });

        // Click an option
        const option = page.locator('.vibeOptionItem').first();
        await expect(option).toBeVisible();

        await page.waitForTimeout(500);
        await option.click({ force: true });

        // Should transition to next step automatically
        // Step 1 -> Step 2 (Tourist Level)
        await expect(page.locator('.question-title')).toContainText('What kind of place?', { timeout: 10000 });
    });
});
