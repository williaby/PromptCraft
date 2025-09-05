import { Page, Browser, expect } from '@playwright/test';
import { Journey1Page } from '../fixtures/Journey1Page';

export class TestUtils {
  /**
   * Wait for Gradio components to be fully loaded and interactive
   */
  static async waitForGradioLoad(page: Page, timeout = 30000) {
    // Wait for main Gradio container (Gradio v5)
    await page.waitForSelector('.gradio-container', { timeout });
    
    // Wait for any Gradio loading indicators to disappear
    await page.waitForFunction(() => {
      const loadingElements = document.querySelectorAll(
        '.loading, .spinner, [data-testid="loading"], .gradio-loading'
      );
      return loadingElements.length === 0;
    }, { timeout: 15000 });
    
    // Additional stabilization wait
    await page.waitForTimeout(1000);
  }

  /**
   * Upload a test file and wait for processing
   */
  static async uploadTestFile(
    page: Page, 
    fileSelector: string, 
    filePath: string,
    expectSuccess = true
  ) {
    // Upload the file
    await page.setInputFiles(fileSelector, filePath);
    
    // Wait for file processing indicators
    try {
      await page.waitForSelector('.file-processing, .uploading', { timeout: 2000 });
      await page.waitForSelector('.file-processing, .uploading', { state: 'hidden', timeout: 10000 });
    } catch {
      // Processing indicators might not appear for quick uploads
    }
    
    if (expectSuccess) {
      // Verify no error messages
      const errorElements = await page.locator('.error, .alert-danger').count();
      expect(errorElements).toBe(0);
    }
    
    return true;
  }

  /**
   * Validate C.R.E.A.T.E. framework breakdown in response
   */
  static async validateCREATEBreakdown(page: Page) {
    const requiredSections = [
      'Context:',
      'Request:',
      'Examples:',
      'Augmentations:',
      'Tone:',
      'Evaluation:'
    ];

    const results = {
      allPresent: true,
      missing: [] as string[],
      present: [] as string[]
    };

    for (const section of requiredSections) {
      try {
        await page.waitForSelector(`text=${section}`, { timeout: 5000 });
        results.present.push(section);
      } catch {
        results.allPresent = false;
        results.missing.push(section);
      }
    }

    return results;
  }

  /**
   * Measure response time for an operation
   */
  static async measureResponseTime(page: Page, operation: () => Promise<void>) {
    const startTime = Date.now();
    await operation();
    const endTime = Date.now();
    return endTime - startTime;
  }

  /**
   * Create a test session with specific configuration
   */
  static async createTestSession(page: Page, config: {
    userTier?: 'free' | 'pro' | 'enterprise';
    model?: string;
    clearStorage?: boolean;
  } = {}) {
    if (config.clearStorage !== false) {
      // Clear browser storage
      await page.context().clearCookies();
      await page.evaluate(() => {
        localStorage.clear();
        sessionStorage.clear();
      });
    }

    // Navigate to the app
    await page.goto('/');
    await this.waitForGradioLoad(page);

    // Set user tier if specified
    if (config.userTier) {
      await page.evaluate((tier) => {
        localStorage.setItem('userTier', tier);
      }, config.userTier);
    }

    // Select model if specified
    if (config.model) {
      try {
        await page.selectOption('select:has-text("Model")', config.model);
      } catch {
        // Model selector might not be visible or use different format
        console.warn(`Could not select model: ${config.model}`);
      }
    }

    return page;
  }

  /**
   * Generate test data for different input types
   */
  static getTestData() {
    return {
      simplePrompt: "Help me write a Python function that sorts a list",
      complexPrompt: `I need to create a comprehensive data analysis pipeline that:
        1. Ingests CSV data from multiple sources
        2. Performs data cleaning and validation
        3. Applies statistical analysis and machine learning models
        4. Generates visualizations and reports
        5. Exports results in multiple formats
        
        The pipeline should be scalable, maintainable, and well-documented.
        Please provide a detailed implementation with error handling and testing.`,
      longPrompt: "A".repeat(10000), // 10k characters
      specialCharacters: "Test with émojis 🚀 and spëcial châractérs: <script>alert('xss')</script>",
      codeSnippet: `def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)`,
      
      // Different content types for file testing
      markdownContent: `# Test Document
        
        This is a **test** document for *PromptCraft* testing.
        
        ## Features
        - Markdown formatting
        - Code blocks
        - Lists
        
        \`\`\`python
        print("Hello, World!")
        \`\`\``,
      
      csvContent: `Name,Age,City
        John Doe,30,New York
        Jane Smith,25,Los Angeles
        Bob Johnson,35,Chicago`,
      
      jsonContent: `{
        "name": "test-data",
        "version": "1.0",
        "description": "Test JSON data for PromptCraft",
        "items": [
          {"id": 1, "value": "item1"},
          {"id": 2, "value": "item2"}
        ]
      }`
    };
  }

