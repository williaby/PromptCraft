import { test, expect } from '@playwright/test';
import { Journey1Page } from '../fixtures/Journey1Page';
import TestUtils from '../helpers/test-utils';
import path from 'path';

test.describe('Journey 1: C.R.E.A.T.E. Framework Deep Validation', () => {
  let journey1Page: Journey1Page;
  const testDataDir = path.join(__dirname, '../data/files');

  test.beforeEach(async ({ page }) => {
    journey1Page = new Journey1Page(page);
    await journey1Page.gotoJourney1();
  });

  test.describe('Domain-Specific Framework Generation', () => {
    test('should generate complete framework for business domain prompts', async ({ page }) => {
      const businessPrompts = [
        'Develop a market entry strategy for Southeast Asian markets',
        'Create a comprehensive employee retention program',
        'Design a digital transformation roadmap for manufacturing',
        'Establish a sustainable supply chain management system'
      ];

      for (const prompt of businessPrompts) {
        await journey1Page.clearAll();
        await journey1Page.enterPrompt(prompt);
        await journey1Page.enhancePrompt(45000);

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        // Validate complete C.R.E.A.T.E. framework
        const createBreakdown = await journey1Page.validateCREATEBreakdown();
        const presentSections = createBreakdown.filter(section => section.present);

        // Business prompts should generate comprehensive frameworks
        expect(presentSections.length).toBeGreaterThanOrEqual(5);

        // Verify business-specific content quality
        expect(enhancedPrompt).toContain('business', { ignoreCase: true });
        expect(enhancedPrompt.length).toBeGreaterThan(prompt.length * 3); // Substantial enhancement

        console.log(`Business prompt "${prompt.substring(0, 30)}..." generated ${presentSections.length}/6 sections`);
      }
    });

    test('should generate complete framework for technical domain prompts', async ({ page }) => {
      const technicalPrompts = [
        'Design a microservices architecture for e-commerce platform',
        'Implement a real-time data processing pipeline with Kafka',
        'Create a machine learning model for fraud detection',
        'Develop a comprehensive API security strategy'
      ];

      for (const prompt of technicalPrompts) {
        await journey1Page.clearAll();
        await journey1Page.enterPrompt(prompt);
        await journey1Page.enhancePrompt(45000);

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        const createBreakdown = await journey1Page.validateCREATEBreakdown();
        const presentSections = createBreakdown.filter(section => section.present);

        // Technical prompts should generate detailed frameworks
        expect(presentSections.length).toBeGreaterThanOrEqual(5);

        // Verify technical depth
        expect(enhancedPrompt.length).toBeGreaterThan(prompt.length * 4);

        // Check for technical terminology presence
        const technicalTerms = ['architecture', 'implementation', 'system', 'technology', 'design'];
        const containsTechnicalTerms = technicalTerms.some(term =>
          enhancedPrompt.toLowerCase().includes(term)
        );
        expect(containsTechnicalTerms).toBe(true);

        console.log(`Technical prompt "${prompt.substring(0, 30)}..." generated ${presentSections.length}/6 sections`);
      }
    });

    test('should generate complete framework for creative domain prompts', async ({ page }) => {
      const creativePrompts = [
        'Write a compelling brand narrative for sustainable fashion startup',
        'Create an engaging social media content strategy for Gen Z audience',
        'Develop a storytelling framework for documentary filmmaking',
        'Design an immersive user experience for virtual reality application'
      ];

      for (const prompt of creativePrompts) {
        await journey1Page.clearAll();
        await journey1Page.enterPrompt(prompt);
        await journey1Page.enhancePrompt(45000);

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        const createBreakdown = await journey1Page.validateCREATEBreakdown();
        const presentSections = createBreakdown.filter(section => section.present);

        // Creative prompts should generate comprehensive frameworks
        expect(presentSections.length).toBeGreaterThanOrEqual(4);

        // Verify creative elements
        const creativeTerms = ['creative', 'design', 'story', 'experience', 'audience', 'narrative'];
        const containsCreativeTerms = creativeTerms.some(term =>
          enhancedPrompt.toLowerCase().includes(term)
        );
        expect(containsCreativeTerms).toBe(true);

        console.log(`Creative prompt "${prompt.substring(0, 30)}..." generated ${presentSections.length}/6 sections`);
      }
    });

    test('should generate complete framework for academic domain prompts', async ({ page }) => {
      const academicPrompts = [
        'Conduct a systematic literature review on climate change adaptation',
        'Design a longitudinal research study on remote work productivity',
        'Analyze the socioeconomic impact of artificial intelligence adoption',
        'Develop a theoretical framework for sustainable urban development'
      ];

      for (const prompt of academicPrompts) {
        await journey1Page.clearAll();
        await journey1Page.enterPrompt(prompt);
        await journey1Page.enhancePrompt(45000);

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        const createBreakdown = await journey1Page.validateCREATEBreakdown();
        const presentSections = createBreakdown.filter(section => section.present);

        // Academic prompts should generate rigorous frameworks
        expect(presentSections.length).toBeGreaterThanOrEqual(5);

        // Verify academic rigor
        const academicTerms = ['research', 'analysis', 'study', 'methodology', 'framework', 'literature'];
        const containsAcademicTerms = academicTerms.some(term =>
          enhancedPrompt.toLowerCase().includes(term)
        );
        expect(containsAcademicTerms).toBe(true);

        console.log(`Academic prompt "${prompt.substring(0, 30)}..." generated ${presentSections.length}/6 sections`);
      }
    });
  });

  test.describe('Framework Completeness and Quality Validation', () => {
    test('should handle incomplete framework generation gracefully', async ({ page }) => {
      // Test with very brief or ambiguous prompts that might not generate complete frameworks
      const briefPrompts = [
        'Help',
        'Do something',
        'Fix it',
        'Make better'
      ];

      for (const prompt of briefPrompts) {
        await journey1Page.clearAll();
        await journey1Page.enterPrompt(prompt);
        await journey1Page.enhancePrompt();

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();

        if (enhancedPrompt && enhancedPrompt.length > 0) {
          // If enhancement was generated, validate quality
          const createBreakdown = await journey1Page.validateCREATEBreakdown();
          const presentSections = createBreakdown.filter(section => section.present);

          // Even with brief prompts, should have some framework structure
          expect(presentSections.length).toBeGreaterThan(0);

          console.log(`Brief prompt "${prompt}" generated ${presentSections.length}/6 sections`);
        } else {
          // If no enhancement, check for appropriate error handling
          const hasError = await journey1Page.hasError();
          if (hasError) {
            const errorMessage = await journey1Page.getErrorMessage();
            expect(errorMessage.length).toBeGreaterThan(0);
            console.log(`Brief prompt "${prompt}" handled with error: ${errorMessage}`);
          }
        }
      }
    });

    test('should maintain framework consistency across model changes', async ({ page }) => {
      const testPrompt = 'Create a comprehensive project management methodology for software development teams';
      const models = ['gpt-4o', 'gpt-4o-mini']; // Test available models

      const frameworkResults = [];

      for (const model of models) {
        await journey1Page.clearAll();

        try {
          await journey1Page.selectModel(model);
        } catch (error) {
          console.log(`Model ${model} not available, skipping`);
          continue;
        }

        await journey1Page.enterPrompt(testPrompt);
        await journey1Page.enhancePrompt(45000);

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        const createBreakdown = await journey1Page.validateCREATEBreakdown();
        const presentSections = createBreakdown.filter(section => section.present);

        frameworkResults.push({
          model,
          sectionsCount: presentSections.length,
          sections: presentSections.map(s => s.name),
          promptLength: enhancedPrompt.length
        });

        // Each model should generate substantial framework
        expect(presentSections.length).toBeGreaterThanOrEqual(4);

        console.log(`Model ${model} generated ${presentSections.length}/6 sections`);
      }

      // Verify consistency across models
      if (frameworkResults.length > 1) {
        const sectionCounts = frameworkResults.map(r => r.sectionsCount);
        const avgSectionCount = sectionCounts.reduce((a, b) => a + b, 0) / sectionCounts.length;

        // All models should generate similar framework completeness
        sectionCounts.forEach(count => {
          expect(Math.abs(count - avgSectionCount)).toBeLessThanOrEqual(2);
        });

        console.log('Framework consistency verified across models:', frameworkResults);
      }
    });

    test('should validate individual C.R.E.A.T.E. component quality', async ({ page }) => {
      const testPrompt = 'Develop a comprehensive employee wellness program that addresses physical health, mental well-being, and work-life balance for a distributed remote workforce';

      await journey1Page.enterPrompt(testPrompt);
      await journey1Page.enhancePrompt(45000);

      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();

      // Validate each C.R.E.A.T.E. component quality
      const createBreakdown = await journey1Page.validateCREATEBreakdown();

      // Context Section Quality
      const contextSection = createBreakdown.find(s => s.name === 'Context');
      if (contextSection && contextSection.present) {
        expect(enhancedPrompt).toContain('context', { ignoreCase: true });
        expect(enhancedPrompt).toContain('background', { ignoreCase: true });
      }

      // Request Section Quality
      const requestSection = createBreakdown.find(s => s.name === 'Request');
      if (requestSection && requestSection.present) {
        expect(enhancedPrompt).toContain('request', { ignoreCase: true });
        expect(enhancedPrompt).toContain('objective', { ignoreCase: true });
      }

      // Examples Section Quality
      const examplesSection = createBreakdown.find(s => s.name === 'Examples');
      if (examplesSection && examplesSection.present) {
        expect(enhancedPrompt).toContain('example', { ignoreCase: true });
      }

      // Augmentations Section Quality
      const augmentationsSection = createBreakdown.find(s => s.name === 'Augmentations');
      if (augmentationsSection && augmentationsSection.present) {
        expect(enhancedPrompt).toContain('augmentation', { ignoreCase: true });
      }

      // Tone & Format Section Quality
      const toneSection = createBreakdown.find(s => s.name === 'Tone');
      if (toneSection && toneSection.present) {
        expect(enhancedPrompt).toContain('tone', { ignoreCase: true });
      }

      // Evaluation Section Quality
      const evaluationSection = createBreakdown.find(s => s.name === 'Evaluation');
      if (evaluationSection && evaluationSection.present) {
        expect(enhancedPrompt).toContain('evaluation', { ignoreCase: true });
        expect(enhancedPrompt).toContain('criteria', { ignoreCase: true });
      }

      console.log('C.R.E.A.T.E. component quality validation completed:', createBreakdown);
    });

    test('should handle framework customization based on context', async ({ page }) => {
      // Test how framework adapts to different contexts within same domain
      const contextVariations = [
        {
          prompt: 'Create a marketing strategy for a B2B SaaS startup targeting enterprise customers',
          expectedContext: ['B2B', 'enterprise', 'SaaS']
        },
        {
          prompt: 'Create a marketing strategy for a B2C e-commerce brand targeting millennials',
          expectedContext: ['B2C', 'e-commerce', 'millennial']
        },
        {
          prompt: 'Create a marketing strategy for a nonprofit organization focusing on environmental conservation',
          expectedContext: ['nonprofit', 'environmental', 'conservation']
        }
      ];

      for (const variation of contextVariations) {
        await journey1Page.clearAll();
        await journey1Page.enterPrompt(variation.prompt);
        await journey1Page.enhancePrompt(45000);

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        // Verify context-specific customization
        variation.expectedContext.forEach(contextTerm => {
          expect(enhancedPrompt).toContain(contextTerm, { ignoreCase: true });
        });

        const createBreakdown = await journey1Page.validateCREATEBreakdown();
        const presentSections = createBreakdown.filter(section => section.present);

        // Should maintain framework completeness regardless of context
        expect(presentSections.length).toBeGreaterThanOrEqual(4);

        console.log(`Context variation "${variation.prompt.substring(0, 40)}..." customized appropriately`);
      }
    });
  });

  test.describe('Framework Integration with File Context', () => {
    test('should integrate uploaded file context into C.R.E.A.T.E. framework', async ({ page }) => {
      const businessFile = path.join(testDataDir, 'sample-data.csv');

      // Upload context file
      await journey1Page.uploadTestFile(businessFile);

      // Create prompt that should leverage file context
      const contextPrompt = 'Analyze the uploaded data and create a comprehensive business intelligence dashboard strategy';
      await journey1Page.enterPrompt(contextPrompt);
      await journey1Page.enhancePrompt(45000);

      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();

      // Verify file context integration
      expect(enhancedPrompt).toContain('data', { ignoreCase: true });
      expect(enhancedPrompt).toContain('dashboard', { ignoreCase: true });

      // Validate C.R.E.A.T.E. framework incorporates file context
      const createBreakdown = await journey1Page.validateCREATEBreakdown();
      const presentSections = createBreakdown.filter(section => section.present);

      // File context should enhance framework completeness
      expect(presentSections.length).toBeGreaterThanOrEqual(5);

      // Context section should reference uploaded file
      const contextSection = createBreakdown.find(s => s.name === 'Context');
      expect(contextSection?.present).toBe(true);

      console.log('File context successfully integrated into C.R.E.A.T.E. framework');
    });

    test('should adapt framework based on multiple file types', async ({ page }) => {
      const multipleFiles = [
        path.join(testDataDir, 'test-document.md'),
        path.join(testDataDir, 'config-sample.json'),
        path.join(testDataDir, 'sample-data.csv')
      ];

      // Upload multiple files
      for (const file of multipleFiles) {
        await journey1Page.uploadTestFile(file);
        await page.waitForTimeout(500);
      }

      const fileSources = await journey1Page.getFileSources();
      expect(fileSources.length).toBeGreaterThan(1);

      // Create comprehensive analysis prompt
      const multiFilePrompt = 'Create a comprehensive technical documentation strategy based on all uploaded files';
      await journey1Page.enterPrompt(multiFilePrompt);
      await journey1Page.enhancePrompt(60000); // Longer timeout for multiple files

      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();

      // Verify multi-file context integration
      expect(enhancedPrompt).toContain('documentation', { ignoreCase: true });
      expect(enhancedPrompt).toContain('technical', { ignoreCase: true });

      // Framework should be comprehensive with multiple context sources
      const createBreakdown = await journey1Page.validateCREATEBreakdown();
      const presentSections = createBreakdown.filter(section => section.present);

      expect(presentSections.length).toBeGreaterThanOrEqual(5);

      console.log(`Multi-file framework generation completed with ${fileSources.length} sources`);
    });
  });
});
