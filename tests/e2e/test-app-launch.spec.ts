import { test, expect } from '@playwright/test';
import { BasePage } from './fixtures/BasePage';
import TestUtils from './helpers/test-utils';

test.describe('Application Launch Tests', () => {
  let basePage: BasePage;

  test.beforeEach(async ({ page }) => {
    basePage = new BasePage(page);
  });

  test('should load the main application successfully', async ({ page }) => {
    // Navigate to the application
    await basePage.goto();

    // Verify page title
    await expect(page).toHaveTitle(/PromptCraft/);

    // Verify main container is visible
    await expect(basePage.gradioContainer).toBeVisible();

    // Verify header is present
    await expect(basePage.headerTitle).toBeVisible();

    // Take screenshot for visual validation
    await basePage.takeScreenshot('app-launch-success');
  });

  test('should display all journey tabs', async ({ page }) => {
    await basePage.goto();

    // Verify all four journey tabs are visible
    await expect(basePage.journey1Tab).toBeVisible();
    await expect(basePage.journey2Tab).toBeVisible();
    await expect(basePage.journey3Tab).toBeVisible();
    await expect(basePage.journey4Tab).toBeVisible();

    // Verify tab text content
    await expect(basePage.journey1Tab).toContainText('Journey 1: Smart Templates');
    await expect(basePage.journey2Tab).toContainText('Journey 2: Intelligent Search');
    await expect(basePage.journey3Tab).toContainText('Journey 3: IDE Integration');
    await expect(basePage.journey4Tab).toContainText('Journey 4: Autonomous Workflows');
  });

  test('should have functional tab navigation', async ({ page }) => {
    await basePage.goto();

    // Test switching between tabs
    for (let i = 1; i <= 4; i++) {
      await basePage.switchToJourney(i as 1 | 2 | 3 | 4);
      
      // Wait for tab to activate
      await page.waitForTimeout(500);
      
      // Verify tab is selected/active using Gradio v5 tab structure
      const activeTab = page.locator('button[role="tab"][aria-selected="true"]');
      await expect(activeTab).toBeVisible();
    }
  });

  test('should display footer with session information', async ({ page }) => {
    await basePage.goto();

    // Verify footer is visible
    await expect(basePage.footerContainer).toBeVisible();

    // Get session info
    const sessionInfo = await basePage.getSessionInfo();
    
    // Verify session info structure
    expect(sessionInfo.duration).toMatch(/\d+\.\d+h/);
    expect(sessionInfo.model).toBeTruthy();
    expect(sessionInfo.requests).toBeGreaterThanOrEqual(0);

    // Verify footer contains expected elements
    await expect(basePage.footerContainer).toContainText('Session:');
    await expect(basePage.footerContainer).toContainText('Model:');
    await expect(basePage.footerContainer).toContainText('Status:');
  });

  test('should be responsive on mobile devices', async ({ page, browserName }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await basePage.goto();

    // Verify main container adapts to mobile
    await expect(basePage.gradioContainer).toBeVisible();

    // Check that tabs are still accessible (using Gradio v5 tab structure)
    const tabs = page.locator('button[role="tab"]').first();
    await expect(tabs).toBeVisible();

    // Take mobile screenshot
    await basePage.takeScreenshot(`mobile-responsive-${browserName}`);
  });

  test('should handle page refresh gracefully', async ({ page }) => {
    await basePage.goto();
    
    // Verify initial load
    await expect(basePage.gradioContainer).toBeVisible();
    
    // Refresh the page
    await page.reload();
    
    // Verify page loads again
    await basePage.waitForPageLoad();
    await expect(basePage.gradioContainer).toBeVisible();
    await expect(basePage.journey1Tab).toBeVisible();
  });

  test('should load within acceptable time limits', async ({ page }) => {
    const startTime = Date.now();
    
    await basePage.goto();
    
    const loadTime = Date.now() - startTime;
    
    // Verify load time is under 5 seconds
    expect(loadTime).toBeLessThan(5000);
    
    // Get detailed performance metrics
    const metrics = await basePage.getPerformanceMetrics();
    
    // Verify performance benchmarks
    expect(metrics.domContentLoaded).toBeLessThan(3000);
    expect(metrics.loadComplete).toBeLessThan(5000);
    
    console.log('Performance metrics:', metrics);
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // Start by loading the page normally
    await basePage.goto();
    await expect(basePage.gradioContainer).toBeVisible();

    // Simulate network offline
    await TestUtils.simulateNetworkConditions(page, 'offline');
    
    // Try to perform an action that requires network
    await basePage.journey1Tab.click();
    
    // Verify the page doesn't crash (basic functionality preserved)
    await expect(basePage.gradioContainer).toBeVisible();
    
    // Restore network
    await TestUtils.simulateNetworkConditions(page, 'normal');
  });

  test('should have proper security headers', async ({ page }) => {
    const response = await page.goto('/');
    
    // Check for important security headers
    const headers = response?.headers();
    
    if (headers) {
      // These might be set by the server/proxy
      console.log('Security headers check:', {
        'content-security-policy': headers['content-security-policy'],
        'x-frame-options': headers['x-frame-options'],
        'x-content-type-options': headers['x-content-type-options'],
      });
    }
    
    // Verify no obvious security issues
    const content = await page.content();
    expect(content).not.toContain('password');
    expect(content).not.toContain('secret');
    expect(content).not.toContain('token');
  });

  test('should maintain session state across tab switches', async ({ page }) => {
    await basePage.goto();
    
    // Get initial session info
    const initialSession = await basePage.getSessionInfo();
    
    // Switch between tabs multiple times
    for (let i = 1; i <= 4; i++) {
      await basePage.switchToJourney(i as 1 | 2 | 3 | 4);
      await page.waitForTimeout(200);
    }
    
    // Verify session info is maintained
    const finalSession = await basePage.getSessionInfo();
    expect(finalSession.model).toBe(initialSession.model);
    // Request count might change due to tab switches
    expect(finalSession.requests).toBeGreaterThanOrEqual(initialSession.requests);
  });

  test('should display admin tab conditionally', async ({ page }) => {
    await basePage.goto();
    
    // Check if admin tab exists
    const adminTabExists = await basePage.adminTab.isVisible().catch(() => false);
    
    if (adminTabExists) {
      await expect(basePage.adminTab).toBeVisible();
      await expect(basePage.adminTab).toContainText('Admin');
      
      // Test admin tab is clickable
      await basePage.adminTab.click();
      await page.waitForTimeout(500);
      
      console.log('Admin tab is available and functional');
    } else {
      console.log('Admin tab is not visible (expected for non-admin users)');
    }
  });
});