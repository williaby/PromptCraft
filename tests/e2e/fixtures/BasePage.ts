import { Page, Locator, expect } from '@playwright/test';

export class BasePage {
  readonly page: Page;
  
  // Common selectors for all pages
  readonly headerTitle: Locator;
  readonly footerContainer: Locator;
  readonly gradioContainer: Locator;
  
  // Tab selectors
  readonly journey1Tab: Locator;
  readonly journey2Tab: Locator;
  readonly journey3Tab: Locator;
  readonly journey4Tab: Locator;
  readonly adminTab: Locator;
  
  constructor(page: Page) {
    this.page = page;
    
    // Initialize common locators for Gradio v5
    this.headerTitle = page.locator('h1:has-text("PromptCraft-Hybrid")');
    this.footerContainer = page.getByText('Session:', { exact: false }).first();
    this.gradioContainer = page.locator('.gradio-container').first();
    
    // Tab locators for Gradio v5 - use role="tab" to target the active tab buttons
    this.journey1Tab = page.locator('button[role="tab"]:has-text("Journey 1: Smart Templates")');
    this.journey2Tab = page.locator('button[role="tab"]:has-text("Journey 2: Intelligent Search")');
    this.journey3Tab = page.locator('button[role="tab"]:has-text("Journey 3: IDE Integration")');
    this.journey4Tab = page.locator('button[role="tab"]:has-text("Journey 4: Autonomous Workflows")');
    this.adminTab = page.locator('button[role="tab"]:has-text("Admin")');
  }

  /**
   * Navigate to the main page and wait for it to load
   */
  async goto() {
    await this.page.goto('/');
    await this.waitForPageLoad();
  }

  /**
   * Wait for the page to fully load
   */
  async waitForPageLoad() {
    // Wait for the main title to be visible (indicates Gradio loaded)
    await this.headerTitle.waitFor({ state: 'visible', timeout: 30000 });
    
    // Wait for any loading indicators to disappear
    await this.page.waitForFunction(() => {
      const loadingElements = document.querySelectorAll('.loading, .spinner, [data-testid="loading"]');
      return loadingElements.length === 0;
    }, { timeout: 5000 }).catch(() => {}); // Don't fail if no loading indicators
    
    // Additional wait for Gradio components to be interactive
    await this.page.waitForTimeout(1000);
  }

  /**
   * Take a screenshot with a descriptive name
   */
  async takeScreenshot(name: string) {
    await this.page.screenshot({ 
      path: `test-results/screenshots/${name}-${Date.now()}.png`,
      fullPage: true 
    });
  }

  /**
   * Wait for a network request to complete
   */
  async waitForApiResponse(urlPattern: string | RegExp) {
    return await this.page.waitForResponse(response => {
      const url = response.url();
      if (typeof urlPattern === 'string') {
        return url.includes(urlPattern);
      } else {
        return urlPattern.test(url);
      }
    });
  }

  /**
   * Check if an element is visible and enabled
   */
  async isInteractive(locator: Locator): Promise<boolean> {
    try {
      await expect(locator).toBeVisible();
      await expect(locator).toBeEnabled();
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Fill text input with typing simulation
   */
  async typeText(locator: Locator, text: string, delay = 50) {
    await locator.click();
    await locator.clear();
    await locator.type(text, { delay });
  }

  /**
   * Upload a file to a file input
   */
  async uploadFile(fileInputLocator: Locator, filePath: string) {
    await fileInputLocator.setInputFiles(filePath);
  }

  /**
   * Wait for text to appear in any element
   */
  async waitForText(text: string, timeout = 10000) {
    await this.page.waitForSelector(`text=${text}`, { timeout });
  }

  /**
   * Switch to a specific journey tab
   */
  async switchToJourney(journeyNumber: 1 | 2 | 3 | 4) {
    const tabMap = {
      1: this.journey1Tab,
      2: this.journey2Tab,
      3: this.journey3Tab,
      4: this.journey4Tab
    };
    
    const tab = tabMap[journeyNumber];
    await tab.click();
    await this.page.waitForTimeout(500); // Allow tab to activate
  }

  /**
   * Get current session information from footer
   */
  async getSessionInfo() {
    await this.footerContainer.waitFor({ state: 'visible' });
    const footerText = await this.footerContainer.textContent();
    
    // Parse session duration, model, and request count from footer
    const sessionDurationMatch = footerText?.match(/Session: ([\d.]+h)/);
    const modelMatch = footerText?.match(/Model: ([^\s|]+)/);
    const requestsMatch = footerText?.match(/Requests: (\d+)/);
    
    return {
      duration: sessionDurationMatch?.[1] || '0.0h',
      model: modelMatch?.[1] || 'unknown',
      requests: parseInt(requestsMatch?.[1] || '0', 10)
    };
  }

  /**
   * Check if rate limit warning is displayed
   */
  async isRateLimited(): Promise<boolean> {
    try {
      await this.page.locator('text=Rate limit exceeded').waitFor({ 
        state: 'visible', 
        timeout: 2000 
      });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get page performance metrics
   */
  async getPerformanceMetrics() {
    return await this.page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        totalTime: navigation.loadEventEnd - navigation.fetchStart,
      };
    });
  }
}

export default BasePage;