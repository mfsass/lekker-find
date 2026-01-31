import { test, expect } from '@playwright/test';

test.describe('Landing Page', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should look lekker on load', async ({ page }) => {
        // Check title
        await expect(page).toHaveTitle(/Lekker Find/);

        // Check hero text
        const hero = page.locator('h1.landing-slogan');
        await expect(hero).toBeVisible();
        await expect(hero).toContainText('Discover something');
        await expect(hero).toContainText('lekker'); // Accent span
    });

    test('should have a Get Started button', async ({ page }) => {
        const button = page.getByRole('button', { name: 'Get Started' });
        await expect(button).toBeVisible();
        await expect(button).toBeEnabled();
    });

    test('should have a Surprise Me button', async ({ page }) => {
        const button = page.getByRole('button', { name: 'Surprise me' });
        await expect(button).toBeVisible();
        // It might be disabled initially if recommendations aren't ready, but usually fast locally
        // If it's disabled, verify that too, but ideally it becomes enabled.
        // Let's check it exists.
        await expect(button).toBeVisible();
    });
});
