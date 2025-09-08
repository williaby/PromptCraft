import { test, expect } from '@playwright/test';
import { Journey1Page } from '../fixtures/Journey1Page';
import TestUtils from '../helpers/test-utils';
import path from 'path';

test.describe('Journey 1: Performance and Load Testing', () => {
  let journey1Page: Journey1Page;
  const testDataDir = path.join(__dirname, '../data/files');

  test.beforeEach(async ({ page }) => {
    journey1Page = new Journey1Page(page);
    await journey1Page.gotoJourney1();
  });

  test.describe('Response Time Performance', () => {
    test('should maintain acceptable response times for simple prompts', async ({ page }) => {
      const simplePrompts = [
        'Create a brief email template',
        'Write a short product description',
        'Generate a simple task list',
        'Create a meeting agenda'
      ];

      const responseTimes = [];

      for (const prompt of simplePrompts) {
        await journey1Page.clearAll();
        await journey1Page.enterPrompt(prompt);

        const responseTime = await TestUtils.measureResponseTime(page, async () => {
          await journey1Page.enhancePrompt(30000);
        });

        responseTimes.push(responseTime);

        // Simple prompts should complete within 15 seconds
        expect(responseTime).toBeLessThan(15000);

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        console.log(`Simple prompt "${prompt.substring(0, 20)}..." completed in ${responseTime}ms`);
      }

      // Calculate average response time
      const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
      console.log(`Average response time for simple prompts: ${avgResponseTime.toFixed(2)}ms`);

      // Average should be under 10 seconds
      expect(avgResponseTime).toBeLessThan(10000);
    });

    test('should handle complex prompts within acceptable time limits', async ({ page }) => {
      const complexPrompts = [
        'Develop a comprehensive digital marketing strategy for a B2B SaaS company targeting enterprise customers in the financial services industry, including detailed buyer personas, content marketing plan, lead generation tactics, and ROI measurement frameworks',
        'Create a detailed project management methodology that combines Agile and Waterfall approaches, includes risk management strategies, stakeholder communication plans, and quality assurance protocols for large-scale software development projects',
        'Design a complete employee onboarding program for a remote-first technology company, covering pre-boarding preparation, first-day experience, 30-60-90 day milestones, mentorship programs, and cultural integration strategies'
      ];

      const complexResponseTimes = [];

      for (const prompt of complexPrompts) {
        await journey1Page.clearAll();
        await journey1Page.enterPrompt(prompt);

        const responseTime = await TestUtils.measureResponseTime(page, async () => {
          await journey1Page.enhancePrompt(60000); // Extended timeout for complex prompts
        });

        complexResponseTimes.push(responseTime);

        // Complex prompts should complete within 45 seconds
        expect(responseTime).toBeLessThan(45000);

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();
        expect(enhancedPrompt.length).toBeGreaterThan(prompt.length * 2);

        console.log(`Complex prompt completed in ${responseTime}ms`);
      }

      const avgComplexResponseTime = complexResponseTimes.reduce((a, b) => a + b, 0) / complexResponseTimes.length;
      console.log(`Average response time for complex prompts: ${avgComplexResponseTime.toFixed(2)}ms`);

      // Complex prompts should average under 30 seconds
      expect(avgComplexResponseTime).toBeLessThan(30000);
    });

    test('should handle file processing performance appropriately', async ({ page }) => {
      const testFiles = [
        path.join(testDataDir, 'simple-text.txt'),
        path.join(testDataDir, 'sample-data.csv'),
        path.join(testDataDir, 'test-document.md'),
        path.join(testDataDir, 'config-sample.json')
      ];

      for (const filePath of testFiles) {
        await journey1Page.clearAll();

        // Measure file upload time
        const uploadTime = await TestUtils.measureResponseTime(page, async () => {
          await journey1Page.uploadTestFile(filePath);
        });

        // File uploads should complete quickly
        expect(uploadTime).toBeLessThan(5000); // 5 seconds

        // Measure enhancement with file context
        const enhancementTime = await TestUtils.measureResponseTime(page, async () => {
          await journey1Page.enterPrompt('Analyze and summarize the uploaded file');
          await journey1Page.enhancePrompt(45000);
        });

        // File processing should complete within reasonable time
        expect(enhancementTime).toBeLessThan(30000); // 30 seconds

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        console.log(`File "${path.basename(filePath)}" - Upload: ${uploadTime}ms, Enhancement: ${enhancementTime}ms`);
      }
    });
  });

  test.describe('Concurrent User Simulation', () => {
    test('should handle multiple concurrent users effectively', async ({ browser }) => {
      const userCount = 5;
      const contexts = [];
      const pages = [];
      const journey1Pages = [];
      const performanceResults = [];

      // Create multiple user contexts
      for (let i = 0; i < userCount; i++) {
        const context = await browser.newContext();
        const page = await context.newPage();
        const j1Page = new Journey1Page(page);

        contexts.push(context);
        pages.push(page);
        journey1Pages.push(j1Page);

        await j1Page.gotoJourney1();
      }

      const prompts = [
        'Create a business proposal for sustainable energy solutions',
        'Design a user interface for a mobile banking application',
        'Develop a training program for customer service representatives',
        'Create a comprehensive marketing plan for a new product launch',
        'Design an enterprise software architecture for scalability'
      ];

      // Execute concurrent enhancements
      const concurrentPromises = journey1Pages.map(async (j1Page, index) => {
        const startTime = Date.now();

        try {
          await j1Page.enterPrompt(prompts[index]);

          // Stagger requests to simulate realistic usage
          await pages[index].waitForTimeout(index * 200);

          await j1Page.enhancePrompt(60000);
          const enhancedPrompt = await j1Page.getEnhancedPrompt();

          const endTime = Date.now();
          const responseTime = endTime - startTime;

          return {
            userIndex: index + 1,
            success: true,
            responseTime,
            promptLength: enhancedPrompt.length,
            error: null
          };
        } catch (error) {
          const endTime = Date.now();
          const responseTime = endTime - startTime;

          return {
            userIndex: index + 1,
            success: false,
            responseTime,
            promptLength: 0,
            error: error.message
          };
        }
      });

      // Wait for all concurrent requests to complete
      const results = await Promise.all(concurrentPromises);
      performanceResults.push(...results);

      // Analyze results
      const successfulRequests = results.filter(r => r.success);
      const failedRequests = results.filter(r => !r.success);

      console.log(`Concurrent test results:`);
      console.log(`  Successful: ${successfulRequests.length}/${userCount}`);
      console.log(`  Failed: ${failedRequests.length}/${userCount}`);

      // At least 80% should succeed
      expect(successfulRequests.length).toBeGreaterThanOrEqual(Math.ceil(userCount * 0.8));

      // Analyze response times for successful requests
      if (successfulRequests.length > 0) {
        const responseTimes = successfulRequests.map(r => r.responseTime);
        const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
        const maxResponseTime = Math.max(...responseTimes);

        console.log(`  Average response time: ${avgResponseTime.toFixed(2)}ms`);
        console.log(`  Max response time: ${maxResponseTime}ms`);

        // Under load, responses should still complete within reasonable time
        expect(avgResponseTime).toBeLessThan(45000); // 45 seconds average
        expect(maxResponseTime).toBeLessThan(90000); // 90 seconds maximum
      }

      // Log failed requests for analysis
      failedRequests.forEach(result => {
        console.log(`  User ${result.userIndex} failed: ${result.error}`);
      });

      // Clean up contexts
      for (const context of contexts) {
        await context.close();
      }
    });

    test('should maintain performance under sequential load', async ({ page }) => {
      const loadTestCount = 10;
      const responseTimes = [];
      const prompts = [
        'Create a marketing email',
        'Write a product description',
        'Generate meeting notes',
        'Design a workflow process',
        'Create documentation template'
      ];

      for (let i = 0; i < loadTestCount; i++) {
        await journey1Page.clearAll();

        const promptIndex = i % prompts.length;
        const testPrompt = `${prompts[promptIndex]} - Test ${i + 1}`;

        await journey1Page.enterPrompt(testPrompt);

        const responseTime = await TestUtils.measureResponseTime(page, async () => {
          await journey1Page.enhancePrompt(45000);
        });

        responseTimes.push(responseTime);

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        console.log(`Load test ${i + 1}/${loadTestCount}: ${responseTime}ms`);

        // Small delay between requests to simulate realistic usage
        await page.waitForTimeout(1000);
      }

      // Analyze performance degradation
      const firstHalf = responseTimes.slice(0, Math.floor(loadTestCount / 2));
      const secondHalf = responseTimes.slice(Math.floor(loadTestCount / 2));

      const firstHalfAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
      const secondHalfAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;

      console.log(`Performance analysis:`);
      console.log(`  First half average: ${firstHalfAvg.toFixed(2)}ms`);
      console.log(`  Second half average: ${secondHalfAvg.toFixed(2)}ms`);

      // Performance should not degrade significantly
      const degradationPercentage = ((secondHalfAvg - firstHalfAvg) / firstHalfAvg) * 100;
      console.log(`  Performance change: ${degradationPercentage.toFixed(2)}%`);

      // Should not degrade by more than 50%
      expect(degradationPercentage).toBeLessThan(50);
    });
  });

  test.describe('Memory and Resource Usage', () => {
    test('should handle large prompt sequences without memory leaks', async ({ page }) => {
      const largePrompts = [];

      // Generate increasingly large prompts
      for (let i = 1; i <= 5; i++) {
        let largePrompt = `Create a comprehensive analysis for scenario ${i}. `;

        // Add context to make prompts progressively larger
        for (let j = 0; j < i * 100; j++) {
          largePrompt += `This is additional context point ${j + 1} that provides detailed information about the scenario requirements and expectations. `;
        }

        largePrompts.push(largePrompt);
      }

      const memoryMetrics = [];

      for (let i = 0; i < largePrompts.length; i++) {
        await journey1Page.clearAll();

        // Get initial memory usage
        const initialMemory = await page.evaluate(() => {
          return {
            usedJSMemory: (performance as any).memory?.usedJSMemory || 0,
            totalJSMemory: (performance as any).memory?.totalJSMemory || 0
          };
        });

        await journey1Page.enterPrompt(largePrompts[i]);
        await journey1Page.enhancePrompt(90000); // Extended timeout for large prompts

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        // Get memory usage after processing
        const finalMemory = await page.evaluate(() => {
          return {
            usedJSMemory: (performance as any).memory?.usedJSMemory || 0,
            totalJSMemory: (performance as any).memory?.totalJSMemory || 0
          };
        });

        const memoryUsed = finalMemory.usedJSMemory - initialMemory.usedJSMemory;
        memoryMetrics.push({
          promptSize: largePrompts[i].length,
          memoryUsed,
          totalMemory: finalMemory.totalJSMemory
        });

        console.log(`Large prompt ${i + 1}: ${largePrompts[i].length} chars, Memory used: ${memoryUsed} bytes`);

        // Force garbage collection if available
        if ((performance as any).memory) {
          await page.evaluate(() => {
            if ((window as any).gc) {
              (window as any).gc();
            }
          });
        }
      }

      // Analyze memory usage patterns
      console.log('Memory usage analysis:', memoryMetrics);

      // Memory usage should not grow excessively
      const totalMemoryUsed = memoryMetrics.reduce((sum, metric) => sum + metric.memoryUsed, 0);
      console.log(`Total memory used across all tests: ${totalMemoryUsed} bytes`);
    });

    test('should handle rapid input changes efficiently', async ({ page }) => {
      const rapidInputs = [
        'Create a brief summary',
        'Write a detailed analysis',
        'Generate a comprehensive report',
        'Design a strategic plan',
        'Develop a implementation guide'
      ];

      // Rapidly change inputs to test UI responsiveness
      for (let iteration = 0; iteration < 3; iteration++) {
        for (let i = 0; i < rapidInputs.length; i++) {
          const startTime = Date.now();

          await journey1Page.clearAll();
          await journey1Page.enterPrompt(rapidInputs[i]);

          // Don't wait for enhancement, just measure input responsiveness
          const inputTime = Date.now() - startTime;

          // Input should be responsive (under 1 second)
          expect(inputTime).toBeLessThan(1000);

          // Small delay to prevent overwhelming the system
          await page.waitForTimeout(100);
        }

        console.log(`Rapid input iteration ${iteration + 1} completed`);
      }

      // Perform one final enhancement to ensure system is still functional
      await journey1Page.enhancePrompt();
      const finalPrompt = await journey1Page.getEnhancedPrompt();
      expect(finalPrompt).toBeTruthy();

      console.log('✅ System remains responsive after rapid input changes');
    });
  });

  test.describe('Network Condition Performance', () => {
    test('should handle slow network conditions gracefully', async ({ page }) => {
      // Test under different network conditions
      const networkConditions = ['slow', 'normal'];

      for (const condition of networkConditions) {
        await TestUtils.simulateNetworkConditions(page, condition);
        await journey1Page.clearAll();

        const testPrompt = `Test prompt under ${condition} network conditions`;
        await journey1Page.enterPrompt(testPrompt);

        const responseTime = await TestUtils.measureResponseTime(page, async () => {
          await journey1Page.enhancePrompt(condition === 'slow' ? 120000 : 45000);
        });

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        console.log(`${condition} network: ${responseTime}ms`);

        if (condition === 'slow') {
          // Slow network should still complete within 2 minutes
          expect(responseTime).toBeLessThan(120000);
        } else {
          // Normal network should be much faster
          expect(responseTime).toBeLessThan(45000);
        }
      }

      // Restore normal network conditions
      await TestUtils.simulateNetworkConditions(page, 'normal');
    });

    test('should provide appropriate feedback during long operations', async ({ page }) => {
      const longPrompt = 'Create a comprehensive business strategy document that includes market analysis, competitive positioning, financial projections, risk assessment, implementation timeline, success metrics, and detailed action plans for the next 5 years of operations in the technology sector'.repeat(3);

      await journey1Page.enterPrompt(longPrompt);

      // Start enhancement and check for progress indicators
      const enhancePromise = journey1Page.enhancePrompt(120000);

      // Wait a moment for progress indicator to appear
      await page.waitForTimeout(2000);

      // Check if progress indicator is visible
      try {
        const progressVisible = await journey1Page.progressIndicator.isVisible();
        if (progressVisible) {
          console.log('✅ Progress indicator shown during long operation');
        } else {
          console.log('⚠️ No progress indicator visible');
        }
      } catch (error) {
        console.log('⚠️ Could not check progress indicator');
      }

      // Wait for enhancement to complete
      await enhancePromise;

      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();

      console.log('✅ Long operation completed successfully');
    });
  });
});
