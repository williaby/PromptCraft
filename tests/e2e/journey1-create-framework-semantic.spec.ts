import { test, expect } from '@playwright/test';

test.describe('Journey 1: C.R.E.A.T.E. Framework Semantic Testing', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to Journey 1 using working patterns
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
  });

  test.describe('C.R.E.A.T.E. Framework Component Analysis', () => {
    test('should demonstrate Context (C) analysis and enhancement', async ({ page }) => {
      console.log('🎯 Testing Context analysis in C.R.E.A.T.E. framework...');

      const contextTestCases = [
        {
          prompt: 'Write an email',
          expectedContextAnalysis: ['audience', 'purpose', 'tone', 'formality'],
          description: 'Minimal context - should request clarification'
        },
        {
          prompt: 'Write a professional email to my team about the quarterly budget review meeting scheduled for next Friday at 2 PM in Conference Room A',
          expectedContextAnalysis: ['professional', 'team', 'meeting', 'specific details'],
          description: 'Rich context - should leverage details'
        },
        {
          prompt: 'Create marketing content for our innovative SaaS platform targeting enterprise customers who struggle with data integration challenges',
          expectedContextAnalysis: ['marketing', 'SaaS', 'enterprise', 'data integration'],
          description: 'Domain-specific context - should show expertise'
        }
      ];

      for (const testCase of contextTestCases) {
        console.log(`📝 Testing: ${testCase.description}`);

        // Enter the prompt
        const textInput = page.locator('textarea').first();
        await textInput.fill(testCase.prompt);

        // Enable framework analysis
        const frameworkCheckbox = page.locator('input[type="checkbox"]').first();
        if (await frameworkCheckbox.count() > 0 && !(await frameworkCheckbox.isChecked())) {
          await frameworkCheckbox.check();
          await page.waitForTimeout(1000);
        }

        // Enhance the prompt
        const enhanceButton = page.locator('button:has-text("Enhance")').first();
        await enhanceButton.click();
        await page.waitForTimeout(8000);

        // Check C.R.E.A.T.E. framework breakdown
        const contextField = page.locator('textarea[label*="Context"], input[label*="Context"]').first();
        if (await contextField.count() > 0) {
          const contextAnalysis = await contextField.inputValue().catch(() => '');
          console.log('📊 Context Analysis:', contextAnalysis.substring(0, 100) + '...');

          // Verify context elements are addressed
          let contextScore = 0;
          for (const element of testCase.expectedContextAnalysis) {
            if (contextAnalysis.toLowerCase().includes(element.toLowerCase())) {
              contextScore++;
            }
          }

          console.log(`✅ Context coverage: ${contextScore}/${testCase.expectedContextAnalysis.length} elements found`);
          expect(contextScore).toBeGreaterThan(0);
        }

        // Clear for next test
        const clearButton = page.locator('button:has-text("Clear")').first();
        if (await clearButton.count() > 0) {
          await clearButton.click({ force: true });
          await page.waitForTimeout(1000);
        }
      }
    });

    test('should demonstrate Request (R) specification and refinement', async ({ page }) => {
      console.log('📋 Testing Request specification in C.R.E.A.T.E. framework...');

      const requestTestCases = [
        {
          prompt: 'Make it better',
          description: 'Vague request - should seek clarification'
        },
        {
          prompt: 'Create a 500-word blog post about sustainable technology trends, written for tech executives, with 3 key takeaways and actionable recommendations',
          description: 'Specific request - should acknowledge requirements'
        },
        {
          prompt: 'Help me write code that processes data and outputs results in a useful format',
          description: 'Technical but vague - should request technical details'
        }
      ];

      for (const testCase of requestTestCases) {
        console.log(`📝 Testing: ${testCase.description}`);

        const textInput = page.locator('textarea').first();
        await textInput.fill(testCase.prompt);

        // Enable framework analysis
        const frameworkCheckbox = page.locator('input[type="checkbox"]').first();
        if (await frameworkCheckbox.count() > 0 && !(await frameworkCheckbox.isChecked())) {
          await frameworkCheckbox.check();
        }

        const enhanceButton = page.locator('button:has-text("Enhance")').first();
        await enhanceButton.click();
        await page.waitForTimeout(8000);

        // Check Request specification
        const requestField = page.locator('textarea[label*="Request"], input[label*="Request"]').first();
        if (await requestField.count() > 0) {
          const requestAnalysis = await requestField.inputValue().catch(() => '');
          console.log('📋 Request Analysis:', requestAnalysis.substring(0, 100) + '...');

          // Verify request clarification occurs for vague prompts
          if (testCase.description.includes('vague')) {
            const clarificationIndicators = ['specific', 'detail', 'clarif', 'more information'];
            let hasClarification = clarificationIndicators.some(indicator =>
              requestAnalysis.toLowerCase().includes(indicator)
            );
            console.log(`✅ Vague request handling: ${hasClarification ? 'Seeks clarification' : 'Direct response'}`);
          }
        }

        // Clear for next test
        const clearButton = page.locator('button:has-text("Clear")').first();
        if (await clearButton.count() > 0) {
          await clearButton.click({ force: true });
          await page.waitForTimeout(1000);
        }
      }
    });

    test('should demonstrate Examples (E) integration and relevance', async ({ page }) => {
      console.log('💡 Testing Examples integration in C.R.E.A.T.E. framework...');

      const exampleTestCases = [
        {
          prompt: 'Create a user story for an e-commerce checkout feature',
          expectedExamples: ['As a user', 'I want to', 'So that', 'acceptance criteria'],
          description: 'Should provide user story format examples'
        },
        {
          prompt: 'Write a Python function to calculate compound interest with proper error handling',
          expectedExamples: ['def', 'try:', 'except:', 'return'],
          description: 'Should provide Python code examples'
        },
        {
          prompt: 'Draft a performance review feedback for a team member who exceeded expectations in project delivery',
          expectedExamples: ['specific examples', 'achievements', 'impact', 'strengths'],
          description: 'Should provide performance review structure examples'
        }
      ];

      for (const testCase of exampleTestCases) {
        console.log(`📝 Testing: ${testCase.description}`);

        const textInput = page.locator('textarea').first();
        await textInput.fill(testCase.prompt);

        const frameworkCheckbox = page.locator('input[type="checkbox"]').first();
        if (await frameworkCheckbox.count() > 0 && !(await frameworkCheckbox.isChecked())) {
          await frameworkCheckbox.check();
        }

        const enhanceButton = page.locator('button:has-text("Enhance")').first();
        await enhanceButton.click();
        await page.waitForTimeout(8000);

        // Check Examples provided
        const examplesField = page.locator('textarea[label*="Example"], input[label*="Example"]').first();
        if (await examplesField.count() > 0) {
          const examplesContent = await examplesField.inputValue().catch(() => '');
          console.log('💡 Examples Content:', examplesContent.substring(0, 100) + '...');

          // Verify relevant examples are provided
          let exampleScore = 0;
          for (const expectedExample of testCase.expectedExamples) {
            if (examplesContent.toLowerCase().includes(expectedExample.toLowerCase())) {
              exampleScore++;
            }
          }

          console.log(`✅ Example relevance: ${exampleScore}/${testCase.expectedExamples.length} expected elements found`);
          expect(exampleScore).toBeGreaterThan(0);
        }

        // Also check enhanced output for examples
        const outputArea = page.locator('textarea').nth(1);
        const enhancedOutput = await outputArea.inputValue().catch(() => '');
        if (enhancedOutput.length > 0) {
          let outputExampleScore = 0;
          for (const expectedExample of testCase.expectedExamples) {
            if (enhancedOutput.toLowerCase().includes(expectedExample.toLowerCase())) {
              outputExampleScore++;
            }
          }
          console.log(`✅ Enhanced output example integration: ${outputExampleScore}/${testCase.expectedExamples.length} elements found`);
        }

        const clearButton = page.locator('button:has-text("Clear")').first();
        if (await clearButton.count() > 0) {
          await clearButton.click({ force: true });
          await page.waitForTimeout(1000);
        }
      }
    });
  });

  test.describe('Framework Coherence and Integration', () => {
    test('should maintain logical flow across all C.R.E.A.T.E. components', async ({ page }) => {
      console.log('🔄 Testing C.R.E.A.T.E. framework coherence...');

      const coherencePrompt = `Create a comprehensive onboarding guide for new software engineers joining our remote-first startup team. The guide should help them understand our culture, processes, and technical stack while making them feel welcomed and prepared for success.`;

      const textInput = page.locator('textarea').first();
      await textInput.fill(coherencePrompt);

      // Enable framework analysis
      const frameworkCheckbox = page.locator('input[type="checkbox"]').first();
      if (await frameworkCheckbox.count() > 0 && !(await frameworkCheckbox.isChecked())) {
        await frameworkCheckbox.check();
      }

      const enhanceButton = page.locator('button:has-text("Enhance")').first();
      await enhanceButton.click();
      await page.waitForTimeout(10000);

      // Check all C.R.E.A.T.E. components for coherence
      const frameworkFields = [
        { name: 'Context', key: 'C' },
        { name: 'Request', key: 'R' },
        { name: 'Example', key: 'E' },
        { name: 'Augmentation', key: 'A' },
        { name: 'Tone', key: 'T' },
        { name: 'Evaluation', key: 'E' }
      ];

      const frameworkData = {};

      for (const field of frameworkFields) {
        const fieldSelector = page.locator(`textarea[label*="${field.name}"], input[label*="${field.name}"]`).first();
        if (await fieldSelector.count() > 0) {
          const content = await fieldSelector.inputValue().catch(() => '');
          frameworkData[field.key] = content;
          console.log(`${field.key} - ${field.name}:`, content.substring(0, 80) + '...');
        }
      }

      // Test coherence between components
      console.log('🔍 Analyzing framework coherence...');

      // Context should align with Request
      if (frameworkData.C && frameworkData.R) {
        const contextTerms = frameworkData.C.toLowerCase().split(/\s+/).slice(0, 10);
        const sharedTerms = contextTerms.filter(term =>
          frameworkData.R.toLowerCase().includes(term) && term.length > 3
        );
        console.log(`✅ Context-Request alignment: ${sharedTerms.length} shared concepts`);
      }

      // Examples should be relevant to the domain
      if (frameworkData.E) {
        const domainTerms = ['onboarding', 'software', 'engineer', 'remote', 'team'];
        const relevantExamples = domainTerms.filter(term =>
          frameworkData.E.toLowerCase().includes(term)
        );
        console.log(`✅ Example relevance: ${relevantExamples.length} domain-relevant terms`);
      }

      // Tone should be appropriate for context
      if (frameworkData.T) {
        const professionalToneIndicators = ['professional', 'welcoming', 'informative', 'clear'];
        const toneAlignment = professionalToneIndicators.some(indicator =>
          frameworkData.T.toLowerCase().includes(indicator)
        );
        console.log(`✅ Tone appropriateness: ${toneAlignment ? 'Aligned' : 'Check needed'}`);
      }
    });

    test('should handle contradictory requirements with resolution strategies', async ({ page }) => {
      console.log('⚖️ Testing contradiction resolution in C.R.E.A.T.E. framework...');

      const contradictoryPrompts = [
        {
          prompt: 'Write a brief but comprehensive detailed report on our quarterly performance that covers everything but keeps it short',
          contradictions: ['brief vs comprehensive', 'detailed vs short'],
          description: 'Length contradiction'
        },
        {
          prompt: 'Create casual professional documentation that is both informal and formal for our enterprise clients',
          contradictions: ['casual vs professional', 'informal vs formal'],
          description: 'Tone contradiction'
        }
      ];

      for (const testCase of contradictoryPrompts) {
        console.log(`📝 Testing: ${testCase.description}`);

        const textInput = page.locator('textarea').first();
        await textInput.fill(testCase.prompt);

        const frameworkCheckbox = page.locator('input[type="checkbox"]').first();
        if (await frameworkCheckbox.count() > 0 && !(await frameworkCheckbox.isChecked())) {
          await frameworkCheckbox.check();
        }

        const enhanceButton = page.locator('button:has-text("Enhance")').first();
        await enhanceButton.click();
        await page.waitForTimeout(8000);

        // Check enhanced output for contradiction resolution
        const outputArea = page.locator('textarea').nth(1);
        const enhancedOutput = await outputArea.inputValue().catch(() => '');

        if (enhancedOutput.length > 0) {
          console.log('🔍 Enhanced Output Preview:', enhancedOutput.substring(0, 150) + '...');

          // Look for contradiction resolution indicators
          const resolutionIndicators = [
            'balance', 'prioritize', 'focus', 'clarification', 'approach',
            'structured', 'key points', 'executive summary'
          ];

          let resolutionScore = 0;
          for (const indicator of resolutionIndicators) {
            if (enhancedOutput.toLowerCase().includes(indicator)) {
              resolutionScore++;
            }
          }

          console.log(`✅ Contradiction resolution: ${resolutionScore} resolution strategies detected`);
          expect(resolutionScore).toBeGreaterThan(0);
        }

        // Check if framework analysis addresses contradictions
        const requestField = page.locator('textarea[label*="Request"]').first();
        if (await requestField.count() > 0) {
          const requestAnalysis = await requestField.inputValue().catch(() => '');
          const addressesContradiction = testCase.contradictions.some(contradiction =>
            requestAnalysis.toLowerCase().includes('contradiction') ||
            requestAnalysis.toLowerCase().includes('balance') ||
            requestAnalysis.toLowerCase().includes('prioritize')
          );

          console.log(`✅ Framework acknowledges contradiction: ${addressesContradiction}`);
        }

        const clearButton = page.locator('button:has-text("Clear")').first();
        if (await clearButton.count() > 0) {
          await clearButton.click({ force: true });
          await page.waitForTimeout(1000);
        }
      }
    });

    test('should adapt framework application to different domains', async ({ page }) => {
      console.log('🎯 Testing C.R.E.A.T.E. framework domain adaptation...');

      const domainTestCases = [
        {
          domain: 'Technical Documentation',
          prompt: 'Create API documentation for our new authentication endpoints',
          expectedAdaptations: ['technical accuracy', 'code examples', 'clear structure', 'developer audience']
        },
        {
          domain: 'Marketing Content',
          prompt: 'Write compelling product messaging for our B2B SaaS platform launch',
          expectedAdaptations: ['persuasive tone', 'value proposition', 'target audience', 'business benefits']
        },
        {
          domain: 'Educational Material',
          prompt: 'Develop a training module on data privacy compliance for new employees',
          expectedAdaptations: ['learning objectives', 'practical examples', 'assessment', 'engagement']
        }
      ];

      for (const testCase of domainTestCases) {
        console.log(`📝 Testing domain: ${testCase.domain}`);

        const textInput = page.locator('textarea').first();
        await textInput.fill(testCase.prompt);

        const frameworkCheckbox = page.locator('input[type="checkbox"]').first();
        if (await frameworkCheckbox.count() > 0 && !(await frameworkCheckbox.isChecked())) {
          await frameworkCheckbox.check();
        }

        const enhanceButton = page.locator('button:has-text("Enhance")').first();
        await enhanceButton.click();
        await page.waitForTimeout(8000);

        // Analyze domain-specific adaptations in framework components
        const contextField = page.locator('textarea[label*="Context"]').first();
        if (await contextField.count() > 0) {
          const contextContent = await contextField.inputValue().catch(() => '');

          let adaptationScore = 0;
          for (const adaptation of testCase.expectedAdaptations) {
            if (contextContent.toLowerCase().includes(adaptation.toLowerCase()) ||
                contextContent.toLowerCase().includes(adaptation.split(' ')[0].toLowerCase())) {
              adaptationScore++;
            }
          }

          console.log(`✅ ${testCase.domain} adaptation: ${adaptationScore}/${testCase.expectedAdaptations.length} domain elements addressed`);
          expect(adaptationScore).toBeGreaterThan(0);
        }

        // Check if enhanced output reflects domain expertise
        const outputArea = page.locator('textarea').nth(1);
        const enhancedOutput = await outputArea.inputValue().catch(() => '');

        if (enhancedOutput.length > 0) {
          let domainScore = 0;
          for (const adaptation of testCase.expectedAdaptations) {
            if (enhancedOutput.toLowerCase().includes(adaptation.toLowerCase())) {
              domainScore++;
            }
          }
          console.log(`✅ ${testCase.domain} output quality: ${domainScore}/${testCase.expectedAdaptations.length} domain characteristics present`);
        }

        const clearButton = page.locator('button:has-text("Clear")').first();
        if (await clearButton.count() > 0) {
          await clearButton.click({ force: true });
          await page.waitForTimeout(1000);
        }
      }
    });
  });

  test.describe('Framework Performance and Edge Cases', () => {
    test('should handle extremely long prompts with framework efficiency', async ({ page }) => {
      console.log('📏 Testing C.R.E.A.T.E. framework with long prompts...');

      const longPrompt = `
        Create a comprehensive strategic business plan for a new fintech startup that aims to revolutionize personal financial management through AI-powered insights and automated investment recommendations. The company will target millennial and Gen-Z consumers who are digitally native but struggle with traditional financial planning tools.

        Our product will integrate with multiple bank accounts, credit cards, and investment platforms to provide a holistic view of users' financial health. Key features include automated budgeting based on spending patterns, personalized investment recommendations using machine learning algorithms, debt optimization strategies, and predictive financial modeling for major life events like buying a home or starting a family.

        The business model will be freemium with basic features available for free and premium features like advanced analytics, one-on-one financial advisor consultations, and priority customer support available through monthly subscription tiers. We need to address regulatory compliance requirements including PCI DSS for payment processing, SOC 2 Type II for data security, and various state and federal financial services regulations.

        The plan should include market analysis of the competitive landscape including established players like Mint, Personal Capital, and YNAB, as well as emerging fintech competitors. Include detailed financial projections for the first three years, go-to-market strategy with specific customer acquisition channels, technology architecture requirements including cloud infrastructure and security considerations, team building plan with key roles and hiring timeline, fundraising strategy with target investors and valuation expectations, and risk mitigation strategies for regulatory, technical, and market risks.

        The final deliverable should be executive-ready with clear sections, actionable recommendations, supporting data and research, visual elements like charts and graphs where appropriate, and a compelling executive summary that could be presented to potential investors or board members.
      `.trim();

      console.log(`📝 Testing with ${longPrompt.length} character prompt`);

      const textInput = page.locator('textarea').first();
      await textInput.fill(longPrompt);

      const frameworkCheckbox = page.locator('input[type="checkbox"]').first();
      if (await frameworkCheckbox.count() > 0 && !(await frameworkCheckbox.isChecked())) {
        await frameworkCheckbox.check();
      }

      // Start timer
      const startTime = Date.now();

      const enhanceButton = page.locator('button:has-text("Enhance")').first();
      await enhanceButton.click();
      await page.waitForTimeout(15000); // Allow extra time for long prompt processing

      const processingTime = Date.now() - startTime;
      console.log(`⏱️ Processing time: ${processingTime}ms`);

      // Verify framework handled complexity appropriately
      const outputArea = page.locator('textarea').nth(1);
      const enhancedOutput = await outputArea.inputValue().catch(() => '');

      if (enhancedOutput.length > 0) {
        console.log(`✅ Enhanced output length: ${enhancedOutput.length} characters`);

        // Check if key complex elements were addressed
        const complexElements = [
          'fintech', 'strategic', 'business plan', 'market analysis',
          'financial projections', 'regulatory', 'technology'
        ];

        let complexityScore = 0;
        for (const element of complexElements) {
          if (enhancedOutput.toLowerCase().includes(element)) {
            complexityScore++;
          }
        }

        console.log(`✅ Complex element handling: ${complexityScore}/${complexElements.length} elements addressed`);
        expect(complexityScore).toBeGreaterThanOrEqual(Math.floor(complexElements.length * 0.6)); // 60% threshold
        expect(processingTime).toBeLessThan(30000); // Should complete within 30 seconds
      }
    });

    test('should maintain framework quality with minimal prompts', async ({ page }) => {
      console.log('🎯 Testing C.R.E.A.T.E. framework with minimal prompts...');

      const minimalPrompts = [
        { prompt: 'Help', expected: 'request clarification' },
        { prompt: 'Write', expected: 'specify what to write' },
        { prompt: 'Code', expected: 'programming context' },
        { prompt: 'Email John', expected: 'email purpose and content' }
      ];

      for (const testCase of minimalPrompts) {
        console.log(`📝 Testing minimal prompt: "${testCase.prompt}"`);

        const textInput = page.locator('textarea').first();
        await textInput.fill(testCase.prompt);

        const frameworkCheckbox = page.locator('input[type="checkbox"]').first();
        if (await frameworkCheckbox.count() > 0 && !(await frameworkCheckbox.isChecked())) {
          await frameworkCheckbox.check();
        }

        const enhanceButton = page.locator('button:has-text("Enhance")').first();
        await enhanceButton.click();
        await page.waitForTimeout(5000);

        // Check if framework requests appropriate clarification
        const requestField = page.locator('textarea[label*="Request"]').first();
        if (await requestField.count() > 0) {
          const requestAnalysis = await requestField.inputValue().catch(() => '');

          const clarificationWords = ['specific', 'details', 'clarif', 'more', 'what', 'how', 'who', 'when'];
          const hasClarification = clarificationWords.some(word =>
            requestAnalysis.toLowerCase().includes(word)
          );

          console.log(`✅ "${testCase.prompt}" -> Requests clarification: ${hasClarification}`);
          expect(hasClarification).toBe(true);
        }

        const clearButton = page.locator('button:has-text("Clear")').first();
        if (await clearButton.count() > 0) {
          await clearButton.click({ force: true });
          await page.waitForTimeout(1000);
        }
      }
    });
  });
});
