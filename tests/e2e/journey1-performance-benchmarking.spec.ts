import { test, expect } from '@playwright/test';
import { testDataGenerator, TestScenario } from './helpers/test-data-generator';
import * as fs from 'fs';
import * as path from 'path';

interface PerformanceMetrics {
  testId: string;
  scenario: string;
  browser: string;
  startTime: number;
  endTime: number;
  duration: number;
  navigationTime: number;
  enhancementTime: number;
  outputLength: number;
  success: boolean;
  errorDetails?: string;
}

test.describe('Journey 1: Performance Benchmarking Tests', () => {
  let performanceResults: PerformanceMetrics[] = [];
  const metricsFile = path.join(__dirname, 'data/performance-metrics.json');

  test.beforeAll(async () => {
    // Ensure data directory exists
    const dataDir = path.dirname(metricsFile);
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }

    // Load existing metrics if available
    if (fs.existsSync(metricsFile)) {
      try {
        const existingMetrics = JSON.parse(fs.readFileSync(metricsFile, 'utf8'));
        performanceResults = existingMetrics.results || [];
      } catch (error) {
        console.log('Starting with fresh performance metrics');
      }
    }
  });

  test.beforeEach(async ({ page, browserName }) => {
    // Navigate to Journey 1 with timing
    const navigationStart = performance.now();

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

    const navigationEnd = performance.now();
    (page as any)._navigationTime = navigationEnd - navigationStart;
  });

  test.afterAll(async () => {
    // Save performance results
    const report = {
      timestamp: new Date().toISOString(),
      totalTests: performanceResults.length,
      results: performanceResults,
      summary: generatePerformanceSummary(performanceResults)
    };

    fs.writeFileSync(metricsFile, JSON.stringify(report, null, 2));
    console.log(`Performance metrics saved to: ${metricsFile}`);
  });

  test.describe('Baseline Performance Tests', () => {
    test('should meet performance benchmarks for minimal complexity prompts', async ({ page, browserName }) => {
      console.log('🚀 Testing baseline performance with minimal complexity...');

      const scenarios = testDataGenerator.getScenariosByComplexity('minimal');

      for (const scenario of scenarios.slice(0, 3)) { // Test first 3 minimal scenarios
        const metrics = await executePerformanceTest(page, browserName || 'unknown', scenario);
        performanceResults.push(metrics);

        console.log(`✅ ${scenario.id}: ${metrics.duration}ms (Enhancement: ${metrics.enhancementTime}ms)`);

        // Baseline assertions
        expect(metrics.success).toBe(true);
        expect(metrics.duration).toBeLessThan(10000); // Should complete within 10 seconds
        expect(metrics.enhancementTime).toBeLessThan(8000); // Enhancement within 8 seconds
        expect(metrics.outputLength).toBeGreaterThan(0); // Should produce output
      }
    });

    test('should handle moderate complexity within performance thresholds', async ({ page, browserName }) => {
      console.log('⚡ Testing moderate complexity performance...');

      const scenarios = testDataGenerator.getScenariosByComplexity('moderate');

      for (const scenario of scenarios.slice(0, 2)) { // Test first 2 moderate scenarios
        const metrics = await executePerformanceTest(page, browserName || 'unknown', scenario);
        performanceResults.push(metrics);

        console.log(`✅ ${scenario.id}: ${metrics.duration}ms (Enhancement: ${metrics.enhancementTime}ms)`);

        // Moderate complexity assertions
        expect(metrics.success).toBe(true);
        expect(metrics.duration).toBeLessThan(15000); // Should complete within 15 seconds
        expect(metrics.enhancementTime).toBeLessThan(12000); // Enhancement within 12 seconds
        expect(metrics.outputLength).toBeGreaterThan(100); // Should produce substantial output
      }
    });

    test('should handle complex prompts within extended thresholds', async ({ page, browserName }) => {
      console.log('🔥 Testing complex prompt performance...');

      const scenarios = testDataGenerator.getScenariosByComplexity('complex');

      for (const scenario of scenarios.slice(0, 1)) { // Test first complex scenario
        const metrics = await executePerformanceTest(page, browserName || 'unknown', scenario, 25000);
        performanceResults.push(metrics);

        console.log(`✅ ${scenario.id}: ${metrics.duration}ms (Enhancement: ${metrics.enhancementTime}ms)`);

        // Complex prompt assertions
        expect(metrics.success).toBe(true);
        expect(metrics.duration).toBeLessThan(25000); // Should complete within 25 seconds
        expect(metrics.enhancementTime).toBeLessThan(22000); // Enhancement within 22 seconds
        expect(metrics.outputLength).toBeGreaterThan(200); // Should produce comprehensive output
      }
    });
  });

  test.describe('Stress Testing', () => {
    test('should handle extreme complexity prompts gracefully', async ({ page, browserName }) => {
      console.log('💥 Testing extreme complexity stress performance...');

      const scenarios = testDataGenerator.getScenariosByComplexity('extreme');

      if (scenarios.length > 0) {
        const scenario = scenarios[0]; // Test first extreme scenario
        const metrics = await executePerformanceTest(page, browserName || 'unknown', scenario, 45000);
        performanceResults.push(metrics);

        console.log(`✅ ${scenario.id}: ${metrics.duration}ms (Enhancement: ${metrics.enhancementTime}ms)`);
        console.log(`📊 Output length: ${metrics.outputLength} characters`);

        // Stress test assertions - more lenient but still bounded
        expect(metrics.success).toBe(true);
        expect(metrics.duration).toBeLessThan(45000); // Should complete within 45 seconds
        expect(metrics.enhancementTime).toBeLessThan(40000); // Enhancement within 40 seconds
        expect(metrics.outputLength).toBeGreaterThan(500); // Should produce substantial output

        // Quality check - extreme prompts should produce comprehensive results
        const outputDensity = metrics.outputLength / scenario.prompt.length;
        expect(outputDensity).toBeGreaterThan(0.5); // Output should be at least half the input length
      } else {
        test.skip();
      }
    });

    test('should maintain performance consistency under rapid requests', async ({ page, browserName }) => {
      console.log('⚡ Testing rapid request consistency...');

      const rapidTestScenario: TestScenario = {
        id: 'rapid-consistency-test',
        category: 'stress-testing',
        prompt: 'Create a brief professional email template for customer support responses',
        expectedBehavior: ['consistent-performance', 'rapid-response'],
        complexity: 'moderate',
        domain: 'customer-support',
        tags: ['stress', 'consistency', 'rapid']
      };

      const iterations = 3;
      const rapidMetrics: PerformanceMetrics[] = [];

      for (let i = 0; i < iterations; i++) {
        console.log(`🔄 Rapid test iteration ${i + 1}/${iterations}`);

        const metrics = await executePerformanceTest(
          page,
          browserName || 'unknown',
          rapidTestScenario,
          15000,
          `rapid-${i + 1}`
        );

        rapidMetrics.push(metrics);
        performanceResults.push(metrics);

        // Brief pause between requests
        await page.waitForTimeout(1000);
      }

      // Analyze consistency
      const durations = rapidMetrics.map(m => m.duration);
      const avgDuration = durations.reduce((sum, d) => sum + d, 0) / durations.length;
      const maxDeviation = Math.max(...durations.map(d => Math.abs(d - avgDuration)));
      const consistencyRatio = maxDeviation / avgDuration;

      console.log(`📊 Rapid test analysis:`);
      console.log(`   Average duration: ${avgDuration.toFixed(0)}ms`);
      console.log(`   Max deviation: ${maxDeviation.toFixed(0)}ms`);
      console.log(`   Consistency ratio: ${(consistencyRatio * 100).toFixed(1)}%`);

      // Consistency assertions
      expect(rapidMetrics.every(m => m.success)).toBe(true);
      expect(avgDuration).toBeLessThan(15000);
      expect(consistencyRatio).toBeLessThan(0.5); // Deviation should be less than 50% of average
    });
  });

  test.describe('Domain-Specific Performance', () => {
    test('should optimize performance for technical domain prompts', async ({ page, browserName }) => {
      console.log('🔧 Testing technical domain performance...');

      const technicalScenarios = testDataGenerator.getScenariosByCategory('examples-integration')
        .filter(s => s.domain.includes('software'));

      if (technicalScenarios.length > 0) {
        const scenario = technicalScenarios[0];
        const metrics = await executePerformanceTest(page, browserName || 'unknown', scenario);
        performanceResults.push(metrics);

        console.log(`✅ Technical domain: ${metrics.duration}ms`);

        // Technical domain should have good performance due to structured nature
        expect(metrics.success).toBe(true);
        expect(metrics.duration).toBeLessThan(12000);
        expect(metrics.outputLength).toBeGreaterThan(150);
      } else {
        test.skip();
      }
    });

    test('should handle business domain prompts efficiently', async ({ page, browserName }) => {
      console.log('💼 Testing business domain performance...');

      const businessScenarios = testDataGenerator.getScenariosByCategory('request-specification')
        .filter(s => s.domain.includes('business') || s.domain.includes('enterprise'));

      if (businessScenarios.length > 0) {
        const scenario = businessScenarios[0];
        const metrics = await executePerformanceTest(page, browserName || 'unknown', scenario);
        performanceResults.push(metrics);

        console.log(`✅ Business domain: ${metrics.duration}ms`);

        expect(metrics.success).toBe(true);
        expect(metrics.duration).toBeLessThan(15000);
        expect(metrics.outputLength).toBeGreaterThan(200);
      } else {
        test.skip();
      }
    });
  });

  test.describe('Performance Regression Detection', () => {
    test('should detect significant performance regressions', async ({ page, browserName }) => {
      console.log('📈 Testing performance regression detection...');

      // Load historical performance data
      const historicalMetrics = performanceResults.filter(m =>
        m.browser === browserName &&
        m.scenario.includes('baseline')
      );

      if (historicalMetrics.length > 0) {
        // Run baseline test
        const baselineScenario = testDataGenerator.getScenariosByComplexity('minimal')[0];
        const currentMetrics = await executePerformanceTest(page, browserName || 'unknown', baselineScenario);
        performanceResults.push(currentMetrics);

        // Compare with historical average
        const historicalAvg = historicalMetrics.reduce((sum, m) => sum + m.duration, 0) / historicalMetrics.length;
        const currentDuration = currentMetrics.duration;
        const regressionThreshold = 1.5; // 50% slower than historical average

        console.log(`📊 Regression analysis:`);
        console.log(`   Historical average: ${historicalAvg.toFixed(0)}ms`);
        console.log(`   Current duration: ${currentDuration.toFixed(0)}ms`);
        console.log(`   Regression ratio: ${(currentDuration / historicalAvg).toFixed(2)}x`);

        // Regression detection
        const hasRegression = currentDuration > (historicalAvg * regressionThreshold);

        if (hasRegression) {
          console.log('⚠️ Performance regression detected!');
        } else {
          console.log('✅ No significant performance regression');
        }

        expect(hasRegression).toBe(false);
      } else {
        console.log('📊 No historical data available for regression detection');
        // Just run a baseline test for future comparison
        const baselineScenario = testDataGenerator.getScenariosByComplexity('minimal')[0];
        const metrics = await executePerformanceTest(page, browserName || 'unknown', baselineScenario);
        performanceResults.push(metrics);
        expect(metrics.success).toBe(true);
      }
    });
  });

  async function executePerformanceTest(
    page: any,
    browser: string,
    scenario: TestScenario,
    timeoutMs: number = 20000,
    testIdSuffix: string = ''
  ): Promise<PerformanceMetrics> {
    const testStart = performance.now();
    const testId = `${scenario.id}${testIdSuffix ? '-' + testIdSuffix : ''}`;

    try {
      // Clear any existing content
      const clearButton = page.locator('button:has-text("Clear")').first();
      if (await clearButton.count() > 0) {
        await clearButton.click({ force: true });
        await page.waitForTimeout(500);
      }

      // Enter the test prompt
      const textInput = page.locator('textarea').first();
      await textInput.fill(scenario.prompt);

      // Start enhancement timing
      const enhancementStart = performance.now();

      const enhanceButton = page.locator('button:has-text("Enhance")').first();
      await enhanceButton.click();

      // Wait for enhancement completion with timeout
      await page.waitForTimeout(Math.min(timeoutMs, 2000)); // Wait at least 2 seconds

      // Check for completion (enhancement output)
      let outputLength = 0;
      try {
        const outputArea = page.locator('textarea').nth(1);
        const enhancedOutput = await outputArea.inputValue().catch(() => '');
        outputLength = enhancedOutput.length;

        // If no output yet, wait a bit more
        if (outputLength === 0) {
          await page.waitForTimeout(Math.min(timeoutMs - 2000, 5000));
          const retryOutput = await outputArea.inputValue().catch(() => '');
          outputLength = retryOutput.length;
        }
      } catch (error) {
        console.log('Could not retrieve output length:', error);
      }

      const enhancementEnd = performance.now();
      const testEnd = performance.now();

      return {
        testId,
        scenario: scenario.id,
        browser,
        startTime: testStart,
        endTime: testEnd,
        duration: testEnd - testStart,
        navigationTime: (page as any)._navigationTime || 0,
        enhancementTime: enhancementEnd - enhancementStart,
        outputLength,
        success: outputLength > 0
      };

    } catch (error) {
      const testEnd = performance.now();
      return {
        testId,
        scenario: scenario.id,
        browser,
        startTime: testStart,
        endTime: testEnd,
        duration: testEnd - testStart,
        navigationTime: (page as any)._navigationTime || 0,
        enhancementTime: testEnd - testStart,
        outputLength: 0,
        success: false,
        errorDetails: error instanceof Error ? error.message : String(error)
      };
    }
  }
});

