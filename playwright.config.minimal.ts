import { defineConfig, devices } from '@playwright/test';

/**
 * Minimal Playwright configuration for Week 1 testing with Chromium only
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }]
  ],
  use: {
    baseURL: 'http://localhost:7860',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  /* Start with Chromium only for Week 1 validation */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  /* Global setup and teardown */
  globalSetup: require.resolve('./tests/e2e/fixtures/global-setup.ts'),
  globalTeardown: require.resolve('./tests/e2e/fixtures/global-teardown.ts'),

  /* Test output directory */
  outputDir: 'test-results/',

  /* Global test timeout - increased for reasonable response times */
  timeout: 120 * 1000, // 2 minutes

  /* Expect timeout for assertions */
  expect: {
    timeout: 30 * 1000, // 30 seconds for reasonable response expectations
  },
});
