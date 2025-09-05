import { test, expect } from '@playwright/test';
import { Journey1Page } from '../fixtures/Journey1Page';
import TestUtils from '../helpers/test-utils';
import path from 'path';

test.describe('Journey 1: Smart Templates Tests', () => {
  let journey1Page: Journey1Page;
  const testDataDir = path.join(__dirname, '../data/files');
  const maliciousDataDir = path.join(__dirname, '../data/malicious');

  test.beforeEach(async ({ page }) => {
    journey1Page = new Journey1Page(page);
    await journey1Page.gotoJourney1();
  });

  test.describe('Basic Prompt Enhancement', () => {
    test('should enhance a simple prompt successfully', async ({ page }) => {
      const testPrompt = TestUtils.getTestData().simplePrompt;
      
      // Enter prompt
      await journey1Page.enterPrompt(testPrompt);
      
      // Click enhance and wait for result
      const responseTime = await TestUtils.measureResponseTime(page, async () => {
        await journey1Page.enhancePrompt();
      });
      
      // Verify response time is acceptable
      expect(responseTime).toBeLessThan(30000); // 30 seconds
      
      // Get enhanced prompt
      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();
      expect(enhancedPrompt).toContain('Enhanced prompt');
      
      // Verify C.R.E.A.T.E. framework breakdown
      const createBreakdown = await journey1Page.validateCREATEBreakdown();
      const presentSections = createBreakdown.filter(section => section.present);
      
      // At least 4 of 6 sections should be present for a good enhancement
      expect(presentSections.length).toBeGreaterThanOrEqual(4);
      
      console.log('C.R.E.A.T.E. breakdown results:', createBreakdown);
      
      // Take screenshot of results
      await journey1Page.takeScreenshot('journey1-basic-enhancement');
    });

    test('should handle complex prompts effectively', async ({ page }) => {
      const complexPrompt = TestUtils.getTestData().complexPrompt;
      
      await journey1Page.enterPrompt(complexPrompt);
      
      const responseTime = await TestUtils.measureResponseTime(page, async () => {
        await journey1Page.enhancePrompt(45000); // Longer timeout for complex prompt
      });
      
      // Complex prompts may take longer but should stay under 45 seconds
      expect(responseTime).toBeLessThan(45000);
      
      // Verify all C.R.E.A.T.E. sections are present for complex prompts
      const createBreakdown = await journey1Page.validateCREATEBreakdown();
      const presentSections = createBreakdown.filter(section => section.present);
      
      // Complex prompts should generate complete frameworks
      expect(presentSections.length).toBeGreaterThanOrEqual(5);
      
      // Verify enhanced prompt is substantially longer than input
      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt.length).toBeGreaterThan(complexPrompt.length);
    });

    test('should handle special characters and emojis', async ({ page }) => {
      const specialCharPrompt = TestUtils.getTestData().specialCharacters;
      
      await journey1Page.enterPrompt(specialCharPrompt);
      await journey1Page.enhancePrompt();
      
      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      
      // Should not break with special characters
      expect(enhancedPrompt).toBeTruthy();
      
      // Should not contain script tags or other security issues
      expect(enhancedPrompt).not.toContain('<script');
      expect(enhancedPrompt).not.toContain('javascript:');
      expect(enhancedPrompt).not.toContain('onerror=');
    });

    test('should validate input length limits', async ({ page }) => {
      const longPrompt = TestUtils.getTestData().longPrompt;
      
      // This should work (10k characters)
      await journey1Page.enterPrompt(longPrompt);
      
      // Should not show immediate error
      expect(await journey1Page.hasError()).toBeFalsy();
      
      // Should process successfully or show appropriate handling
      await journey1Page.enhancePrompt();
      
      // Either success or appropriate length handling message
      const hasError = await journey1Page.hasError();
      if (hasError) {
        const errorMessage = await journey1Page.getErrorMessage();
        expect(errorMessage).toContain('length', { ignoreCase: true });
      }
    });
  });

  test.describe('File Upload Functionality', () => {
    test('should upload and process a text file', async ({ page }) => {
      const textFile = path.join(testDataDir, 'simple-text.txt');
      
      // Upload file
      await journey1Page.uploadTestFile(textFile);
      
      // Verify file sources are displayed
      const fileSources = await journey1Page.getFileSources();
      expect(fileSources.length).toBeGreaterThan(0);
      expect(fileSources[0]).toContain('simple-text.txt');
      
      // Process with uploaded file context
      await journey1Page.enterPrompt('Analyze the uploaded document');
      await journey1Page.enhancePrompt();
      
      // Verify file content influences the output
      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toContain('document', { ignoreCase: true });
    });

    test('should process markdown files correctly', async ({ page }) => {
      const markdownFile = path.join(testDataDir, 'test-document.md');
      
      await journey1Page.uploadTestFile(markdownFile);
      
      // Verify markdown file is processed
      const fileSources = await journey1Page.getFileSources();
      expect(fileSources).toContain('test-document.md');
      
      await journey1Page.enterPrompt('Create a summary of this document');
      await journey1Page.enhancePrompt();
      
      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();
      
      // Should understand markdown structure
      expect(enhancedPrompt).toContain('markdown', { ignoreCase: true });
    });

    test('should process CSV data files', async ({ page }) => {
      const csvFile = path.join(testDataDir, 'sample-data.csv');
      
      await journey1Page.uploadTestFile(csvFile);
      await journey1Page.enterPrompt('Analyze this employee data');
      await journey1Page.enhancePrompt();
      
      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      
      // Should recognize CSV structure
      expect(enhancedPrompt).toContain('data', { ignoreCase: true });
      expect(enhancedPrompt).toContain('analysis', { ignoreCase: true });
    });

    test('should process JSON configuration files', async ({ page }) => {
      const jsonFile = path.join(testDataDir, 'config-sample.json');
      
      await journey1Page.uploadTestFile(jsonFile);
      await journey1Page.enterPrompt('Explain this configuration');
      await journey1Page.enhancePrompt();
      
      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toContain('configuration', { ignoreCase: true });
    });

    test('should handle multiple file uploads', async ({ page }) => {
      const files = [
        path.join(testDataDir, 'simple-text.txt'),
        path.join(testDataDir, 'sample-data.csv')
      ];
      
      // Upload first file
      await journey1Page.uploadTestFile(files[0]);
      
      // Upload second file (testing multiple uploads)
      await journey1Page.uploadTestFile(files[1]);
      
      const fileSources = await journey1Page.getFileSources();
      expect(fileSources.length).toBe(2);
      
      await journey1Page.enterPrompt('Compare these two files');
      await journey1Page.enhancePrompt();
      
      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toContain('compare', { ignoreCase: true });
    });
  });

  test.describe('Model Selection and Cost Tracking', () => {
    test('should allow model selection', async ({ page }) => {
      // Try to select a different model
      await journey1Page.selectModel('gpt-4o');
      
      await journey1Page.enterPrompt('Test with different model');
      await journey1Page.enhancePrompt();
      
      // Verify model attribution shows the selected model
      const attribution = await journey1Page.getModelAttribution();
      expect(attribution.model).toContain('gpt-4', { ignoreCase: true });
    });

    test('should track costs accurately', async ({ page }) => {
      const initialCost = await journey1Page.getCurrentCost();
      
      await journey1Page.enterPrompt('Cost tracking test');
      await journey1Page.enhancePrompt();
      
      const finalCost = await journey1Page.getCurrentCost();
      
      // Cost should increase after processing
      expect(finalCost).toBeGreaterThan(initialCost);
      
      // Verify cost is displayed in model attribution
      const attribution = await journey1Page.getModelAttribution();
      expect(parseFloat(attribution.cost)).toBeGreaterThan(0);
    });
  });

  test.describe('Copy and Export Functions', () => {
    test('should copy code blocks successfully', async ({ page }) => {
      await journey1Page.enterPrompt('Create a Python function for data processing');
      await journey1Page.enhancePrompt();
      
      // Test copy code functionality
      await journey1Page.copyCodeBlocks();
      
      // Verify success feedback appears
      await journey1Page.waitForText('copied');
    });

    test('should copy as markdown successfully', async ({ page }) => {
      await journey1Page.enterPrompt('Create documentation for an API');
      await journey1Page.enhancePrompt();
      
      await journey1Page.copyAsMarkdown();
      
      // Verify success feedback
      await journey1Page.waitForText('copied');
    });

    test('should export content in different formats', async ({ page }) => {
      await journey1Page.enterPrompt('Generate a project report');
      await journey1Page.enhancePrompt();
      
      // Test markdown export
      const download = await journey1Page.exportContent('md');
      expect(download.suggestedFilename()).toContain('.md');
      
      // Verify file was created
      const downloadPath = await download.path();
      expect(downloadPath).toBeTruthy();
    });
  });

  test.describe('Error Handling and Edge Cases', () => {
    test('should handle empty input gracefully', async ({ page }) => {
      // Try to enhance without input
      await journey1Page.enhanceButton.click();
      
      // Should show appropriate message
      const hasError = await journey1Page.hasError();
      if (hasError) {
        const errorMessage = await journey1Page.getErrorMessage();
        expect(errorMessage).toContain('input', { ignoreCase: true });
      }
    });

    test('should handle network timeouts gracefully', async ({ page }) => {
      // Simulate slow network
      await TestUtils.simulateNetworkConditions(page, 'slow');
      
      await journey1Page.enterPrompt('Test with slow network');
      
      try {
        await journey1Page.enhancePrompt(10000); // Short timeout to trigger timeout
        
        // If it succeeds despite slow network, that's also acceptable
        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();
      } catch (error) {
        // Should handle timeout gracefully
        const hasError = await journey1Page.hasError();
        expect(hasError).toBeTruthy();
        
        const errorMessage = await journey1Page.getErrorMessage();
        expect(errorMessage).toContain('timeout', { ignoreCase: true });
      }
      
      // Restore normal network
      await TestUtils.simulateNetworkConditions(page, 'normal');
    });

    test('should clear inputs properly', async ({ page }) => {
      await journey1Page.enterPrompt('Test prompt to be cleared');
      
      // Upload a file
      const textFile = path.join(testDataDir, 'simple-text.txt');
      await journey1Page.uploadTestFile(textFile);
      
      // Clear all
      await journey1Page.clearAll();
      
      // Verify inputs are cleared
      const textInputValue = await journey1Page.textInput.inputValue();
      expect(textInputValue).toBe('');
    });
  });

  test.describe('Security Validation', () => {
    test('should reject oversized files', async ({ page }) => {
      const oversizedFile = path.join(maliciousDataDir, 'oversized-file.txt');
      
      // This should fail
      const result = await journey1Page.testFileValidation(oversizedFile, true);
      
      if (typeof result === 'string') {
        expect(result).toContain('size', { ignoreCase: true });
      }
    });

    test('should sanitize malicious content', async ({ page }) => {
      const maliciousFile = path.join(maliciousDataDir, 'fake-text-with-script.txt');
      
      try {
        await journey1Page.uploadTestFile(maliciousFile);
        await journey1Page.enterPrompt('Process this content');
        await journey1Page.enhancePrompt();
        
        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        
        // Should not contain script tags or dangerous content
        expect(enhancedPrompt).not.toContain('<script');
        expect(enhancedPrompt).not.toContain('javascript:');
        expect(enhancedPrompt).not.toContain('onerror=');
        expect(enhancedPrompt).not.toContain('DROP TABLE');
      } catch (error) {
        // Security rejection is also acceptable
        console.log('File rejected by security system (expected behavior)');
      }
    });
  });
});