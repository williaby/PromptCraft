import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class Journey1Page extends BasePage {
  // Input elements
  readonly textInput: Locator;
  readonly fileUpload: Locator;
  readonly modelSelector: Locator;
  readonly customModelSelector: Locator;
  
  // Action buttons
  readonly enhanceButton: Locator;
  readonly clearButton: Locator;
  readonly copyCodeButton: Locator;
  readonly copyMarkdownButton: Locator;
  readonly exportButton: Locator;
  
  // Output elements
  readonly enhancedPromptOutput: Locator;
  readonly contextAnalysis: Locator;
  readonly requestSpecification: Locator;
  readonly examplesSection: Locator;
  readonly augmentationsSection: Locator;
  readonly toneFormat: Locator;
  readonly evaluationCriteria: Locator;
  readonly modelAttribution: Locator;
  readonly fileSources: Locator;
  
  // Status elements
  readonly progressIndicator: Locator;
  readonly costTracker: Locator;
  readonly errorMessage: Locator;
  
  constructor(page: Page) {
    super(page);
    
    // Initialize Journey 1 specific locators
    this.textInput = page.locator('textarea[placeholder*="prompt"], textarea[label*="Input"]').first();
    this.fileUpload = page.locator('input[type="file"]').first();
    this.modelSelector = page.locator('select, .dropdown').filter({ hasText: /gpt|claude|model/i }).first();
    this.customModelSelector = page.locator('input[placeholder*="custom"], input[label*="Custom"]').first();
    
    // Action buttons
    this.enhanceButton = page.locator('button', { hasText: /enhance|process|submit/i }).first();
    this.clearButton = page.locator('button', { hasText: /clear|reset/i }).first();
    this.copyCodeButton = page.locator('button', { hasText: /copy.*code/i }).first();
    this.copyMarkdownButton = page.locator('button', { hasText: /copy.*markdown/i }).first();
    this.exportButton = page.locator('button', { hasText: /export/i }).first();
    
    // Output elements - look for C.R.E.A.T.E. framework sections
    this.enhancedPromptOutput = page.locator('[data-testid="enhanced-prompt"], .output-text').first();
    this.contextAnalysis = page.locator('text=Context:').locator('..').first();
    this.requestSpecification = page.locator('text=Request:').locator('..').first();
    this.examplesSection = page.locator('text=Examples:').locator('..').first();
    this.augmentationsSection = page.locator('text=Augmentations:').locator('..').first();
    this.toneFormat = page.locator('text=Tone:').locator('..').first();
    this.evaluationCriteria = page.locator('text=Evaluation:').locator('..').first();
    this.modelAttribution = page.locator('.model-attribution, [id="model-attribution"]');
    this.fileSources = page.locator('#file-sources, [data-testid="file-sources"]');
    
    // Status elements
    this.progressIndicator = page.locator('.progress-indicator, .loading, [data-testid="progress"]');
    this.costTracker = page.locator('text=Cost:').locator('..').or(page.locator('.cost-tracker'));
    this.errorMessage = page.locator('.error, .alert-error, [data-testid="error"]');
  }

  /**
   * Navigate to Journey 1 and wait for it to load
   */
  async gotoJourney1() {
    await this.goto();
    await this.switchToJourney(1);
    await this.waitForJourney1Load();
  }

  /**
   * Wait for Journey 1 specific components to load
   */
  async waitForJourney1Load() {
    await this.textInput.waitFor({ state: 'visible' });
    await this.enhanceButton.waitFor({ state: 'visible' });
  }

  /**
   * Enter text prompt for enhancement
   */
  async enterPrompt(text: string) {
    await this.typeText(this.textInput, text);
  }

  /**
   * Select a model from the dropdown
   */
  async selectModel(modelName: string) {
    await this.modelSelector.click();
    await this.page.locator(`option[value="${modelName}"], text=${modelName}`).first().click();
  }

  /**
   * Upload a test file
   */
  async uploadTestFile(filePath: string) {
    await this.uploadFile(this.fileUpload, filePath);
    
    // Wait for file to be processed
    await this.page.waitForTimeout(1000);
    
    // Check if file processing completed
    await this.page.waitForFunction(() => {
      const fileProcessingElements = document.querySelectorAll('.processing-file, .uploading');
      return fileProcessingElements.length === 0;
    }, { timeout: 10000 });
  }

  /**
   * Click enhance button and wait for processing
   */
  async enhancePrompt(timeout = 30000) {
    await this.enhanceButton.click();
    
    // Wait for processing to start (progress indicator appears)
    try {
      await this.progressIndicator.waitFor({ state: 'visible', timeout: 5000 });
    } catch {
      // Progress indicator might not appear for quick responses
    }
    
    // Wait for processing to complete (progress indicator disappears)
    await this.progressIndicator.waitFor({ state: 'hidden', timeout });
    
    // Wait for output to appear
    await this.enhancedPromptOutput.waitFor({ state: 'visible', timeout: 5000 });
  }

  /**
   * Validate C.R.E.A.T.E. framework breakdown is present
   */
  async validateCREATEBreakdown() {
    const sections = [
      { name: 'Context', locator: this.contextAnalysis },
      { name: 'Request', locator: this.requestSpecification },
      { name: 'Examples', locator: this.examplesSection },
      { name: 'Augmentations', locator: this.augmentationsSection },
      { name: 'Tone', locator: this.toneFormat },
      { name: 'Evaluation', locator: this.evaluationCriteria }
    ];

    const results = [];
    for (const section of sections) {
      try {
        await expect(section.locator).toBeVisible({ timeout: 5000 });
        results.push({ name: section.name, present: true });
      } catch {
        results.push({ name: section.name, present: false });
      }
    }

    return results;
  }

  /**
   * Get the enhanced prompt text
   */
  async getEnhancedPrompt(): Promise<string> {
    await this.enhancedPromptOutput.waitFor({ state: 'visible' });
    return await this.enhancedPromptOutput.textContent() || '';
  }

  /**
   * Copy code blocks functionality
   */
  async copyCodeBlocks() {
    await this.copyCodeButton.click();
    
    // Wait for success feedback
    await this.waitForText('copied', 3000);
  }

  /**
   * Copy as markdown functionality
   */
  async copyAsMarkdown() {
    await this.copyMarkdownButton.click();
    
    // Wait for success feedback
    await this.waitForText('copied', 3000);
  }

  /**
   * Export content functionality
   */
  async exportContent(format: 'md' | 'txt' | 'json' = 'md') {
    await this.exportButton.click();
    
    // Select format if dropdown appears
    try {
      await this.page.locator(`text=${format.toUpperCase()}`).click({ timeout: 2000 });
    } catch {
      // Format selector might not be visible or format already selected
    }
    
    // Wait for download to be triggered
    const downloadPromise = this.page.waitForEvent('download');
    const download = await downloadPromise;
    
    return download;
  }

  /**
   * Get model attribution information
   */
  async getModelAttribution() {
    await this.modelAttribution.waitFor({ state: 'visible' });
    const text = await this.modelAttribution.textContent();
    
    // Parse model name, time, and cost from attribution
    const modelMatch = text?.match(/Generated by:\s*([^\s|]+)/);
    const timeMatch = text?.match(/Time:\s*([\d.]+s)/);
    const costMatch = text?.match(/Cost:\s*\$?([\d.]+)/);
    
    return {
      model: modelMatch?.[1] || 'unknown',
      time: timeMatch?.[1] || '0s',
      cost: costMatch?.[1] || '0'
    };
  }

  /**
   * Get file sources information
   */
  async getFileSources(): Promise<string[]> {
    try {
      await this.fileSources.waitFor({ state: 'visible', timeout: 3000 });
      const text = await this.fileSources.textContent() || '';
      
      // Extract file names from the sources text
      const fileMatches = text.match(/([^\s]+\.(txt|md|csv|json|pdf|docx))/g);
      return fileMatches || [];
    } catch {
      return [];
    }
  }

  /**
   * Get current cost from cost tracker
   */
  async getCurrentCost(): Promise<number> {
    try {
      await this.costTracker.waitFor({ state: 'visible', timeout: 3000 });
      const text = await this.costTracker.textContent() || '0';
      const costMatch = text.match(/\$?([\d.]+)/);
      return parseFloat(costMatch?.[1] || '0');
    } catch {
      return 0;
    }
  }

  /**
   * Check if there's an error message displayed
   */
  async hasError(): Promise<boolean> {
    try {
      await this.errorMessage.waitFor({ state: 'visible', timeout: 2000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get error message text if present
   */
  async getErrorMessage(): Promise<string> {
    if (await this.hasError()) {
      return await this.errorMessage.textContent() || '';
    }
    return '';
  }

  /**
   * Clear all inputs
   */
  async clearAll() {
    if (await this.clearButton.isVisible()) {
      await this.clearButton.click();
    } else {
      await this.textInput.clear();
    }
    
    await this.page.waitForTimeout(500);
  }

  /**
   * Test file upload validation
   */
  async testFileValidation(filePath: string, expectError = false) {
    await this.uploadFile(this.fileUpload, filePath);
    
    if (expectError) {
      // Expect error message to appear
      await this.errorMessage.waitFor({ state: 'visible', timeout: 5000 });
      return await this.getErrorMessage();
    } else {
      // Expect successful upload
      await this.page.waitForTimeout(2000);
      return !await this.hasError();
    }
  }
}

export default Journey1Page;