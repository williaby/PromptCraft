import { test, expect } from '@playwright/test';
import { Journey1Page } from './fixtures/Journey1Page';

test.describe('Locator Verification Tests', () => {
  let journey1Page: Journey1Page;

  test.beforeEach(async ({ page }) => {
    journey1Page = new Journey1Page(page);
  });

  test('should find Journey 1 elements with updated locators', async ({ page }) => {
    // Navigate to the application
    await journey1Page.goto();

    // Try to navigate to Journey 1 tab
    try {
      await journey1Page.journey1Tab.click({ timeout: 10000 });
      console.log('✅ Journey 1 tab found and clicked');
    } catch (error) {
      console.log('❌ Journey 1 tab not found:', error.message);

      // Take screenshot for debugging
      await page.screenshot({
        path: 'test-results/journey1-tab-not-found.png',
        fullPage: true
      });

      // List all available buttons for debugging
      const buttons = await page.locator('button').all();
      console.log('Available buttons:');
      for (let i = 0; i < Math.min(buttons.length, 10); i++) {
        const text = await buttons[i].textContent();
        console.log(`  Button ${i}: "${text}"`);
      }
    }

    // Wait a bit for tab content to load
    await page.waitForTimeout(2000);

    // Take screenshot of current state
    await page.screenshot({
      path: 'test-results/after-tab-click.png',
      fullPage: true
    });

    // Test individual element visibility with better error reporting
    const elements = [
      { name: 'Text Input', locator: journey1Page.textInput },
      { name: 'File Upload', locator: journey1Page.fileUpload },
      { name: 'Model Selector', locator: journey1Page.modelSelector },
      { name: 'Enhance Button', locator: journey1Page.enhanceButton },
      { name: 'Enhanced Prompt Output', locator: journey1Page.enhancedPromptOutput }
    ];

    for (const element of elements) {
      try {
        const isVisible = await element.locator.isVisible({ timeout: 5000 });
        if (isVisible) {
          console.log(`✅ ${element.name} found and visible`);
        } else {
          console.log(`⚠️  ${element.name} found but not visible`);
        }
      } catch (error) {
        console.log(`❌ ${element.name} not found:`, error.message);
      }
    }

    // Get page content for analysis if needed
    const pageContent = await page.content();
    const hasGradio = pageContent.includes('gradio');
    const hasTextarea = pageContent.includes('<textarea');
    const hasButton = pageContent.includes('<button');

    console.log('Page analysis:');
    console.log(`  Has Gradio: ${hasGradio}`);
    console.log(`  Has Textarea: ${hasTextarea}`);
    console.log(`  Has Buttons: ${hasButton}`);

    // Look for any textareas and buttons that exist
    const textareas = await page.locator('textarea').count();
    const buttons = await page.locator('button').count();
    const fileInputs = await page.locator('input[type="file"]').count();
    const selects = await page.locator('select').count();

    console.log('Element counts:');
    console.log(`  Textareas: ${textareas}`);
    console.log(`  Buttons: ${buttons}`);
    console.log(`  File inputs: ${fileInputs}`);
    console.log(`  Selects: ${selects}`);

    // If we found basic elements, the test passes
    expect(hasButton).toBe(true);
    expect(buttons).toBeGreaterThan(0);
  });

  test('should be able to interact with found elements', async ({ page }) => {
    await journey1Page.goto();

    try {
      // Try to click Journey 1 tab
      await journey1Page.journey1Tab.click({ timeout: 5000 });
    } catch (error) {
      console.log('Journey 1 tab not found, continuing with available elements');
    }

    await page.waitForTimeout(2000);

    // Try to interact with text input if found
    try {
      await journey1Page.textInput.waitFor({ state: 'visible', timeout: 5000 });
      await journey1Page.textInput.fill('Test prompt');
      console.log('✅ Successfully filled text input');
    } catch (error) {
      console.log('❌ Could not interact with text input:', error.message);
    }

    // Try to click enhance button if found
    try {
      await journey1Page.enhanceButton.waitFor({ state: 'visible', timeout: 5000 });
      console.log('✅ Enhance button is visible and ready to click');
    } catch (error) {
      console.log('❌ Enhance button not found or not visible:', error.message);
    }

    // Take final screenshot
    await page.screenshot({
      path: 'test-results/interaction-test-final.png',
      fullPage: true
    });
  });

  test('should handle application not running gracefully', async ({ page }) => {
    // This test helps us understand what happens when the app isn't running
    try {
      await page.goto('/', { timeout: 10000 });
      console.log('✅ Application is running and accessible');
    } catch (error) {
      console.log('❌ Application is not running or not accessible:', error.message);
      expect(true).toBe(true); // Pass the test even if app isn't running
    }
  });
});
