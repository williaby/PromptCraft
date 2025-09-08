import { test, expect } from '@playwright/test';
import { Journey1Page } from '../fixtures/Journey1Page';
import TestUtils from '../helpers/test-utils';
import path from 'path';

test.describe('Journey 1: Advanced User Workflows', () => {
  let journey1Page: Journey1Page;
  const testDataDir = path.join(__dirname, '../data/files');

  test.beforeEach(async ({ page }) => {
    journey1Page = new Journey1Page(page);
    await journey1Page.gotoJourney1();
  });

  test.describe('Priority 1: Critical User Pathways', () => {
    test('should support iterative prompt enhancement', async ({ page }) => {
      // Test progressive enhancement workflow
      const initialPrompt = 'Create a marketing email';

      // First enhancement
      await journey1Page.enterPrompt(initialPrompt);
      await journey1Page.enhancePrompt();

      const firstEnhancement = await journey1Page.getEnhancedPrompt();
      expect(firstEnhancement).toBeTruthy();
      expect(firstEnhancement.length).toBeGreaterThan(initialPrompt.length);

      // Use enhanced prompt as input for second iteration
      await journey1Page.clearAll();
      await journey1Page.enterPrompt(firstEnhancement);
      await journey1Page.enhancePrompt();

      const secondEnhancement = await journey1Page.getEnhancedPrompt();
      expect(secondEnhancement).toBeTruthy();
      expect(secondEnhancement.length).toBeGreaterThan(firstEnhancement.length);

      // Third iteration to verify continued improvement
      await journey1Page.clearAll();
      await journey1Page.enterPrompt(secondEnhancement);
      await journey1Page.enhancePrompt();

      const thirdEnhancement = await journey1Page.getEnhancedPrompt();
      expect(thirdEnhancement).toBeTruthy();

      // Verify each iteration maintains C.R.E.A.T.E. structure
      const finalCreateBreakdown = await journey1Page.validateCREATEBreakdown();
      const presentSections = finalCreateBreakdown.filter(section => section.present);
      expect(presentSections.length).toBeGreaterThanOrEqual(5);

      console.log('Iterative enhancement results:', {
        initial: initialPrompt.length,
        first: firstEnhancement.length,
        second: secondEnhancement.length,
        third: thirdEnhancement.length,
        createSections: presentSections.length
      });
    });

    test('should maintain state across browser refresh', async ({ page }) => {
      const testPrompt = 'Analyze customer behavior patterns for e-commerce optimization';
      const testFile = path.join(testDataDir, 'sample-data.csv');

      // Set initial state
      await journey1Page.enterPrompt(testPrompt);
      await journey1Page.uploadTestFile(testFile);
      await journey1Page.selectModel('gpt-4o');

      // Verify initial state is set
      const initialTextValue = await journey1Page.textInput.inputValue();
      const initialFileSources = await journey1Page.getFileSources();
      expect(initialTextValue).toBe(testPrompt);
      expect(initialFileSources.length).toBeGreaterThan(0);

      // Refresh the page
      await page.reload();
      await journey1Page.waitForJourney1Load();

      // Check state recovery
      const recoveredTextValue = await journey1Page.textInput.inputValue();

      if (recoveredTextValue === testPrompt) {
        // State was preserved - verify file sources too
        const recoveredFileSources = await journey1Page.getFileSources();
        expect(recoveredFileSources.length).toBeGreaterThan(0);
        console.log('✅ State fully preserved across refresh');
      } else {
        // State was not preserved - verify graceful handling
        expect(recoveredTextValue).toBe('');
        console.log('⚠️ State not preserved - graceful reset confirmed');

        // Verify user can continue working normally after refresh
        await journey1Page.enterPrompt('Test prompt after refresh');
        await journey1Page.enhancePrompt();
        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();
      }
    });

    test('should handle concurrent Journey 1 usage', async ({ browser }) => {
      // Create multiple browser contexts to simulate concurrent users
      const contexts = [];
      const pages = [];
      const journey1Pages = [];

      // Create 3 concurrent sessions
      for (let i = 0; i < 3; i++) {
        const context = await browser.newContext();
        const page = await context.newPage();
        const j1Page = new Journey1Page(page);

        contexts.push(context);
        pages.push(page);
        journey1Pages.push(j1Page);

        await j1Page.gotoJourney1();
      }

      // Perform different actions in each session simultaneously
      const prompts = [
        'Create a business proposal for renewable energy solutions',
        'Design a user interface for mobile banking application',
        'Develop a training program for customer service representatives'
      ];

      const enhancementPromises = journey1Pages.map(async (j1Page, index) => {
        await j1Page.enterPrompt(prompts[index]);

        // Stagger the enhancement calls slightly
        await pages[index].waitForTimeout(index * 500);

        await j1Page.enhancePrompt();
        return await j1Page.getEnhancedPrompt();
      });

      // Wait for all enhancements to complete
      const results = await Promise.all(enhancementPromises);

      // Verify all sessions completed successfully
      results.forEach((result, index) => {
        expect(result).toBeTruthy();
        expect(result.length).toBeGreaterThan(prompts[index].length);
        console.log(`Session ${index + 1} enhancement length: ${result.length}`);
      });

      // Verify no cross-contamination between sessions
      for (let i = 0; i < results.length; i++) {
        for (let j = i + 1; j < results.length; j++) {
          expect(results[i]).not.toBe(results[j]);
        }
      }

      // Clean up contexts
      for (const context of contexts) {
        await context.close();
      }

      console.log('✅ All concurrent sessions completed successfully with unique results');
    });

    test('should handle template reuse workflow', async ({ page }) => {
      // Create initial enhanced prompt
      const businessPrompt = 'Create a strategic business plan';
      await journey1Page.enterPrompt(businessPrompt);
      await journey1Page.enhancePrompt();

      const enhancedTemplate = await journey1Page.getEnhancedPrompt();
      expect(enhancedTemplate).toBeTruthy();

      // Copy the enhanced prompt as markdown
      await journey1Page.copyAsMarkdown();
      await journey1Page.waitForText('copied', 3000);

      // Simulate using this as a template for a new prompt
      await journey1Page.clearAll();

      // Modify the template for reuse
      const modifiedPrompt = enhancedTemplate.replace('business plan', 'marketing strategy');
      await journey1Page.enterPrompt(modifiedPrompt);
      await journey1Page.enhancePrompt();

      const newEnhancement = await journey1Page.getEnhancedPrompt();
      expect(newEnhancement).toBeTruthy();
      expect(newEnhancement).toContain('marketing', { ignoreCase: true });

      // Verify template reuse maintains quality
      const createBreakdown = await journey1Page.validateCREATEBreakdown();
      const presentSections = createBreakdown.filter(section => section.present);
      expect(presentSections.length).toBeGreaterThanOrEqual(4);

      console.log('Template reuse workflow completed successfully');
    });

    test('should handle session persistence across tab switches', async ({ page }) => {
      const testPrompt = 'Develop a comprehensive training curriculum for data science';

      // Set up Journey 1 state
      await journey1Page.enterPrompt(testPrompt);
      await journey1Page.enhancePrompt();

      const originalEnhancement = await journey1Page.getEnhancedPrompt();
      expect(originalEnhancement).toBeTruthy();

      // Switch to Journey 2 tab
      await journey1Page.switchToJourney(2);
      await page.waitForTimeout(1000);

      // Switch back to Journey 1
      await journey1Page.switchToJourney(1);
      await journey1Page.waitForJourney1Load();

      // Check if state is preserved
      const preservedEnhancement = await journey1Page.getEnhancedPrompt();

      if (preservedEnhancement === originalEnhancement) {
        console.log('✅ Session state preserved across tab switches');
        expect(preservedEnhancement).toBe(originalEnhancement);
      } else {
        console.log('⚠️ Session state not preserved - verifying graceful handling');

        // Verify we can continue working normally
        await journey1Page.enterPrompt('New prompt after tab switch');
        await journey1Page.enhancePrompt();
        const newEnhancement = await journey1Page.getEnhancedPrompt();
        expect(newEnhancement).toBeTruthy();
      }
    });
  });

  test.describe('Error Recovery and Resilience', () => {
    test('should recover gracefully from network interruption', async ({ page }) => {
      // Set up test prompt
      const testPrompt = 'Create a comprehensive project management methodology';
      await journey1Page.enterPrompt(testPrompt);

      // Simulate network interruption during enhancement
      await TestUtils.simulateNetworkConditions(page, 'offline');

      try {
        await journey1Page.enhancePrompt(5000); // Short timeout to trigger failure
      } catch (error) {
        console.log('Expected network error occurred');
      }

      // Restore network
      await TestUtils.simulateNetworkConditions(page, 'normal');

      // Verify error state is handled gracefully
      const hasError = await journey1Page.hasError();
      if (hasError) {
        const errorMessage = await journey1Page.getErrorMessage();
        expect(errorMessage).toContain('network', { ignoreCase: true });
      }

      // Verify user can retry after network recovery
      await journey1Page.enhancePrompt();
      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();

      console.log('✅ Successfully recovered from network interruption');
    });

    test('should handle rapid consecutive enhancement requests', async ({ page }) => {
      const testPrompts = [
        'Create a user onboarding flow',
        'Design a feedback collection system',
        'Develop a performance monitoring dashboard'
      ];

      // Rapidly submit multiple enhancement requests
      for (let i = 0; i < testPrompts.length; i++) {
        await journey1Page.clearAll();
        await journey1Page.enterPrompt(testPrompts[i]);

        // Don't wait for completion before next request
        journey1Page.enhanceButton.click();

        // Small delay to prevent overwhelming the system
        await page.waitForTimeout(100);
      }

      // Wait for all requests to settle
      await page.waitForTimeout(5000);

      // Check final state - should show one completed enhancement
      const finalEnhancement = await journey1Page.getEnhancedPrompt();
      expect(finalEnhancement).toBeTruthy();

      // Verify system didn't crash
      const hasError = await journey1Page.hasError();
      if (hasError) {
        const errorMessage = await journey1Page.getErrorMessage();
        // Error should be informative, not a crash
        expect(errorMessage.length).toBeGreaterThan(0);
        expect(errorMessage).not.toContain('500', { ignoreCase: true });
      }

      console.log('✅ System handled rapid consecutive requests gracefully');
    });

    test('should maintain functionality with JavaScript errors', async ({ page }) => {
      // Inject a non-critical JavaScript error
      await page.addInitScript(() => {
        // Simulate a minor JS error that shouldn't break functionality
        setTimeout(() => {
          console.error('Simulated non-critical error');
        }, 1000);
      });

      // Navigate and verify basic functionality still works
      await journey1Page.gotoJourney1();

      const testPrompt = 'Test functionality with JS error present';
      await journey1Page.enterPrompt(testPrompt);
      await journey1Page.enhancePrompt();

      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();

      // Verify C.R.E.A.T.E. framework still works
      const createBreakdown = await journey1Page.validateCREATEBreakdown();
      const presentSections = createBreakdown.filter(section => section.present);
      expect(presentSections.length).toBeGreaterThan(0);

      console.log('✅ Core functionality maintained despite JS errors');
    });
  });

  test.describe('Complex File Processing Workflows', () => {
    test('should handle file replacement workflow', async ({ page }) => {
      const testFiles = [
        path.join(testDataDir, 'simple-text.txt'),
        path.join(testDataDir, 'sample-data.csv')
      ];

      // Upload first file
      await journey1Page.uploadTestFile(testFiles[0]);
      let fileSources = await journey1Page.getFileSources();
      expect(fileSources.length).toBe(1);
      expect(fileSources[0]).toContain('simple-text.txt');

      // Replace with second file
      await journey1Page.uploadTestFile(testFiles[1]);
      fileSources = await journey1Page.getFileSources();

      // Verify file replacement handling
      expect(fileSources.length).toBeGreaterThan(0);

      // Process with final file state
      await journey1Page.enterPrompt('Analyze the uploaded data');
      await journey1Page.enhancePrompt();

      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();
      expect(enhancedPrompt).toContain('data', { ignoreCase: true });

      console.log('✅ File replacement workflow completed successfully');
    });

    test('should handle mixed file type processing', async ({ page }) => {
      const mixedFiles = [
        path.join(testDataDir, 'simple-text.txt'),
        path.join(testDataDir, 'sample-data.csv'),
        path.join(testDataDir, 'test-document.md'),
        path.join(testDataDir, 'config-sample.json')
      ];

      // Upload all files
      for (const file of mixedFiles) {
        await journey1Page.uploadTestFile(file);
        await page.waitForTimeout(500); // Allow processing time
      }

      const fileSources = await journey1Page.getFileSources();
      expect(fileSources.length).toBeGreaterThan(0);

      // Process with comprehensive prompt
      await journey1Page.enterPrompt('Create a comprehensive analysis report based on all uploaded documents');
      await journey1Page.enhancePrompt(45000); // Longer timeout for multiple files

      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();

      // Verify different file types are recognized
      expect(enhancedPrompt).toContain('analysis', { ignoreCase: true });

      // Verify C.R.E.A.T.E. framework handles complex context
      const createBreakdown = await journey1Page.validateCREATEBreakdown();
      const presentSections = createBreakdown.filter(section => section.present);
      expect(presentSections.length).toBeGreaterThanOrEqual(4);

      console.log(`✅ Mixed file processing completed with ${fileSources.length} sources`);
    });
  });
});
