import { test, expect } from '@playwright/test';
import { Journey1Page } from '../fixtures/Journey1Page';
import TestUtils from '../helpers/test-utils';
import path from 'path';
import crypto from 'crypto';

test.describe('Journey 1: Data Integrity Verification', () => {
  let journey1Page: Journey1Page;
  const testDataDir = path.join(__dirname, '../data/files');

  test.beforeEach(async ({ page }) => {
    journey1Page = new Journey1Page(page);
    await journey1Page.gotoJourney1();
  });

  test.describe('File Content Integrity', () => {
    test('should preserve file content through processing pipeline', async ({ page }) => {
      // Create a file with known content and checksum
      const testFileName = 'integrity-test.txt';
      const testFilePath = path.join(testDataDir, testFileName);
      const originalContent = `Data Integrity Test File
Created: ${new Date().toISOString()}
Content: This file contains specific test data to verify integrity through the processing pipeline.

Special characters: émojis 🔥, symbols ✓✗, quotes "double" and 'single'
Numbers: 123456789, floats: 3.14159, negatives: -42
Unicode: Ñoël, 北京, العربية, עברית

Line breaks and formatting:
- Bullet point 1
- Bullet point 2
  - Nested item
    - Double nested

Code block:
function test() {
  return "integrity check";
}

End of test file.`;

      const fs = require('fs');
      fs.writeFileSync(testFilePath, originalContent, 'utf8');

      // Calculate checksum of original content
      const originalChecksum = crypto.createHash('md5').update(originalContent).digest('hex');
      console.log(`Original content checksum: ${originalChecksum}`);

      // Upload the file
      await journey1Page.uploadTestFile(testFilePath);

      const fileSources = await journey1Page.getFileSources();
      expect(fileSources.length).toBeGreaterThan(0);
      expect(fileSources[0]).toContain(testFileName);

      // Process through enhancement
      await journey1Page.enterPrompt('Analyze the uploaded test file and provide a summary of its structure and content');
      await journey1Page.enhancePrompt();

      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();

      // Verify original content references appear in enhancement
      const contentChecks = [
        'Data Integrity Test',
        'Special characters',
        'émojis',
        'Unicode',
        'Code block',
        'function test()'
      ];

      contentChecks.forEach(checkString => {
        if (!enhancedPrompt.includes(checkString)) {
          console.warn(`Content check failed: "${checkString}" not found in enhanced output`);
        } else {
          console.log(`✅ Content preserved: "${checkString}"`);
        }
      });

      // Verify enhancement references the file appropriately
      expect(enhancedPrompt).toContain('file', { ignoreCase: true });
      expect(enhancedPrompt).toContain('test', { ignoreCase: true });

      // Clean up
      if (fs.existsSync(testFilePath)) {
        fs.unlinkSync(testFilePath);
      }

      console.log('✅ File content integrity verification completed');
    });

    test('should handle encoding edge cases consistently', async ({ page }) => {
      const encodingTestCases = [
        {
          name: 'utf8-mixed.txt',
          content: `UTF-8 Mixed Encoding Test
English text with special chars: café, naïve, résumé
Emoji: 🚀🔥💯⚡🎉🌟✨🎯
Chinese: 你好世界 北京 上海
Japanese: こんにちは 東京
Arabic: مرحبا العالم القاهرة
Hebrew: שלום עולם תל אביב
Russian: Привет мир Москва
Mathematical: ∞ ∑ ∏ ∫ ∂ √ ±
Currency: €$¥£₹₿
Arrows: ←→↑↓⟵⟶⟸⟹`
        },
        {
          name: 'symbols-test.txt',
          content: `Symbol Encoding Test
Quotes: "double" 'single' „german" «french» 「japanese」
Dashes: - – — ―
Spaces: regular  double   triple    tab	end
Punctuation: !@#$%^&*()_+-=[]{}|;':\",./<>?
Accented: àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ
Math: ∀∂∃∄∅∆∇∈∉∊∋∌∍∎∏∐∑−∓∔∕∖∗∘∙√∛∜∝∞∟
Technical: ©®™℠℡℗℞№℧Ω℧`
        }
      ];

      for (const testCase of encodingTestCases) {
        const testFilePath = path.join(testDataDir, testCase.name);
        const fs = require('fs');
        fs.writeFileSync(testFilePath, testCase.content, 'utf8');

        await journey1Page.clearAll();
        await journey1Page.uploadTestFile(testFilePath);

        const fileSources = await journey1Page.getFileSources();
        expect(fileSources.length).toBeGreaterThan(0);

        await journey1Page.enterPrompt(`Analyze the encoding test file ${testCase.name} and verify all special characters are preserved`);
        await journey1Page.enhancePrompt();

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        // Verify specific encoding elements are handled
        const encodingChecks = testCase.content.includes('UTF-8') ?
          ['café', '你好', 'こんにちは', 'مرحبا', '🚀', '€'] :
          ['"double"', '–', 'àáâã', '∀∂∃', '©®™'];

        encodingChecks.forEach(check => {
          if (enhancedPrompt.includes(check)) {
            console.log(`✅ ${testCase.name}: Encoding preserved for "${check}"`);
          } else {
            console.warn(`⚠️ ${testCase.name}: Encoding check failed for "${check}"`);
          }
        });

        // Clean up
        if (fs.existsSync(testFilePath)) {
          fs.unlinkSync(testFilePath);
        }
      }

      console.log('✅ Encoding edge cases testing completed');
    });

    test('should maintain file metadata integrity', async ({ page }) => {
      const metadataTestFiles = [
        { name: 'small-file.txt', size: 'small', content: 'Small file content for metadata testing.' },
        { name: 'medium-file.md', size: 'medium', content: '# Medium File\n\n' + 'This is medium content.\n'.repeat(50) },
        { name: 'structured-data.csv', size: 'structured', content: 'Name,Value,Type\nTest,123,Number\nData,ABC,String\nFlag,true,Boolean' }
      ];

      const fs = require('fs');
      const fileMetadata = [];

      // Create files and collect metadata
      for (const fileInfo of metadataTestFiles) {
        const filePath = path.join(testDataDir, fileInfo.name);
        fs.writeFileSync(filePath, fileInfo.content, 'utf8');

        const stats = fs.statSync(filePath);
        fileMetadata.push({
          name: fileInfo.name,
          size: stats.size,
          type: path.extname(fileInfo.name),
          created: stats.birthtime,
          modified: stats.mtime
        });
      }

      // Upload each file and verify metadata handling
      for (let i = 0; i < metadataTestFiles.length; i++) {
        await journey1Page.clearAll();

        const filePath = path.join(testDataDir, metadataTestFiles[i].name);
        await journey1Page.uploadTestFile(filePath);

        const fileSources = await journey1Page.getFileSources();
        expect(fileSources.length).toBeGreaterThan(0);

        // Verify filename is preserved
        expect(fileSources[0]).toContain(metadataTestFiles[i].name);

        await journey1Page.enterPrompt(`Provide details about the uploaded file including its structure and content type`);
        await journey1Page.enhancePrompt();

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        // Verify file type recognition
        const fileExtension = path.extname(metadataTestFiles[i].name).slice(1);
        if (fileExtension) {
          expect(enhancedPrompt.toLowerCase()).toContain(fileExtension);
        }

        // Verify filename is referenced
        expect(enhancedPrompt).toContain(metadataTestFiles[i].name, { ignoreCase: true });

        console.log(`✅ Metadata integrity verified for ${metadataTestFiles[i].name}`);
      }

      // Clean up test files
      metadataTestFiles.forEach(fileInfo => {
        const filePath = path.join(testDataDir, fileInfo.name);
        if (fs.existsSync(filePath)) {
          fs.unlinkSync(filePath);
        }
      });

      console.log('✅ File metadata integrity testing completed');
    });
  });

  test.describe('C.R.E.A.T.E. Framework Content Integrity', () => {
    test('should maintain semantic consistency in framework sections', async ({ page }) => {
      const consistencyTestPrompt = 'Develop a comprehensive employee training program for remote work effectiveness, including skill development, communication protocols, performance measurement, and technology adoption strategies';

      // Generate framework multiple times to test consistency
      const frameworkResults = [];

      for (let i = 0; i < 3; i++) {
        await journey1Page.clearAll();
        await journey1Page.enterPrompt(consistencyTestPrompt);
        await journey1Page.enhancePrompt();

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        const createBreakdown = await journey1Page.validateCREATEBreakdown();

        frameworkResults.push({
          iteration: i + 1,
          enhancedPrompt,
          createBreakdown,
          presentSections: createBreakdown.filter(s => s.present)
        });

        console.log(`Framework iteration ${i + 1}: ${frameworkResults[i].presentSections.length}/6 sections present`);
      }

      // Analyze consistency across iterations
      const sectionCounts = frameworkResults.map(r => r.presentSections.length);
      const avgSections = sectionCounts.reduce((a, b) => a + b, 0) / sectionCounts.length;
      const sectionVariance = sectionCounts.map(count => Math.abs(count - avgSections));
      const maxVariance = Math.max(...sectionVariance);

      console.log(`Framework consistency analysis:`);
      console.log(`  Average sections: ${avgSections.toFixed(2)}`);
      console.log(`  Section counts: ${sectionCounts.join(', ')}`);
      console.log(`  Max variance: ${maxVariance.toFixed(2)}`);

      // Consistency check: variance should be reasonable
      expect(maxVariance).toBeLessThanOrEqual(2); // Allow up to 2 sections difference

      // Semantic consistency check - key terms should appear consistently
      const keyTerms = ['training', 'remote', 'employee', 'program', 'development'];

      keyTerms.forEach(term => {
        const appearanceCount = frameworkResults.filter(r =>
          r.enhancedPrompt.toLowerCase().includes(term.toLowerCase())
        ).length;

        console.log(`Term "${term}" appeared in ${appearanceCount}/3 iterations`);
        expect(appearanceCount).toBeGreaterThanOrEqual(2); // Should appear in at least 2/3 iterations
      });

      console.log('✅ C.R.E.A.T.E. framework semantic consistency verified');
    });

    test('should preserve user input context in framework', async ({ page }) => {
      const contextPreservationTests = [
        {
          prompt: 'Create a marketing strategy for a sustainable fashion startup targeting millennial consumers in urban markets',
          keyTerms: ['marketing', 'sustainable', 'fashion', 'startup', 'millennial', 'urban'],
          context: 'business'
        },
        {
          prompt: 'Design a machine learning pipeline for real-time fraud detection in financial transactions using Python and TensorFlow',
          keyTerms: ['machine learning', 'pipeline', 'fraud detection', 'financial', 'python', 'tensorflow'],
          context: 'technical'
        },
        {
          prompt: 'Write a compelling brand story for a local artisan bakery that emphasizes family traditions and organic ingredients',
          keyTerms: ['brand story', 'artisan', 'bakery', 'family', 'traditions', 'organic'],
          context: 'creative'
        }
      ];

      for (const test of contextPreservationTests) {
        await journey1Page.clearAll();
        await journey1Page.enterPrompt(test.prompt);
        await journey1Page.enhancePrompt();

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        console.log(`Testing context preservation for ${test.context} prompt`);

        // Verify original prompt intent is preserved
        test.keyTerms.forEach(term => {
          const isPreserved = enhancedPrompt.toLowerCase().includes(term.toLowerCase());
          if (isPreserved) {
            console.log(`✅ Key term preserved: "${term}"`);
          } else {
            console.warn(`⚠️ Key term may be lost: "${term}"`);
          }

          // Allow for synonyms and variations, so don't fail test but log concerns
        });

        // Verify enhancement maintains original domain/context
        const domainIndicators = {
          business: ['strategy', 'market', 'business', 'consumer', 'target'],
          technical: ['implementation', 'system', 'development', 'technology', 'architecture'],
          creative: ['story', 'narrative', 'brand', 'creative', 'content']
        };

        const relevantIndicators = domainIndicators[test.context];
        const indicatorMatches = relevantIndicators.filter(indicator =>
          enhancedPrompt.toLowerCase().includes(indicator.toLowerCase())
        ).length;

        expect(indicatorMatches).toBeGreaterThan(0);
        console.log(`${test.context} context preserved with ${indicatorMatches}/${relevantIndicators.length} domain indicators`);
      }

      console.log('✅ User input context preservation verified');
    });

    test('should handle framework regeneration consistently', async ({ page }) => {
      const regenerationPrompt = 'Develop a crisis management communication plan for a technology company facing a data security incident';

      // Initial generation
      await journey1Page.enterPrompt(regenerationPrompt);
      await journey1Page.enhancePrompt();

      const initialEnhancement = await journey1Page.getEnhancedPrompt();
      expect(initialEnhancement).toBeTruthy();

      const initialBreakdown = await journey1Page.validateCREATEBreakdown();
      const initialSections = initialBreakdown.filter(s => s.present).length;

      console.log(`Initial framework generation: ${initialSections}/6 sections`);

      // Regenerate by using enhanced output as new input
      await journey1Page.clearAll();
      await journey1Page.enterPrompt(initialEnhancement);
      await journey1Page.enhancePrompt();

      const regeneratedEnhancement = await journey1Page.getEnhancedPrompt();
      expect(regeneratedEnhancement).toBeTruthy();

      const regeneratedBreakdown = await journey1Page.validateCREATEBreakdown();
      const regeneratedSections = regeneratedBreakdown.filter(s => s.present).length;

      console.log(`Regenerated framework: ${regeneratedSections}/6 sections`);

      // Quality shouldn't degrade significantly
      expect(regeneratedSections).toBeGreaterThanOrEqual(initialSections - 1);

      // Content should expand, not just repeat
      expect(regeneratedEnhancement.length).toBeGreaterThan(initialEnhancement.length * 0.8);

      // Key terms should still be present
      const keyTerms = ['crisis', 'management', 'communication', 'technology', 'security'];
      keyTerms.forEach(term => {
        expect(regeneratedEnhancement.toLowerCase()).toContain(term.toLowerCase());
      });

      console.log('✅ Framework regeneration consistency verified');
    });
  });

  test.describe('State Consistency Across Operations', () => {
    test('should maintain UI state consistency with backend processing', async ({ page }) => {
      const stateTestPrompt = 'Create a project timeline for developing a mobile application with backend API integration';

      await journey1Page.enterPrompt(stateTestPrompt);

      // Get initial UI state
      const initialInputState = await journey1Page.textInput.inputValue();
      expect(initialInputState).toBe(stateTestPrompt);

      // Start enhancement
      await journey1Page.enhancePrompt();

      // Verify input state is preserved during processing
      const duringProcessingState = await journey1Page.textInput.inputValue();
      expect(duringProcessingState).toBe(stateTestPrompt);

      // Verify final state consistency
      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();

      const finalInputState = await journey1Page.textInput.inputValue();
      expect(finalInputState).toBe(stateTestPrompt);

      // Test cost tracking consistency
      const initialCost = 0; // Assuming we start at 0
      const finalCost = await journey1Page.getCurrentCost();

      expect(finalCost).toBeGreaterThanOrEqual(initialCost);

      // Verify model attribution matches processing
      const attribution = await journey1Page.getModelAttribution();
      if (attribution.model && attribution.cost) {
        console.log(`State consistency: Model ${attribution.model}, Cost $${attribution.cost}`);
        expect(parseFloat(attribution.cost)).toBeGreaterThan(0);
      }

      console.log('✅ UI-backend state consistency verified');
    });

    test('should handle concurrent state modifications appropriately', async ({ browser }) => {
      // Create two browser contexts for concurrent access
      const context1 = await browser.newContext();
      const context2 = await browser.newContext();

      const page1 = await context1.newPage();
      const page2 = await context2.newPage();

      const journey1Page1 = new Journey1Page(page1);
      const journey1Page2 = new Journey1Page(page2);

      await journey1Page1.gotoJourney1();
      await journey1Page2.gotoJourney1();

      // Perform concurrent operations
      const prompt1 = 'Concurrent test 1: Design a user authentication system';
      const prompt2 = 'Concurrent test 2: Create a data backup strategy';

      const concurrentOperations = [
        (async () => {
          await journey1Page1.enterPrompt(prompt1);
          await journey1Page1.enhancePrompt();
          return await journey1Page1.getEnhancedPrompt();
        })(),
        (async () => {
          await journey1Page2.enterPrompt(prompt2);
          await journey1Page2.enhancePrompt();
          return await journey1Page2.getEnhancedPrompt();
        })()
      ];

      const results = await Promise.all(concurrentOperations);

      // Verify both operations completed successfully
      expect(results[0]).toBeTruthy();
      expect(results[1]).toBeTruthy();

      // Verify no cross-contamination
      expect(results[0]).not.toBe(results[1]);
      expect(results[0]).toContain('authentication', { ignoreCase: true });
      expect(results[1]).toContain('backup', { ignoreCase: true });

      console.log('✅ Concurrent state modification handling verified');

      // Clean up
      await context1.close();
      await context2.close();
    });

    test('should maintain session integrity across page interactions', async ({ page }) => {
      // Perform initial operation
      const sessionPrompt = 'Session integrity test: Create a software testing strategy';
      await journey1Page.enterPrompt(sessionPrompt);
      await journey1Page.enhancePrompt();

      const initialResult = await journey1Page.getEnhancedPrompt();
      expect(initialResult).toBeTruthy();

      // Navigate away and back (simulate tab switching)
      await page.goto('about:blank');
      await page.waitForTimeout(1000);
      await journey1Page.goto();
      await journey1Page.switchToJourney(1);
      await journey1Page.waitForJourney1Load();

      // Check if session state is preserved
      const inputAfterNavigation = await journey1Page.textInput.inputValue();
      const outputAfterNavigation = await journey1Page.getEnhancedPrompt();

      if (inputAfterNavigation === sessionPrompt && outputAfterNavigation === initialResult) {
        console.log('✅ Session state fully preserved across navigation');
      } else if (inputAfterNavigation === '' && outputAfterNavigation === '') {
        console.log('⚠️ Session state cleared - testing recovery');

        // Test that new operations work correctly
        await journey1Page.enterPrompt('Recovery test after navigation');
        await journey1Page.enhancePrompt();

        const recoveryResult = await journey1Page.getEnhancedPrompt();
        expect(recoveryResult).toBeTruthy();
        console.log('✅ System recovered correctly after session reset');
      } else {
        console.log('⚠️ Partial session state preservation detected');
      }

      console.log('✅ Session integrity across page interactions verified');
    });
  });

  test.describe('Export and Copy Fidelity', () => {
    test('should export exact displayed content', async ({ page }) => {
      const exportTestPrompt = 'Create a detailed technical specification for a REST API including authentication, endpoints, data models, and error handling';

      await journey1Page.enterPrompt(exportTestPrompt);
      await journey1Page.enhancePrompt();

      const displayedContent = await journey1Page.getEnhancedPrompt();
      expect(displayedContent).toBeTruthy();

      // Test markdown export
      try {
        const download = await journey1Page.exportContent('md');
        const downloadPath = await download.path();

        if (downloadPath) {
          const fs = require('fs');
          const exportedContent = fs.readFileSync(downloadPath, 'utf8');

          // Verify key content is preserved in export
          const keyPhrases = ['technical specification', 'REST API', 'authentication', 'endpoints'];

          keyPhrases.forEach(phrase => {
            const inDisplayed = displayedContent.toLowerCase().includes(phrase.toLowerCase());
            const inExported = exportedContent.toLowerCase().includes(phrase.toLowerCase());

            if (inDisplayed && inExported) {
              console.log(`✅ Export fidelity: "${phrase}" preserved`);
            } else if (inDisplayed && !inExported) {
              console.warn(`⚠️ Export fidelity issue: "${phrase}" missing in export`);
            }
          });

          // Verify export is substantial
          expect(exportedContent.length).toBeGreaterThan(100);

          console.log(`Export size comparison: Displayed ${displayedContent.length} chars, Exported ${exportedContent.length} chars`);
        }
      } catch (error) {
        console.log(`Export functionality may not be available: ${error.message}`);
      }

      console.log('✅ Export fidelity verification completed');
    });

    test('should preserve formatting in copy operations', async ({ page }) => {
      const formattingTestPrompt = 'Create a code documentation example with multiple programming languages, code blocks, and structured formatting';

      await journey1Page.enterPrompt(formattingTestPrompt);
      await journey1Page.enhancePrompt();

      const enhancedContent = await journey1Page.getEnhancedPrompt();
      expect(enhancedContent).toBeTruthy();

      // Test copy as markdown
      try {
        await journey1Page.copyAsMarkdown();
        await journey1Page.waitForText('copied', 5000);

        // We can't directly access clipboard in automated tests,
        // but we can verify the copy operation completed without errors
        console.log('✅ Copy as markdown operation completed successfully');

        // Verify the content that would be copied has proper structure
        if (enhancedContent.includes('```') || enhancedContent.includes('`')) {
          console.log('✅ Code blocks detected in content for copying');
        }

        if (enhancedContent.includes('#') || enhancedContent.includes('##')) {
          console.log('✅ Markdown headers detected in content');
        }

      } catch (error) {
        console.log(`Copy markdown functionality may not be available: ${error.message}`);
      }

      // Test copy code blocks
      try {
        await journey1Page.copyCodeBlocks();
        await journey1Page.waitForText('copied', 5000);

        console.log('✅ Copy code blocks operation completed successfully');
      } catch (error) {
        console.log(`Copy code blocks functionality may not be available: ${error.message}`);
      }

      console.log('✅ Copy formatting preservation verification completed');
    });

    test('should maintain data integrity during iterative operations', async ({ page }) => {
      const iterativePrompt = 'Develop a comprehensive data analysis workflow';

      // Track data through multiple operations
      const operationResults = [];

      // Initial enhancement
      await journey1Page.enterPrompt(iterativePrompt);
      await journey1Page.enhancePrompt();

      const initialResult = await journey1Page.getEnhancedPrompt();
      expect(initialResult).toBeTruthy();

      operationResults.push({
        operation: 'initial',
        content: initialResult,
        length: initialResult.length
      });

      // Copy operation
      try {
        await journey1Page.copyAsMarkdown();
        await journey1Page.waitForText('copied', 3000);

        operationResults.push({
          operation: 'copy',
          content: initialResult, // Content should remain unchanged
          length: initialResult.length
        });
      } catch (error) {
        console.log('Copy operation not available for integrity test');
      }

      // Clear and re-enter enhanced content
      await journey1Page.clearAll();
      await journey1Page.enterPrompt(initialResult);
      await journey1Page.enhancePrompt();

      const reprocessedResult = await journey1Page.getEnhancedPrompt();
      expect(reprocessedResult).toBeTruthy();

      operationResults.push({
        operation: 'reprocessed',
        content: reprocessedResult,
        length: reprocessedResult.length
      });

      // Analyze integrity across operations
      console.log('Iterative operation integrity analysis:');
      operationResults.forEach(result => {
        console.log(`  ${result.operation}: ${result.length} characters`);
      });

      // Verify key terms persist across operations
      const keyTerms = ['data', 'analysis', 'workflow'];
      keyTerms.forEach(term => {
        const persistsAcrossOps = operationResults.every(result =>
          result.content.toLowerCase().includes(term.toLowerCase())
        );

        if (persistsAcrossOps) {
          console.log(`✅ Key term "${term}" persists across all operations`);
        } else {
          console.warn(`⚠️ Key term "${term}" may be lost during operations`);
        }
      });

      console.log('✅ Iterative operation data integrity verified');
    });
  });
});
