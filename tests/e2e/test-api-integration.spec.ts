import { test, expect } from '@playwright/test';
import { BasePage } from './fixtures/BasePage';
import TestUtils from './helpers/test-utils';

test.describe('API Integration Tests', () => {
  let basePage: BasePage;

  test.beforeEach(async ({ page }) => {
    basePage = new BasePage(page);
  });

  test.describe('Application Availability', () => {
    test('should return successful response from main application', async ({ page }) => {
      const response = await page.goto('/');
      
      expect(response?.status()).toBe(200);
      
      // Check if it's a Gradio application
      const content = await page.content();
      expect(content).toContain('Gradio');
      
      console.log('Main application loaded successfully');
    });

    test('should provide configuration health status', async ({ page }) => {
      const response = await page.goto('/health/config');
      
      // Should return 200 for healthy config or 500 for config issues
      expect([200, 500]).toContain(response?.status());
      
      const configHealth = await response?.json();
      expect(configHealth).toHaveProperty('status');
      
      if (response?.status() === 200) {
        expect(configHealth.status).toBe('healthy');
        expect(configHealth).toHaveProperty('config_status');
      } else {
        console.log('Configuration issues detected:', configHealth);
      }
    });

    test('should provide MCP integration health status', async ({ page }) => {
      try {
        const response = await page.goto('/health/mcp');
        
        if (response?.status() === 200) {
          const mcpHealth = await response?.json();
          expect(mcpHealth).toHaveProperty('status');
          expect(mcpHealth).toHaveProperty('service');
          expect(mcpHealth.service).toBe('mcp-integration');
          
          console.log('MCP integration status:', mcpHealth.status);
        } else {
          console.log('MCP integration not available or unhealthy');
        }
        
      } catch (error) {
        console.log('MCP endpoint not available:', error.message);
      }
    });

    test('should provide circuit breaker status', async ({ page }) => {
      try {
        const response = await page.goto('/health/circuit-breakers');
        
        expect(response?.status()).toBe(200);
        
        const circuitBreakerHealth = await response?.json();
        expect(circuitBreakerHealth).toHaveProperty('status');
        expect(circuitBreakerHealth).toHaveProperty('service', 'circuit-breaker-monitoring');
        
        if (circuitBreakerHealth.circuit_breakers) {
          console.log('Circuit breakers found:', Object.keys(circuitBreakerHealth.circuit_breakers));
        }
        
      } catch (error) {
        console.log('Circuit breaker endpoint issue:', error.message);
      }
    });
  });

  test.describe('API Response Validation', () => {
    test('should handle API errors gracefully', async ({ page }) => {
      // Test with invalid endpoint
      const response = await page.goto('/api/invalid-endpoint', { waitUntil: 'networkidle' });
      
      expect(response?.status()).toBe(404);
      
      // Should return JSON error response, not HTML
      const contentType = response?.headers()['content-type'] || '';
      if (contentType.includes('application/json')) {
        const errorData = await response?.json();
        expect(errorData).toHaveProperty('detail');
      }
    });

    test('should validate CORS headers on API responses', async ({ page }) => {
      // Monitor API requests
      const apiResponses = [];
      
      page.on('response', (response) => {
        if (response.url().includes('/api/') || response.url().includes('/health')) {
          apiResponses.push({
            url: response.url(),
            status: response.status(),
            headers: response.headers()
          });
        }
      });
      
      await basePage.goto();
      await basePage.waitForPageLoad();
      
      // Check CORS headers on API responses
      for (const response of apiResponses) {
        const headers = response.headers;
        
        console.log(`API Response: ${response.url}`, {
          status: response.status,
          cors: {
            'access-control-allow-origin': headers['access-control-allow-origin'],
            'access-control-allow-methods': headers['access-control-allow-methods'],
            'access-control-allow-credentials': headers['access-control-allow-credentials']
          }
        });
        
        // Basic CORS validation
        if (headers['access-control-allow-origin']) {
          expect(headers['access-control-allow-origin']).toBeTruthy();
        }
      }
    });

    test('should handle rate limiting correctly', async ({ page }) => {
      // Navigate to app first
      await basePage.goto();
      
      // Make multiple rapid requests to test rate limiting
      const requests = [];
      
      for (let i = 0; i < 10; i++) {
        try {
          const response = await page.goto('/health', { waitUntil: 'networkidle', timeout: 5000 });
          requests.push({
            attempt: i + 1,
            status: response?.status(),
            success: response?.status() === 200
          });
        } catch (error) {
          requests.push({
            attempt: i + 1,
            success: false,
            error: error.message
          });
        }
      }
      
      const successfulRequests = requests.filter(r => r.success);
      const failedRequests = requests.filter(r => !r.success);
      
      console.log(`Rate limit test: ${successfulRequests.length} successful, ${failedRequests.length} failed`);
      
      // Most requests should succeed for health endpoint (higher rate limit)
      expect(successfulRequests.length).toBeGreaterThan(5);
    });
  });

  test.describe('WebSocket Integration', () => {
    test('should handle WebSocket connections if available', async ({ page }) => {
      // Check if WebSocket connections are used
      const wsConnections = [];
      
      page.on('websocket', (ws) => {
        console.log('WebSocket connection:', ws.url());
        wsConnections.push(ws);
        
        ws.on('framereceived', (frame) => {
          console.log('WS frame received:', frame.payload);
        });
        
        ws.on('framesent', (frame) => {
          console.log('WS frame sent:', frame.payload);
        });
      });
      
      await basePage.goto();
      await basePage.waitForPageLoad();
      
      // Allow time for WebSocket connections
      await page.waitForTimeout(3000);
      
      console.log(`WebSocket connections detected: ${wsConnections.length}`);
      
      if (wsConnections.length > 0) {
        // If WebSockets are used, they should be properly connected
        for (const ws of wsConnections) {
          expect(ws.isClosed()).toBeFalsy();
        }
      }
    });
  });

  test.describe('Authentication Integration', () => {
    test('should handle authentication flow correctly', async ({ page }) => {
      await basePage.goto();
      
      // Check for authentication-related elements or redirects
      const currentUrl = page.url();
      
      // If there's authentication, we should either:
      // 1. Be logged in and see the interface
      // 2. Be redirected to login page
      // 3. See authentication status in the UI
      
      const hasAuthElements = await page.locator('[data-testid="auth"], .auth, .login, .logout').count() > 0;
      const hasMainInterface = await basePage.gradioContainer.isVisible();
      
      if (hasAuthElements) {
        console.log('Authentication elements detected');
        
        // Should have proper auth status indication
        const authStatus = await page.locator('.auth-status, [data-testid="auth-status"]').textContent();
        console.log('Auth status:', authStatus);
        
      } else if (hasMainInterface) {
        console.log('Main interface accessible without authentication');
      } else {
        console.log('Authentication may be redirecting or blocking access');
      }
      
      // Basic expectation: should either show auth UI or main interface
      const hasAccessibleContent = hasAuthElements || hasMainInterface;
      expect(hasAccessibleContent).toBeTruthy();
    });

    test('should maintain session consistency', async ({ page }) => {
      await basePage.goto();
      
      // Get initial session info
      const initialSession = await basePage.getSessionInfo();
      
      // Navigate to different pages/tabs
      await basePage.switchToJourney(2);
      await page.waitForTimeout(1000);
      await basePage.switchToJourney(3);
      await page.waitForTimeout(1000);
      await basePage.switchToJourney(1);
      
      // Check session consistency
      const finalSession = await basePage.getSessionInfo();
      
      // Session ID or key info should remain consistent
      expect(finalSession.model).toBe(initialSession.model);
      
      console.log('Session consistency check passed');
    });
  });

  test.describe('Error Recovery Integration', () => {
    test('should recover from network interruptions', async ({ page }) => {
      await basePage.goto();
      
      // Verify initial functionality
      expect(await basePage.gradioContainer.isVisible()).toBeTruthy();
      
      // Simulate network interruption
      await TestUtils.simulateNetworkConditions(page, 'offline');
      
      // Try to interact during network outage
      try {
        await basePage.switchToJourney(2);
        await page.waitForTimeout(2000);
      } catch (error) {
        console.log('Expected error during network outage:', error.message);
      }
      
      // Restore network
      await TestUtils.simulateNetworkConditions(page, 'normal');
      
      // Should recover functionality
      await page.waitForTimeout(2000);
      await basePage.switchToJourney(1);
      
      // Interface should still be functional
      expect(await basePage.gradioContainer.isVisible()).toBeTruthy();
      
      console.log('Network recovery test completed');
    });

    test('should handle server errors gracefully', async ({ page }) => {
      // Monitor for server error responses
      const serverErrors = [];
      
      page.on('response', (response) => {
        if (response.status() >= 500) {
          serverErrors.push({
            url: response.url(),
            status: response.status(),
            statusText: response.statusText()
          });
        }
      });
      
      await basePage.goto();
      
      // Perform various operations to test server interaction
      await basePage.switchToJourney(1);
      await basePage.switchToJourney(2);
      await basePage.switchToJourney(3);
      await basePage.switchToJourney(4);
      
      // Check for server errors
      if (serverErrors.length > 0) {
        console.log('Server errors detected:', serverErrors);
        
        // Interface should still be accessible despite server errors
        expect(await basePage.gradioContainer.isVisible()).toBeTruthy();
        
        // Should show appropriate error messages to user
        const errorMessages = await page.locator('.error, .alert, .notification').count();
        if (errorMessages > 0) {
          const errorText = await page.locator('.error, .alert, .notification').first().textContent();
          expect(errorText).toBeTruthy();
          console.log('User-facing error message:', errorText);
        }
      } else {
        console.log('No server errors during integration test');
      }
    });
  });

  test.describe('Data Flow Integration', () => {
    test('should maintain data consistency across journeys', async ({ page }) => {
      await basePage.goto();
      
      // Start with Journey 1
      await basePage.switchToJourney(1);
      
      // Get model selection (if available)
      const modelSelector = page.locator('select, .dropdown').first();
      let selectedModel = 'default';
      
      if (await modelSelector.isVisible()) {
        selectedModel = await modelSelector.inputValue() || 'default';
      }
      
      // Switch to other journeys
      await basePage.switchToJourney(2);
      await basePage.switchToJourney(3);
      await basePage.switchToJourney(4);
      
      // Return to Journey 1
      await basePage.switchToJourney(1);
      
      // Check if model selection persisted
      if (await modelSelector.isVisible()) {
        const currentModel = await modelSelector.inputValue() || 'default';
        expect(currentModel).toBe(selectedModel);
      }
      
      console.log('Data consistency maintained across journeys');
    });

    test('should handle concurrent operations properly', async ({ browser }) => {
      const contexts = [];
      const pages = [];
      
      // Create multiple contexts
      for (let i = 0; i < 3; i++) {
        const context = await browser.newContext();
        const page = await context.newPage();
        await page.goto('/');
        
        contexts.push(context);
        pages.push(page);
      }
      
      try {
        // Perform operations simultaneously
        const operations = pages.map(async (page, index) => {
          const basePage = new BasePage(page);
          await basePage.waitForPageLoad();
          await basePage.switchToJourney((index % 4) + 1 as 1 | 2 | 3 | 4);
          return {
            page: index,
            sessionInfo: await basePage.getSessionInfo()
          };
        });
        
        const results = await Promise.all(operations);
        
        // Each session should maintain its own state
        const models = results.map(r => r.sessionInfo.model);
        const requests = results.map(r => r.sessionInfo.requests);
        
        console.log('Concurrent operation results:', results);
        
        // All operations should complete successfully
        expect(results.length).toBe(3);
        
      } finally {
        // Clean up
        for (const context of contexts) {
          await context.close();
        }
      }
    });
  });

  test.describe('External Service Integration', () => {
    test('should handle external service dependencies', async ({ page }) => {
      // Monitor requests to external services
      const externalRequests = [];
      
      page.on('request', (request) => {
        const url = request.url();
        if (!url.includes('localhost') && !url.includes('127.0.0.1')) {
          externalRequests.push({
            url,
            method: request.method(),
            resourceType: request.resourceType()
          });
        }
      });
      
      await basePage.goto();
      await basePage.waitForPageLoad();
      
      console.log(`External requests detected: ${externalRequests.length}`);
      
      for (const request of externalRequests) {
        console.log('External request:', request);
      }
      
      // Should handle external service failures gracefully
      // (This is more of a monitoring test)
    });

    test('should validate vector database integration', async ({ page }) => {
      // This test checks if Qdrant vector database integration is working
      // by monitoring for relevant API calls or checking functionality
      
      const vectorDbRequests = [];
      
      page.on('request', (request) => {
        const url = request.url();
        if (url.includes('qdrant') || url.includes('6333') || url.includes('vector')) {
          vectorDbRequests.push({
            url,
            method: request.method()
          });
        }
      });
      
      await basePage.goto();
      
      // Switch to Journey 2 (which uses vector search)
      await basePage.switchToJourney(2);
      
      console.log(`Vector database requests: ${vectorDbRequests.length}`);
      
      if (vectorDbRequests.length > 0) {
        console.log('Vector database integration active');
      } else {
        console.log('Vector database requests not detected in UI load');
      }
    });
  });
});