  /**
   * Create temporary test files
   */
  static async createTestFiles(baseDir: string) {
    const fs = require('fs').promises;
    const path = require('path');
    const testData = this.getTestData();

    const files = {
      'test.txt': 'Simple text file content for testing PromptCraft file upload.',
      'test.md': testData.markdownContent,
      'test.csv': testData.csvContent,
      'test.json': testData.jsonContent,
      'large-file.txt': 'X'.repeat(50 * 1024 * 1024), // 50MB file
      'empty-file.txt': '',
      'special-chars.txt': 'File with spëcial châractérs and émojis 🚀'
    };

    const createdFiles = [];
    for (const [filename, content] of Object.entries(files)) {
      const filePath = path.join(baseDir, filename);
      await fs.writeFile(filePath, content, 'utf8');
      createdFiles.push(filePath);
    }

    return createdFiles;
  }

  /**
   * Wait for network requests to complete
   */
  static async waitForNetworkIdle(page: Page, timeout = 5000) {
    await page.waitForLoadState('networkidle', { timeout });
  }

  /**
   * Test rate limiting by making rapid requests
   */
  static async testRateLimit(journey1Page: Journey1Page, requestCount = 35) {
    const results = [];
    
    for (let i = 0; i < requestCount; i++) {
      const startTime = Date.now();
      
      try {
        await journey1Page.enterPrompt(`Test prompt ${i}`);
        await journey1Page.enhancePrompt(5000); // Short timeout for rate limit testing
        
        const isRateLimited = await journey1Page.page.isRateLimited();
        results.push({
          requestNumber: i + 1,
          success: !isRateLimited,
          rateLimited: isRateLimited,
          responseTime: Date.now() - startTime
        });
        
        if (isRateLimited) {
          break; // Stop once rate limited
        }
        
      } catch (error) {
        results.push({
          requestNumber: i + 1,
          success: false,
          error: error.message,
          responseTime: Date.now() - startTime
        });
      }
      
      // Small delay between requests
      await journey1Page.page.waitForTimeout(100);
    }
    
    return results;
  }

  /**
   * Validate accessibility compliance
   */
  static async checkAccessibility(page: Page) {
    // Basic accessibility checks
    const issues = [];

    // Check for alt text on images
    const images = await page.locator('img').all();
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      if (!alt) {
        issues.push('Image missing alt text');
      }
    }

    // Check for form labels
    const inputs = await page.locator('input, textarea, select').all();
    for (const input of inputs) {
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      
      if (id) {
        const label = await page.locator(`label[for="${id}"]`).count();
        if (label === 0 && !ariaLabel) {
          issues.push('Input missing label');
        }
      }
    }

    // Check color contrast (basic check)
    const elements = await page.locator('button, .btn, a').all();
    for (const element of elements) {
      const styles = await element.evaluate((el) => {
        const computedStyle = window.getComputedStyle(el);
        return {
          color: computedStyle.color,
          backgroundColor: computedStyle.backgroundColor
        };
      });
      
      // Basic contrast validation would go here
      // This is a simplified check - in real scenarios, use axe-core
    }

    return {
      passed: issues.length === 0,
      issues
    };
  }

  /**
   * Simulate network conditions (slow, offline, etc.)
   */
  static async simulateNetworkConditions(
    page: Page, 
    condition: 'slow' | 'offline' | 'normal'
  ) {
    const client = await page.context().newCDPSession(page);
    
    switch (condition) {
      case 'slow':
        await client.send('Network.emulateNetworkConditions', {
          offline: false,
          downloadThroughput: 50 * 1024, // 50KB/s
          uploadThroughput: 20 * 1024,   // 20KB/s
          latency: 500 // 500ms
        });
        break;
        
      case 'offline':
        await client.send('Network.emulateNetworkConditions', {
          offline: true,
          downloadThroughput: 0,
          uploadThroughput: 0,
          latency: 0
        });
        break;
        
      case 'normal':
      default:
        await client.send('Network.emulateNetworkConditions', {
          offline: false,
          downloadThroughput: -1,
          uploadThroughput: -1,
          latency: 0
        });
        break;
    }
  }

  /**
   * Get browser console logs
   */
  static async getConsoleLogs(page: Page) {
    const logs = [];
    
    page.on('console', (msg) => {
      logs.push({
        type: msg.type(),
        text: msg.text(),
        timestamp: new Date().toISOString()
      });
    });
    
    return logs;
  }

  /**
   * Take performance snapshot
   */
  static async getPerformanceSnapshot(page: Page) {
    const metrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const resources = performance.getEntriesByType('resource');
      
      return {
        navigation: {
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
          loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
          totalTime: navigation.loadEventEnd - navigation.fetchStart,
          dns: navigation.domainLookupEnd - navigation.domainLookupStart,
          tcp: navigation.connectEnd - navigation.connectStart,
          request: navigation.responseStart - navigation.requestStart,
          response: navigation.responseEnd - navigation.responseStart,
          domProcessing: navigation.domComplete - navigation.domLoading
        },
        resources: resources.length,
        memory: (performance as any).memory ? {
          used: (performance as any).memory.usedJSHeapSize,
          total: (performance as any).memory.totalJSHeapSize,
          limit: (performance as any).memory.jsHeapSizeLimit
        } : null
      };
    });
    
    return metrics;
  }
}

export default TestUtils;