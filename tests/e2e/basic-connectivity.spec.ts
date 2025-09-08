import { test, expect } from '@playwright/test';

test.describe('Basic Connectivity Test', () => {
  test('should connect to PromptCraft application', async ({ page }) => {
    console.log('Attempting to connect to http://localhost:7860');

    try {
      await page.goto('http://localhost:7860', {
        waitUntil: 'networkidle',
        timeout: 60000
      });

      console.log('Successfully connected to application');

      // Take a screenshot to see what we get
      await page.screenshot({ path: 'test-results/connectivity-test.png', fullPage: true });

      // Check if we can see the basic page elements
      const title = await page.title();
      console.log(`Page title: ${title}`);

      // Look for any text content
      const bodyText = await page.locator('body').textContent();
      console.log(`Body content length: ${bodyText?.length || 0} characters`);

      if (bodyText && bodyText.length > 100) {
        console.log(`First 200 chars: ${bodyText.substring(0, 200)}...`);
      }

      // Success if we get here
      expect(true).toBe(true);

    } catch (error) {
      console.error('Connection failed:', error.message);

      // Try to get more information about the error
      const currentUrl = page.url();
      console.log(`Current URL: ${currentUrl}`);

      throw error;
    }
  });

  test('should find basic UI elements', async ({ page }) => {
    await page.goto('http://localhost:7860', { waitUntil: 'networkidle', timeout: 60000 });

    // Look for common elements that might indicate a working Gradio app
    const elements = [
      'button',
      'textarea',
      'input',
      '[data-testid]',
      '.gradio-container',
      '#root',
      '#app'
    ];

    const foundElements = [];

    for (const selector of elements) {
      try {
        const count = await page.locator(selector).count();
        foundElements.push(`${selector}: ${count}`);
        console.log(`Found ${count} elements matching "${selector}"`);
      } catch (error) {
        foundElements.push(`${selector}: error`);
      }
    }

    console.log('Element scan results:', foundElements);

    // We expect to find at least some interactive elements
    const buttonCount = await page.locator('button').count();
    const textareaCount = await page.locator('textarea').count();

    expect(buttonCount + textareaCount).toBeGreaterThan(0);
  });
});