function generatePerformanceSummary(results: PerformanceMetrics[]) {
  if (results.length === 0) return {};

  const successfulTests = results.filter(r => r.success);
  const failedTests = results.filter(r => !r.success);

  const durations = successfulTests.map(r => r.duration);
  const enhancementTimes = successfulTests.map(r => r.enhancementTime);

  return {
    totalTests: results.length,
    successfulTests: successfulTests.length,
    failedTests: failedTests.length,
    successRate: (successfulTests.length / results.length * 100).toFixed(1) + '%',
    performance: {
      averageDuration: durations.length > 0 ? (durations.reduce((sum, d) => sum + d, 0) / durations.length).toFixed(0) + 'ms' : 'N/A',
      medianDuration: durations.length > 0 ? durations.sort((a, b) => a - b)[Math.floor(durations.length / 2)].toFixed(0) + 'ms' : 'N/A',
      minDuration: durations.length > 0 ? Math.min(...durations).toFixed(0) + 'ms' : 'N/A',
      maxDuration: durations.length > 0 ? Math.max(...durations).toFixed(0) + 'ms' : 'N/A',
      averageEnhancement: enhancementTimes.length > 0 ? (enhancementTimes.reduce((sum, d) => sum + d, 0) / enhancementTimes.length).toFixed(0) + 'ms' : 'N/A'
    },
    byBrowser: groupBy(results, 'browser'),
    byComplexity: groupBy(results, r => {
      if (r.duration < 5000) return 'fast';
      if (r.duration < 15000) return 'moderate';
      if (r.duration < 30000) return 'slow';
      return 'very-slow';
    })
  };
}

function groupBy<T>(array: T[], keyFn: ((item: T) => string) | keyof T): Record<string, number> {
  return array.reduce((groups, item) => {
    const key = typeof keyFn === 'function' ? keyFn(item) : String(item[keyFn]);
    groups[key] = (groups[key] || 0) + 1;
    return groups;
  }, {} as Record<string, number>);
}
