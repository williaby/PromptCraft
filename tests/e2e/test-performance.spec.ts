import { test, expect } from '@playwright/test';
import { Journey1Page } from './fixtures/Journey1Page';
import { BasePage } from './fixtures/BasePage';
import TestUtils from './helpers/test-utils';
import path from 'path';

test.describe('Performance Tests', () => {
  let basePage: BasePage;
  let journey1Page: Journey1Page;
  const testDataDir = path.join(__dirname, 'data/files');

  test.beforeEach(async ({ page }) => {
    basePage = new BasePage(page);
    journey1Page = new Journey1Page(page);
  });

  test.describe('Page Load Performance', () => {
    test('should load within performance benchmarks', async ({ page }) => {
      const startTime = Date.now();
      
      await basePage.goto();
      
      const loadTime = Date.now() - startTime;
      const metrics = await TestUtils.getPerformanceSnapshot(page);
      
      // Performance benchmarks
      expect(loadTime).toBeLessThan(5000); // Total load under 5s
      expect(metrics.navigation.domContentLoaded).toBeLessThan(3000); // DOM ready under 3s
      expect(metrics.navigation.loadComplete).toBeLessThan(5000); // Load complete under 5s
      
      // Detailed timing checks
      expect(metrics.navigation.dns).toBeLessThan(500); // DNS lookup under 500ms
      expect(metrics.navigation.tcp).toBeLessThan(1000); // TCP connection under 1s
      expect(metrics.navigation.request).toBeLessThan(1000); // Request time under 1s
      
      console.log('Load performance metrics:', {
        totalLoad: loadTime,
        ...metrics.navigation,
        resourceCount: metrics.resources,
        memoryUsage: metrics.memory
      });
      
      await basePage.takeScreenshot('performance-load-complete');
    });

    test('should maintain performance across different viewport sizes', async ({ page }) => {
      const viewports = [
        { width: 1920, height: 1080, name: 'desktop-large' },
        { width: 1366, height: 768, name: 'desktop-medium' },
        { width: 768, height: 1024, name: 'tablet' },
        { width: 375, height: 667, name: 'mobile' }
      ];

      const performanceResults = [];

      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        
        const startTime = Date.now();
        await basePage.goto();
        const loadTime = Date.now() - startTime;
        
        const metrics = await TestUtils.getPerformanceSnapshot(page);
        
        performanceResults.push({
          viewport: viewport.name,
          loadTime,
          domContentLoaded: metrics.navigation.domContentLoaded,
          memoryUsage: metrics.memory?.used || 0
        });
        
        // Each viewport should load reasonably fast
        expect(loadTime).toBeLessThan(7000); // Allow slightly more time for smaller devices
      }

      console.log('Performance across viewports:', performanceResults);
      
      // Desktop should generally be fastest
      const desktop = performanceResults.find(r => r.viewport === 'desktop-large');
      const mobile = performanceResults.find(r => r.viewport === 'mobile');
      
      expect(desktop.loadTime).toBeLessThan(mobile.loadTime * 1.5); // Desktop should be at most 50% slower
    });

    test('should handle concurrent users efficiently', async ({ browser }) => {
      const concurrentUsers = 5;
      const contexts = [];
      const pages = [];
      
      // Create multiple browser contexts (simulating different users)
      for (let i = 0; i < concurrentUsers; i++) {
        const context = await browser.newContext();
        const page = await context.newPage();
        contexts.push(context);
        pages.push(page);
      }
      
      try {
        // Measure concurrent load performance
        const startTime = Date.now();
        const loadPromises = pages.map(async (page, index) => {
          const userStartTime = Date.now();
          await page.goto('/');
          await TestUtils.waitForGradioLoad(page);
          return {
            user: index + 1,
            loadTime: Date.now() - userStartTime
          };
        });
        
        const results = await Promise.all(loadPromises);
        const totalTime = Date.now() - startTime;
        
        // All users should load within reasonable time
        for (const result of results) {
          expect(result.loadTime).toBeLessThan(10000); // 10s per user
        }
        
        // Total time should be reasonable for concurrent load
        expect(totalTime).toBeLessThan(15000); // 15s total for all users
        
        const avgLoadTime = results.reduce((sum, r) => sum + r.loadTime, 0) / results.length;
        console.log(`Concurrent load test: ${concurrentUsers} users, avg ${avgLoadTime}ms per user`);
        
      } finally {
        // Clean up contexts
        for (const context of contexts) {
          await context.close();
        }
      }
    });
  });

  test.describe('API Response Performance', () => {
    test('should process simple prompts quickly', async ({ page }) => {
      await journey1Page.gotoJourney1();
      
      const simplePrompt = TestUtils.getTestData().simplePrompt;
      await journey1Page.enterPrompt(simplePrompt);
      
      const responseTime = await TestUtils.measureResponseTime(page, async () => {
        await journey1Page.enhancePrompt();
      });
      
      // Simple prompts should process under 10 seconds
      expect(responseTime).toBeLessThan(10000);
      
      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();
      
      console.log(`Simple prompt processing time: ${responseTime}ms`);
    });

    test('should handle complex prompts within time limits', async ({ page }) => {
      await journey1Page.gotoJourney1();
      
      const complexPrompt = TestUtils.getTestData().complexPrompt;
      await journey1Page.enterPrompt(complexPrompt);
      
      const responseTime = await TestUtils.measureResponseTime(page, async () => {
        await journey1Page.enhancePrompt(45000); // Extended timeout for complex prompts
      });
      
      // Complex prompts should process under 30 seconds
      expect(responseTime).toBeLessThan(30000);
      
      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();
      expect(enhancedPrompt.length).toBeGreaterThan(complexPrompt.length);
      
      console.log(`Complex prompt processing time: ${responseTime}ms`);
    });

    test('should process file uploads efficiently', async ({ page }) => {
      await journey1Page.gotoJourney1();
      
      const testFiles = [
        { path: path.join(testDataDir, 'simple-text.txt'), type: 'text' },
        { path: path.join(testDataDir, 'sample-data.csv'), type: 'csv' },
        { path: path.join(testDataDir, 'config-sample.json'), type: 'json' },
        { path: path.join(testDataDir, 'test-document.md'), type: 'markdown' }
      ];
      
      const uploadResults = [];
      
      for (const testFile of testFiles) {
        const uploadStartTime = Date.now();
        
        await journey1Page.uploadTestFile(testFile.path);
        await journey1Page.enterPrompt(`Process this ${testFile.type} file`);
        
        const processingTime = await TestUtils.measureResponseTime(page, async () => {
          await journey1Page.enhancePrompt();
        });
        
        const totalTime = Date.now() - uploadStartTime;
        
        uploadResults.push({
          fileType: testFile.type,
          processingTime,
          totalTime
        });
        
        // File processing should complete within reasonable time
        expect(processingTime).toBeLessThan(15000); // 15s for file processing
        expect(totalTime).toBeLessThan(20000); // 20s total including upload
        
        // Clear for next test
        await journey1Page.clearAll();
      }
      
      console.log('File processing performance:', uploadResults);
    });

    test('should handle large content efficiently', async ({ page }) => {
      await journey1Page.gotoJourney1();
      
      const largeFile = path.join(testDataDir, 'large-content.txt');
      
      const startTime = Date.now();
      await journey1Page.uploadTestFile(largeFile);
      await journey1Page.enterPrompt('Summarize this large document');
      
      const processingTime = await TestUtils.measureResponseTime(page, async () => {
        await journey1Page.enhancePrompt(60000); // Extended timeout for large content
      });
      
      const totalTime = Date.now() - startTime;
      
      // Large content should still process within reasonable limits
      expect(processingTime).toBeLessThan(45000); // 45s for large content processing
      expect(totalTime).toBeLessThan(50000); // 50s total
      
      console.log(`Large content processing: ${processingTime}ms (total: ${totalTime}ms)`);
    });
  });

  test.describe('Memory and Resource Usage', () => {
    test('should maintain stable memory usage', async ({ page }) => {
      await journey1Page.gotoJourney1();
      
      const iterations = 10;
      const memorySnapshots = [];
      
      for (let i = 0; i < iterations; i++) {
        await journey1Page.clearAll();
        await journey1Page.enterPrompt(`Memory test iteration ${i + 1}`);
        await journey1Page.enhancePrompt();
        
        const metrics = await TestUtils.getPerformanceSnapshot(page);
        
        if (metrics.memory) {
          memorySnapshots.push({
            iteration: i + 1,
            used: metrics.memory.used,
            total: metrics.memory.total
          });
        }
        
        // Small delay between iterations
        await page.waitForTimeout(1000);
      }
      
      if (memorySnapshots.length > 0) {
        const initialMemory = memorySnapshots[0].used;
        const finalMemory = memorySnapshots[memorySnapshots.length - 1].used;
        const memoryGrowth = finalMemory - initialMemory;
        const growthRatio = memoryGrowth / initialMemory;
        
        // Memory growth should be reasonable (less than 50% increase)
        expect(growthRatio).toBeLessThan(0.5);
        
        console.log('Memory usage analysis:', {
          initial: `${(initialMemory / 1024 / 1024).toFixed(2)}MB`,
          final: `${(finalMemory / 1024 / 1024).toFixed(2)}MB`,
          growth: `${(memoryGrowth / 1024 / 1024).toFixed(2)}MB`,
          growthPercent: `${(growthRatio * 100).toFixed(1)}%`
        });
      }
    });

    test('should handle multiple browser tabs efficiently', async ({ browser }) => {
      const tabCount = 3;
      const contexts = [];
      const journey1Pages = [];
      
      // Open multiple tabs
      for (let i = 0; i < tabCount; i++) {
        const context = await browser.newContext();
        const page = await context.newPage();
        const journey1 = new Journey1Page(page);
        await journey1.gotoJourney1();
        
        contexts.push(context);
        journey1Pages.push(journey1);
      }
      
      try {
        // Perform operations in all tabs simultaneously
        const operations = journey1Pages.map(async (journey1, index) => {
          const startTime = Date.now();
          await journey1.enterPrompt(`Multi-tab test ${index + 1}`);
          await journey1.enhancePrompt();
          return {
            tab: index + 1,
            responseTime: Date.now() - startTime
          };
        });
        
        const results = await Promise.all(operations);
        
        // All tabs should complete reasonably quickly
        for (const result of results) {
          expect(result.responseTime).toBeLessThan(20000); // 20s per tab
        }
        
        const avgResponseTime = results.reduce((sum, r) => sum + r.responseTime, 0) / results.length;
        console.log(`Multi-tab performance: ${tabCount} tabs, avg ${avgResponseTime}ms`);
        
      } finally {
        // Clean up
        for (const context of contexts) {
          await context.close();
        }
      }
    });
  });

  test.describe('Network Performance', () => {
    test('should handle slow network conditions', async ({ page }) => {
      await journey1Page.gotoJourney1();
      
      // Simulate slow network (50KB/s)
      await TestUtils.simulateNetworkConditions(page, 'slow');
      
      const slowNetworkStartTime = Date.now();
      await journey1Page.enterPrompt('Test under slow network conditions');
      
      try {
        await journey1Page.enhancePrompt(60000); // Extended timeout for slow network
        
        const responseTime = Date.now() - slowNetworkStartTime;
        
        // Should complete even on slow network, but may take longer
        expect(responseTime).toBeLessThan(60000); // 60s timeout
        
        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();
        
        console.log(`Slow network response time: ${responseTime}ms`);
        
      } catch (error) {
        // Timeout is acceptable on very slow networks
        console.log('Request timed out on slow network (expected behavior)');
        
        // Should show appropriate error message
        const hasError = await journey1Page.hasError();
        if (hasError) {
          const errorMessage = await journey1Page.getErrorMessage();
          expect(errorMessage).toMatch(/timeout|network|slow/i);
        }
      }
      
      // Restore normal network
      await TestUtils.simulateNetworkConditions(page, 'normal');
    });

    test('should optimize resource loading', async ({ page }) => {
      // Monitor network requests
      const requests = [];
      page.on('request', (request) => {
        requests.push({
          url: request.url(),
          resourceType: request.resourceType(),
          size: request.postDataBuffer()?.length || 0
        });
      });
      
      const responses = [];
      page.on('response', (response) => {
        responses.push({
          url: response.url(),
          status: response.status(),
          size: response.headers()['content-length'] || 0,
          timing: response.timing()
        });
      });
      
      await basePage.goto();
      
      // Allow all resources to load
      await TestUtils.waitForNetworkIdle(page);
      
      // Analyze resource loading
      const totalRequests = requests.length;
      const failedRequests = responses.filter(r => r.status >= 400).length;
      const avgResponseTime = responses
        .filter(r => r.timing)
        .reduce((sum, r) => sum + (r.timing?.responseEnd - r.timing?.responseStart || 0), 0) / responses.length;
      
      // Performance expectations
      expect(failedRequests).toBeLessThan(totalRequests * 0.05); // Less than 5% failed requests
      expect(avgResponseTime).toBeLessThan(2000); // Average response under 2s
      
      console.log('Resource loading analysis:', {
        totalRequests,
        failedRequests,
        failureRate: `${(failedRequests / totalRequests * 100).toFixed(1)}%`,
        avgResponseTime: `${avgResponseTime.toFixed(0)}ms`
      });
    });
  });

  test.describe('Stress Testing', () => {
    test('should handle rapid consecutive requests', async ({ page }) => {
      await journey1Page.gotoJourney1();
      
      const rapidRequestCount = 10;
      const results = [];
      
      for (let i = 0; i < rapidRequestCount; i++) {
        const startTime = Date.now();
        
        try {
          await journey1Page.clearAll();
          await journey1Page.enterPrompt(`Rapid request ${i + 1}`);
          await journey1Page.enhancePrompt(15000); // Shorter timeout for stress test
          
          results.push({
            request: i + 1,
            success: true,
            responseTime: Date.now() - startTime
          });
          
        } catch (error) {
          results.push({
            request: i + 1,
            success: false,
            error: error.message,
            responseTime: Date.now() - startTime
          });
        }
        
        // Minimal delay between requests for stress testing
        await page.waitForTimeout(100);
      }
      
      const successfulRequests = results.filter(r => r.success);
      const avgSuccessTime = successfulRequests.length > 0 
        ? successfulRequests.reduce((sum, r) => sum + r.responseTime, 0) / successfulRequests.length 
        : 0;
      
      // Should handle at least 80% of rapid requests successfully
      expect(successfulRequests.length / rapidRequestCount).toBeGreaterThan(0.8);
      
      console.log(`Rapid request stress test: ${successfulRequests.length}/${rapidRequestCount} successful, avg ${avgSuccessTime}ms`);
    });

    test('should maintain performance during long session', async ({ page }) => {
      await journey1Page.gotoJourney1();
      
      const sessionDuration = 5 * 60 * 1000; // 5 minutes
      const requestInterval = 30 * 1000; // Every 30 seconds
      const startTime = Date.now();
      const performanceData = [];
      
      let requestCount = 0;
      
      while (Date.now() - startTime < sessionDuration) {
        const requestStartTime = Date.now();
        requestCount++;
        
        try {
          await journey1Page.clearAll();
          await journey1Page.enterPrompt(`Long session request ${requestCount}`);
          await journey1Page.enhancePrompt(20000);
          
          const responseTime = Date.now() - requestStartTime;
          const metrics = await TestUtils.getPerformanceSnapshot(page);
          
          performanceData.push({
            request: requestCount,
            responseTime,
            memory: metrics.memory?.used || 0,
            timestamp: Date.now() - startTime
          });
          
        } catch (error) {
          performanceData.push({
            request: requestCount,
            error: error.message,
            timestamp: Date.now() - startTime
          });
        }
        
        // Wait until next interval
        await page.waitForTimeout(requestInterval - (Date.now() - requestStartTime));
      }
      
      // Analyze performance degradation over time
      const successfulRequests = performanceData.filter(d => !d.error);
      const firstHalfAvg = successfulRequests
        .slice(0, Math.floor(successfulRequests.length / 2))
        .reduce((sum, d) => sum + d.responseTime, 0) / Math.floor(successfulRequests.length / 2);
      const secondHalfAvg = successfulRequests
        .slice(Math.floor(successfulRequests.length / 2))
        .reduce((sum, d) => sum + d.responseTime, 0) / (successfulRequests.length - Math.floor(successfulRequests.length / 2));
      
      // Performance should not degrade significantly over time
      expect(secondHalfAvg).toBeLessThan(firstHalfAvg * 1.5); // No more than 50% degradation
      
      console.log(`Long session test: ${requestCount} requests over ${sessionDuration/1000}s`);
      console.log(`Performance: first half ${firstHalfAvg}ms, second half ${secondHalfAvg}ms`);
    });
  });
});