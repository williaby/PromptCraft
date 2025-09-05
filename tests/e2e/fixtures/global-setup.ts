import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global test setup for PromptCraft-Hybrid...');
  
  // Launch browser for setup
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Wait for the application to be ready
    console.log('⏳ Waiting for application to be ready...');
    await page.goto('http://localhost:7860/');
    
    // Wait for Gradio to load completely - use actual Gradio selectors
    await page.waitForSelector('div:has-text("PromptCraft-Hybrid")', { timeout: 30000 });
    
    console.log('✅ Application health check passed');
    
    // Perform any additional setup (clear databases, seed data, etc.)
    await performTestSetup(page);
    
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
  
  console.log('✅ Global setup completed successfully');
}

async function performTestSetup(page: any) {
  // Clear any existing test data
  console.log('🧹 Cleaning up any existing test data...');
  
  // Clear any test data and ensure Gradio is fully loaded
  await page.goto('http://localhost:7860/');
  
  // Wait for Gradio components to be ready - look for the main title
  try {
    await page.waitForSelector('h1:has-text("PromptCraft-Hybrid")', { timeout: 10000 });
  } catch {
    // Fallback to looking for any Journey tab
    await page.waitForSelector('text=Journey 1: Smart Templates', { timeout: 10000 });
  }
  console.log('✅ Main interface loaded successfully');
}

export default globalSetup;