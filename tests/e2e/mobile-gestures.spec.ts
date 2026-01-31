
import { test, expect } from '@playwright/test';

test.describe('Mobile Gestures', () => {
    test.use({ viewport: { width: 375, height: 667 } }); // iPhone 8 dimensions

    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        const surpriseBtn = page.getByRole('button', { name: 'Surprise me' });
        await expect(surpriseBtn).toBeEnabled();
        await surpriseBtn.click();

        // Wait for results to load
        await expect(page.locator('.results-container')).toBeVisible({ timeout: 60000 });

        // Dismiss tutorial if present
        const guide = page.locator('.results-swipe-tutorial');
        if (await guide.isVisible()) {
            await guide.click();
        }
    });

    test('should allow swiping back to previous card', async ({ page }) => {
        // Use first() to avoid strict mode error if multiple cards are temporarily present (during animation)
        const card = page.locator('.results-card').first();
        await expect(card).toBeVisible();

        const firstVenueName = await card.locator('.results-venue-name').innerText();

        // 1. Swipe Left to go to next card
        const box1 = await card.boundingBox();
        if (!box1) throw new Error('Card not found');

        const startX1 = box1.x + box1.width * 0.8;
        const startY1 = box1.y + box1.height / 2;
        const endX1 = box1.x + box1.width * 0.2;

        await page.mouse.move(startX1, startY1);
        await page.mouse.down();
        // Slower swipe with more steps for WebKit reliability
        await page.mouse.move(endX1, startY1, { steps: 25 });
        await page.mouse.up();

        await page.waitForTimeout(2000); // Increased wait for animation stability

        const cardAfterSwipe = page.locator('.results-card').first();
        await expect(cardAfterSwipe).toBeVisible();
        const secondVenueName = await cardAfterSwipe.locator('.results-venue-name').innerText();
        expect(secondVenueName).not.toBe(firstVenueName);

        // 2. Swipe Right to go back (The "Back Swipe")
        const box2 = await cardAfterSwipe.boundingBox();
        if (!box2) throw new Error('Card not found');

        const centerX = box2.x + box2.width / 2;
        const centerY = box2.y + box2.height / 2;

        await page.mouse.move(centerX - 100, centerY);
        await page.mouse.down();
        // Slower swipe for WebKit stability
        await page.mouse.move(centerX + 150, centerY, { steps: 25 });
        await page.mouse.up();

        await page.waitForTimeout(2000); // Increased wait for animation

        const finalCard = page.locator('.results-card').first();
        await expect(finalCard).toBeVisible();
        const currentVenueName = await finalCard.locator('.results-venue-name').innerText();

        expect(currentVenueName).toBe(firstVenueName);
    });
});
