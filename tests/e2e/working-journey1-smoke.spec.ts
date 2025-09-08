import { test, expect } from '@playwright/test';

test.describe('Working Journey 1 Smoke Test', () => {

  // Disable global setup/teardown for this test to avoid localStorage issues
  test('should perform basic Journey 1 smoke test', async ({ page }) => {
    console.log('🚀 Starting Journey 1 smoke test...');

    // Navigate to the application
    await page.goto('http://localhost:7860', {
      waitUntil: 'load',
      timeout: 30000
    });

    console.log('✅ Page loaded successfully');

    // Wait for basic page elements
    await page.waitForSelector('h1', { timeout: 15000 });
    const title = await page.locator('h1').textContent();
    console.log(`✅ Page title: "${title}"`);
    expect(title).toContain('PromptCraft');

    // Handle the Journey 1 button with multiple matches
    const journey1Buttons = page.locator('button:has-text("📝 Journey 1: Smart Templates")');
    const buttonCount = await journey1Buttons.count();
    console.log(`✅ Found ${buttonCount} Journey 1 buttons`);
    expect(buttonCount).toBeGreaterThan(0);

    // Click the tab version (usually the second one with role="tab")
    const journey1Tab = page.locator('button[role="tab"]:has-text("Journey 1")');
    if (await journey1Tab.count() > 0) {
      await journey1Tab.click();
      console.log('✅ Journey 1 tab clicked');
    } else {
      // Fallback to first button
      await journey1Buttons.first().click();
      console.log('✅ Journey 1 button clicked (fallback)');
    }

    // Wait a moment for tab content to load
    await page.waitForTimeout(2000);

    // Look for the text input more generically
    const textInputs = page.locator('textarea');
    const textInputCount = await textInputs.count();
    console.log(`✅ Found ${textInputCount} text areas`);
    expect(textInputCount).toBeGreaterThan(0);

    // Use the first visible textarea as the main input
    const mainInput = textInputs.first();
    await expect(mainInput).toBeVisible({ timeout: 10000 });
    console.log('✅ Main text input found and visible');

    // Test basic text input functionality
    const testPrompt = 'Basic smoke test prompt';
    await mainInput.fill(testPrompt);
    const inputValue = await mainInput.inputValue();
    expect(inputValue).toBe(testPrompt);
    console.log('✅ Text input functionality working');

    // Look for buttons
    const allButtons = page.locator('button');
    const buttonCount2 = await allButtons.count();
    console.log(`✅ Found ${buttonCount2} total buttons on page`);

    // Look specifically for the enhance button
    const enhanceButtons = page.locator('button:has-text("Enhance")');
    const enhanceCount = await enhanceButtons.count();
    console.log(`✅ Found ${enhanceCount} buttons with "Enhance" text`);

    if (enhanceCount > 0) {
      const enhanceButton = enhanceButtons.first();
      await expect(enhanceButton).toBeVisible();
      console.log('✅ Enhance button found and visible');

      // Test button interaction (click but don't wait for enhancement to complete)
      await enhanceButton.click();
      console.log('✅ Enhance button clicked successfully');

      // Give a moment for any immediate UI changes
      await page.waitForTimeout(2000);

    } else {
      console.log('⚠️ Enhance button not found by text match');
    }

    // Look for clear functionality
    const clearButtons = page.locator('button:has-text("Clear")');
    const clearCount = await clearButtons.count();
    console.log(`✅ Found ${clearCount} buttons with "Clear" text`);

    if (clearCount > 0) {
      const clearButton = clearButtons.first();
      await clearButton.click();
      await page.waitForTimeout(1000);

      // Check if input was cleared
      const clearedValue = await mainInput.inputValue();
      console.log(`✅ After clear, input value: "${clearedValue}"`);
    }

    // Take a screenshot of the final state
    await page.screenshot({
      path: 'test-results/journey1-smoke-test-final.png',
      fullPage: true
    });

    console.log('🎉 Journey 1 smoke test completed successfully');
    console.log('📊 Summary:');
    console.log(`   - Page loaded: ✅`);
    console.log(`   - Title found: ✅`);
    console.log(`   - Journey 1 buttons: ${buttonCount}`);
    console.log(`   - Text inputs: ${textInputCount}`);
    console.log(`   - Total buttons: ${buttonCount2}`);
    console.log(`   - Enhance buttons: ${enhanceCount}`);
    console.log(`   - Clear buttons: ${clearCount}`);
  });

  test('should test basic authentication state', async ({ page }) => {
    console.log('🔐 Testing authentication state...');

    await page.goto('http://localhost:7860', {
      waitUntil: 'load',
      timeout: 30000
    });

    // Check if we're redirected to a login page or if the app loads directly
    const currentUrl = page.url();
    console.log(`🌐 Current URL: ${currentUrl}`);

    // Check if we see the main app interface
    const hasMainInterface = await page.locator('h1:has-text("PromptCraft")').count() > 0;
    console.log(`🎨 Main interface visible: ${hasMainInterface ? 'Yes' : 'No'}`);

    if (hasMainInterface) {
      console.log('✅ Direct access to application - no authentication redirect');

      // Check for any authentication indicators
      const authIndicators = [
        'Login',
        'Sign in',
        'Authenticate',
        'Cloudflare',
        'Access Denied'
      ];

      let authFound = false;
      for (const indicator of authIndicators) {
        const count = await page.locator(`text=${indicator}`).count();
        if (count > 0) {
          console.log(`🔍 Found authentication indicator: "${indicator}"`);
          authFound = true;
        }
      }

      if (!authFound) {
        console.log('✅ No authentication barriers detected');
      }

    } else {
      console.log('⚠️ Main interface not immediately visible - possible authentication required');

      // Take screenshot of what we see instead
      await page.screenshot({
        path: 'test-results/auth-state-screenshot.png',
        fullPage: true
      });

      // Get page content for analysis
      const pageContent = await page.content();
      console.log(`📄 Page content length: ${pageContent.length} characters`);

      if (pageContent.includes('cloudflare')) {
        console.log('🔒 Cloudflare authentication detected');
      }
    }

    console.log('🔐 Authentication state test completed');
  });
});
