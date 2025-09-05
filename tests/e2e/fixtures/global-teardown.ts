import { chromium, FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting global test teardown...');
  
  // Launch browser for cleanup
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Clean up any test data that was created during tests
    await performTestCleanup(page);
    
  } catch (error) {
    console.error('⚠️ Global teardown encountered an error (non-critical):', error);
  } finally {
    await browser.close();
  }
  
  console.log('✅ Global teardown completed');
}

async function performTestCleanup(page: any) {
  // Clean up test data, sessions, temporary files, etc.
  console.log('🗑️ Performing test cleanup...');
  
  // Clear browser storage
  await page.context().clearCookies();
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  
  // You could add API calls here to clean up databases, remove test files, etc.
}

export default globalTeardown;