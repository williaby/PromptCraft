import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Journey 1: Visual Regression Testing', () => {
  const baselineDir = path.join(__dirname, 'visual-baselines');
  const diffDir = path.join(__dirname, 'visual-diffs');

  test.beforeAll(async () => {
    // Ensure baseline and diff directories exist
    [baselineDir, diffDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  });

  test.beforeEach(async ({ page }) => {
    // Navigate to Journey 1 with consistent setup
    await page.goto('http://localhost:7860', {
      waitUntil: 'load',
      timeout: 30000
    });

    await page.waitForSelector('h1', { timeout: 15000 });

    // Switch to Journey 1 tab
    const journey1Tab = page.locator('button[role="tab"]:has-text("Journey 1")');
    if (await journey1Tab.count() > 0) {
      await journey1Tab.click();
      await page.waitForTimeout(2000);
    }

    // Wait for UI to stabilize
    await page.waitForTimeout(1000);
  });

  test.describe('Initial State Visual Validation', () => {
    test('should match Journey 1 initial layout baseline', async ({ page, browserName }) => {
      console.log('📸 Capturing Journey 1 initial state...');

      // Ensure consistent viewport
      await page.setViewportSize({ width: 1280, height: 1024 });

      // Wait for all content to load
      await page.waitForSelector('textarea', { timeout: 10000 });
      await page.waitForTimeout(2000);

      // Take baseline screenshot
      await expect(page).toHaveScreenshot(`journey1-initial-${browserName}.png`, {
        fullPage: true,
        threshold: 0.2, // Allow for minor font rendering differences
        maxDiffPixels: 1000
      });

      console.log('✅ Initial layout visual validation completed');
    });

    test('should match mobile Journey 1 layout', async ({ page, browserName }) => {
      console.log('📱 Capturing mobile Journey 1 layout...');

      // Set mobile viewport
      await page.setViewportSize({ width: 390, height: 844 });

      await page.waitForSelector('textarea', { timeout: 10000 });
      await page.waitForTimeout(2000);

      // Take mobile screenshot
      await expect(page).toHaveScreenshot(`journey1-mobile-${browserName}.png`, {
        fullPage: true,
        threshold: 0.2,
        maxDiffPixels: 800
      });

      console.log('✅ Mobile layout visual validation completed');
    });

    test('should match Journey 1 tab navigation states', async ({ page, browserName }) => {
      console.log('🔄 Capturing tab navigation states...');

      await page.setViewportSize({ width: 1280, height: 1024 });

      // Capture active Journey 1 tab state
      await expect(page).toHaveScreenshot(`journey1-tab-active-${browserName}.png`, {
        clip: { x: 0, y: 0, width: 1280, height: 200 }, // Header area only
        threshold: 0.1,
        maxDiffPixels: 500
      });

      // Switch to another tab and back to test state changes
      const journey2Tab = page.locator('button[role="tab"]:has-text("Journey 2")');
      if (await journey2Tab.count() > 0) {
        await journey2Tab.click();
        await page.waitForTimeout(1000);

        // Switch back to Journey 1
        const journey1Tab = page.locator('button[role="tab"]:has-text("Journey 1")');
        await journey1Tab.click();
        await page.waitForTimeout(2000);

        // Verify visual state restoration
        await expect(page).toHaveScreenshot(`journey1-tab-restored-${browserName}.png`, {
          clip: { x: 0, y: 0, width: 1280, height: 200 },
          threshold: 0.1,
          maxDiffPixels: 500
        });
      }

      console.log('✅ Tab navigation visual validation completed');
    });
  });

  test.describe('Interactive State Visual Validation', () => {
    test('should match text input focus and content states', async ({ page, browserName }) => {
      console.log('⌨️ Capturing text input states...');

      await page.setViewportSize({ width: 1280, height: 1024 });

      const textInput = page.locator('textarea').first();

      // Capture focused input state
      await textInput.click();
      await page.waitForTimeout(500);

      await expect(page).toHaveScreenshot(`journey1-input-focused-${browserName}.png`, {
        clip: { x: 0, y: 200, width: 1280, height: 600 }, // Input area
        threshold: 0.2,
        maxDiffPixels: 1000
      });

      // Capture input with content
      await textInput.fill('Sample test prompt for visual regression testing');
      await page.waitForTimeout(500);

      await expect(page).toHaveScreenshot(`journey1-input-content-${browserName}.png`, {
        clip: { x: 0, y: 200, width: 1280, height: 600 },
        threshold: 0.2,
        maxDiffPixels: 800
      });

      console.log('✅ Text input visual states validated');
    });

    test('should match button states and interactions', async ({ page, browserName }) => {
      console.log('🔘 Capturing button interaction states...');

      await page.setViewportSize({ width: 1280, height: 1024 });

      // Fill input first to enable buttons
      const textInput = page.locator('textarea').first();
      await textInput.fill('Test prompt for button states');
      await page.waitForTimeout(500);

      // Capture buttons in default state
      await expect(page).toHaveScreenshot(`journey1-buttons-default-${browserName}.png`, {
        clip: { x: 0, y: 600, width: 1280, height: 200 }, // Button area
        threshold: 0.1,
        maxDiffPixels: 500
      });

      // Capture enhance button hover state (if possible)
      const enhanceButton = page.locator('button:has-text("Enhance")').first();
      await enhanceButton.hover();
      await page.waitForTimeout(300);

      await expect(page).toHaveScreenshot(`journey1-enhance-hover-${browserName}.png`, {
        clip: { x: 0, y: 600, width: 1280, height: 200 },
        threshold: 0.1,
        maxDiffPixels: 400
      });

      console.log('✅ Button states visual validation completed');
    });

    test('should match enhancement output visual states', async ({ page, browserName }) => {
      console.log('✨ Capturing enhancement output states...');

      await page.setViewportSize({ width: 1280, height: 1024 });

      // Fill input and trigger enhancement
      const textInput = page.locator('textarea').first();
      await textInput.fill('Create a visual regression test prompt');

      const enhanceButton = page.locator('button:has-text("Enhance")').first();
      await enhanceButton.click();

      // Wait for enhancement to begin (loading state)
      await page.waitForTimeout(2000);

      // Capture loading/processing state
      await expect(page).toHaveScreenshot(`journey1-enhancement-processing-${browserName}.png`, {
        fullPage: true,
        threshold: 0.3, // More lenient for loading states
        maxDiffPixels: 2000
      });

      // Wait for enhancement completion
      await page.waitForTimeout(8000);

      // Capture completed enhancement state
      await expect(page).toHaveScreenshot(`journey1-enhancement-complete-${browserName}.png`, {
        fullPage: true,
        threshold: 0.2,
        maxDiffPixels: 1500
      });

      console.log('✅ Enhancement output visual validation completed');
    });
  });

  test.describe('Framework Analysis Visual Validation', () => {
    test('should match C.R.E.A.T.E. framework display states', async ({ page, browserName }) => {
      console.log('🔍 Capturing C.R.E.A.T.E. framework states...');

      await page.setViewportSize({ width: 1280, height: 1024 });

      // Fill input for framework analysis
      const textInput = page.locator('textarea').first();
      await textInput.fill('Test prompt for C.R.E.A.T.E. framework analysis');

      // Enable framework analysis if available
      const frameworkCheckbox = page.locator('input[type="checkbox"]').first();
      if (await frameworkCheckbox.count() > 0 && !(await frameworkCheckbox.isChecked())) {
        await frameworkCheckbox.check();
        await page.waitForTimeout(1000);
      }

      // Trigger enhancement
      const enhanceButton = page.locator('button:has-text("Enhance")').first();
      await enhanceButton.click();
      await page.waitForTimeout(10000);

      // Capture framework analysis display
      await expect(page).toHaveScreenshot(`journey1-framework-analysis-${browserName}.png`, {
        fullPage: true,
        threshold: 0.2,
        maxDiffPixels: 2000
      });

      // Check for framework breakdown accordion/section
      const frameworkAccordion = page.locator('text=C.R.E.A.T.E.').first();
      if (await frameworkAccordion.count() > 0) {
        // Expand framework breakdown if collapsed
        try {
          await frameworkAccordion.click();
          await page.waitForTimeout(1000);

          await expect(page).toHaveScreenshot(`journey1-framework-expanded-${browserName}.png`, {
            fullPage: true,
            threshold: 0.2,
            maxDiffPixels: 1500
          });
        } catch (error) {
          console.log('Framework breakdown not expandable or already expanded');
        }
      }

      console.log('✅ C.R.E.A.T.E. framework visual validation completed');
    });
  });

  test.describe('Error State Visual Validation', () => {
    test('should match error and empty states', async ({ page, browserName }) => {
      console.log('⚠️ Capturing error and empty states...');

      await page.setViewportSize({ width: 1280, height: 1024 });

      // Capture empty state
      await expect(page).toHaveScreenshot(`journey1-empty-state-${browserName}.png`, {
        fullPage: true,
        threshold: 0.1,
        maxDiffPixels: 500
      });

      // Try to trigger enhancement without input (if applicable)
      const enhanceButton = page.locator('button:has-text("Enhance")').first();
      if (await enhanceButton.isEnabled()) {
        await enhanceButton.click();
        await page.waitForTimeout(2000);

        // Capture any error states or validation messages
        await expect(page).toHaveScreenshot(`journey1-validation-state-${browserName}.png`, {
          fullPage: true,
          threshold: 0.2,
          maxDiffPixels: 1000
        });
      }

      console.log('✅ Error state visual validation completed');
    });

    test('should match cleared state visual consistency', async ({ page, browserName }) => {
      console.log('🗑️ Capturing cleared state consistency...');

      await page.setViewportSize({ width: 1280, height: 1024 });

      // Fill content first
      const textInput = page.locator('textarea').first();
      await textInput.fill('Content to be cleared for visual testing');
      await page.waitForTimeout(500);

      // Clear the content
      const clearButton = page.locator('button:has-text("Clear")').first();
      if (await clearButton.count() > 0) {
        await clearButton.click();
        await page.waitForTimeout(1000);

        // Capture cleared state
        await expect(page).toHaveScreenshot(`journey1-cleared-state-${browserName}.png`, {
          fullPage: true,
          threshold: 0.1,
          maxDiffPixels: 500
        });

        // Should match initial empty state
        await expect(page).toHaveScreenshot(`journey1-empty-state-${browserName}.png`);
      }

      console.log('✅ Cleared state visual validation completed');
    });
  });

  test.describe('Responsive Design Visual Validation', () => {
    test('should match responsive breakpoints', async ({ page, browserName }) => {
      console.log('📐 Capturing responsive design breakpoints...');

      const breakpoints = [
        { name: 'mobile', width: 375, height: 667 },
        { name: 'tablet', width: 768, height: 1024 },
        { name: 'desktop', width: 1280, height: 1024 },
        { name: 'wide', width: 1920, height: 1080 }
      ];

      // Fill content for consistent testing
      const textInput = page.locator('textarea').first();
      await textInput.fill('Responsive design test prompt');

      for (const breakpoint of breakpoints) {
        console.log(`📱 Testing ${breakpoint.name} breakpoint (${breakpoint.width}x${breakpoint.height})`);

        await page.setViewportSize({
          width: breakpoint.width,
          height: breakpoint.height
        });

        // Wait for layout to adjust
        await page.waitForTimeout(1000);

        // Ensure Journey 1 is still active after viewport change
        const journey1Tab = page.locator('button[role="tab"]:has-text("Journey 1")');
        if (await journey1Tab.count() > 0 && !(await journey1Tab.getAttribute('aria-selected'))) {
          await journey1Tab.click();
          await page.waitForTimeout(1000);
        }

        await expect(page).toHaveScreenshot(`journey1-${breakpoint.name}-${browserName}.png`, {
          fullPage: true,
          threshold: 0.2,
          maxDiffPixels: 1500
        });
      }

      console.log('✅ Responsive design visual validation completed');
    });
  });

  test.describe('Cross-Browser Visual Consistency', () => {
    test('should maintain visual consistency across browsers', async ({ page, browserName }) => {
      console.log(`🌐 Validating visual consistency for ${browserName}...`);

      await page.setViewportSize({ width: 1280, height: 1024 });

      // Fill standardized content
      const textInput = page.locator('textarea').first();
      await textInput.fill('Cross-browser visual consistency test content');
      await page.waitForTimeout(500);

      // Capture cross-browser baseline
      await expect(page).toHaveScreenshot(`journey1-cross-browser-${browserName}.png`, {
        fullPage: true,
        threshold: 0.3, // More lenient for cross-browser differences
        maxDiffPixels: 2000
      });

      // Test specific UI components that might differ across browsers
      const componentAreas = [
        { name: 'header', clip: { x: 0, y: 0, width: 1280, height: 200 } },
        { name: 'input-area', clip: { x: 0, y: 200, width: 1280, height: 400 } },
        { name: 'buttons', clip: { x: 0, y: 600, width: 1280, height: 150 } }
      ];

      for (const area of componentAreas) {
        await expect(page).toHaveScreenshot(`journey1-${area.name}-${browserName}.png`, {
          clip: area.clip,
          threshold: 0.2,
          maxDiffPixels: 800
        });
      }

      console.log(`✅ ${browserName} visual consistency validation completed`);
    });
  });

  test.afterAll(async () => {
    // Generate visual regression report
    const reportPath = path.join(__dirname, 'visual-regression-report.html');

    const reportContent = `
<!DOCTYPE html>
<html>
<head>
    <title>Visual Regression Test Report</title>
    <style>
        body { font-family: system-ui; margin: 20px; }
        .header { border-bottom: 2px solid #ccc; padding-bottom: 10px; }
        .test-section { margin: 20px 0; }
        .screenshot { margin: 10px; display: inline-block; }
        .screenshot img { max-width: 300px; border: 1px solid #ddd; }
        .summary { background: #f5f5f5; padding: 15px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Visual Regression Test Report</h1>
        <p>Generated: ${new Date().toISOString()}</p>
    </div>

    <div class="summary">
        <h2>Summary</h2>
        <p>This report contains visual regression test results for Journey 1 UI components.</p>
        <p>Screenshots are captured at various states and compared against baselines.</p>
        <p>Check the test-results directory for detailed diffs and actual vs expected comparisons.</p>
    </div>

    <div class="test-section">
        <h2>Test Categories</h2>
        <ul>
            <li>Initial State Visual Validation</li>
            <li>Interactive State Visual Validation</li>
            <li>Framework Analysis Visual Validation</li>
            <li>Error State Visual Validation</li>
            <li>Responsive Design Visual Validation</li>
            <li>Cross-Browser Visual Consistency</li>
        </ul>
    </div>

    <div class="test-section">
        <h2>Key Files</h2>
        <p><strong>Baselines:</strong> ${baselineDir}</p>
        <p><strong>Diffs:</strong> ${diffDir}</p>
        <p><strong>Test Results:</strong> test-results/</p>
    </div>
</body>
</html>`;

    fs.writeFileSync(reportPath, reportContent);
    console.log(`📊 Visual regression report generated: ${reportPath}`);
  });
});
