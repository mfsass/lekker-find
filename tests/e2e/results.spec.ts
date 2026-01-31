import { test, expect } from '@playwright/test';

test.describe('Advanced Results Interaction', () => {
    test.slow();
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        const surpriseBtn = page.getByRole('button', { name: 'Surprise me' });
        await expect(surpriseBtn).toBeEnabled({ timeout: 20000 });
        await surpriseBtn.click();

        // Wait for results to load (account for LoadingScreen)
        await expect(page.locator('.results-container')).toBeVisible({ timeout: 60000 });

        // Dismiss mobile swipe guide if present
        const guide = page.locator('.results-swipe-tutorial');
        if (await guide.isVisible()) {
            await guide.click();
            await page.waitForTimeout(500);
        }
    });

    test('should allow swiping through cards', async ({ page }) => {
        const activeCard = page.locator('.results-card').first();
        await expect(activeCard).toBeVisible({ timeout: 15000 });

        const initialVenueName = await activeCard.locator('h2.results-venue-name').innerText();

        // Perform a swipe left
        const box = await activeCard.boundingBox();
        if (box) {
            const startX = box.x + box.width * 0.8;
            const startY = box.y + box.height / 2;
            const endX = box.x + box.width * 0.2;

            await page.mouse.move(startX, startY);
            await page.mouse.down();
            await page.mouse.move(startX - 20, startY, { steps: 3 }); // Initial drag move
            await page.mouse.move(endX, startY, { steps: 7 }); // Fast swipe
            await page.mouse.up();
        }

        // Wait for transition animation
        await page.waitForTimeout(1500);

        // Verify next card is different
        const nextVenueName = await page.locator('.results-card h2.results-venue-name').first().innerText();
        expect(nextVenueName).not.toBe(initialVenueName);
    });

    test('should allow navigation via buttons', async ({ page }) => {
        // Buttons are usually only on desktop
        const nextBtn = page.locator('.results-nav-btn[aria-label="Next venue"]');
        if (await nextBtn.isVisible()) {
            const initialVenueName = await page.locator('.results-card h2.results-venue-name').first().innerText();
            await nextBtn.click();
            await page.waitForTimeout(800);

            const nextVenueName = await page.locator('.results-card h2.results-venue-name').first().innerText();
            expect(nextVenueName).not.toBe(initialVenueName);

            // Go back
            const prevBtn = page.locator('.results-nav-btn[aria-label="Previous venue"]');
            await prevBtn.click();
            await page.waitForTimeout(800);

            const backVenueName = await page.locator('.results-card h2.results-venue-name').first().innerText();
            expect(backVenueName).toBe(initialVenueName);
        }
    });

    test('should show end message when reaching final card', async ({ page }) => {
        // More robust approach: swipe until end message appears
        for (let i = 0; i < 50; i++) {
            const endMessage = page.locator('.results-end-message');
            if (await endMessage.isVisible()) break;

            const nextBtn = page.locator('.results-nav-btn[aria-label="Next venue"]');
            if (await nextBtn.isVisible() && await nextBtn.isEnabled()) {
                await nextBtn.click();
            } else {
                const card = page.locator('.results-card').first();
                if (!(await card.isVisible())) break;
                // On mobile, tapping the card goes to the next venue
                await card.click();
            }
            await page.waitForTimeout(200);
        }

        await expect(page.locator('.results-end-message')).toBeVisible({ timeout: 15000 });
        await expect(page.getByText('Not quite right?')).toBeVisible();
    });

    test('should handle sharing and clipboard', async ({ page, context, browserName }, testInfo) => {
        // WebKit/Safari often has issues with clipboard permissions in headless mode
        if (browserName === 'webkit' || testInfo.project.name === 'Mobile Safari') {
            test.skip();
            return;
        }

        // Navigate via standard flow for sharing (Surprise Me disables sharing)
        await page.goto('/');
        await page.getByRole('button', { name: 'Get Started' }).click();

        // Step 1: Intent
        await expect(page.getByText('What sounds good?')).toBeVisible();
        await page.locator('.vibeOptionItem').first().click();

        // Step 2: Tourist Level
        await expect(page.getByText('What kind of place?')).toBeVisible();
        await page.locator('.vibeOptionItem').first().click();

        // Step 3: Budget
        await expect(page.getByText("What's your budget?")).toBeVisible();
        await page.locator('.vibeOptionItem').first().click();

        // Step 4: Moods
        await expect(page.getByText("What's the vibe?")).toBeVisible();
        // Select two moods for higher matching and better stability
        const moonBtns = page.getByRole('button', { name: /Select .* mood/ });
        await expect(moonBtns.first()).toBeVisible();
        await moonBtns.nth(0).click();
        await moonBtns.nth(1).click();

        const continueBtn = page.getByRole('button', { name: 'Continue' });
        await expect(continueBtn).toBeEnabled();
        await continueBtn.click();

        // Step 5: Avoid
        await expect(page.getByText('Anything to avoid?')).toBeVisible();
        await page.getByRole('button', { name: 'Get Results' }).click();

        // IMPORTANT: Wait for results to actually load
        await expect(page.locator('.results-container')).toBeVisible({ timeout: 30000 });

        await context.grantPermissions(['clipboard-read', 'clipboard-write']);

        const shareBtn = page.locator('.share-btn').first();
        await expect(shareBtn).toBeVisible({ timeout: 15000 });
        await shareBtn.click();

        await expect(shareBtn).toContainText('Copied!');
        const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
        // Check for the share query parameter which is the core of the functionality
        expect(clipboardText).toContain('?q=');
    });
});
