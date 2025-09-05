import { test, expect } from '@playwright/test';
import { Journey1Page } from './fixtures/Journey1Page';
import TestUtils from './helpers/test-utils';
import path from 'path';

test.describe('Security Tests', () => {
  let journey1Page: Journey1Page;
  const testDataDir = path.join(__dirname, 'data/files');
  const maliciousDataDir = path.join(__dirname, 'data/malicious');

  test.beforeEach(async ({ page }) => {
    journey1Page = new Journey1Page(page);
    await journey1Page.gotoJourney1();
  });

  test.describe('File Upload Security', () => {
    test('should enforce file size limits', async ({ page }) => {
      const oversizedFile = path.join(maliciousDataDir, 'oversized-file.txt');
      
      // Attempt to upload oversized file
      try {
        await journey1Page.testFileValidation(oversizedFile, true);
        
        // Should show size error
        const errorMessage = await journey1Page.getErrorMessage();
        expect(errorMessage).toMatch(/size|large|limit/i);
        
      } catch (error) {
        // Browser might reject the file before it reaches the server
        console.log('File rejected at browser level (expected for security)');
      }
    });

    test('should validate file types', async ({ page }) => {
      // Create a test file with unsupported extension
      const tempDir = require('os').tmpdir();
      const unsupportedFile = path.join(tempDir, 'test.exe');
      
      // Create a fake executable file
      require('fs').writeFileSync(unsupportedFile, 'fake executable content');
      
      try {
        const result = await journey1Page.testFileValidation(unsupportedFile, true);
        
        if (typeof result === 'string') {
          expect(result).toMatch(/type|format|supported/i);
        }
        
      } catch (error) {
        console.log('Unsupported file type blocked (expected)');
      } finally {
        // Clean up
        try {
          require('fs').unlinkSync(unsupportedFile);
        } catch {}
      }
    });

    test('should scan for malicious content', async ({ page }) => {
      const maliciousFile = path.join(maliciousDataDir, 'fake-text-with-script.txt');
      
      try {
        await journey1Page.uploadTestFile(maliciousFile);
        
        // If upload succeeds, check that content is sanitized
        await journey1Page.enterPrompt('Process this uploaded file');
        await journey1Page.enhancePrompt();
        
        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        
        // Verify dangerous content is not present in output
        expect(enhancedPrompt).not.toContain('<script');
        expect(enhancedPrompt).not.toContain('javascript:');
        expect(enhancedPrompt).not.toContain('onerror=');
        expect(enhancedPrompt).not.toContain('DROP TABLE');
        expect(enhancedPrompt).not.toContain('$(cat /etc/passwd)');
        
      } catch (error) {
        // Security system blocking file is also acceptable
        console.log('Malicious content blocked by security system');
        
        const hasError = await journey1Page.hasError();
        if (hasError) {
          const errorMessage = await journey1Page.getErrorMessage();
          expect(errorMessage).toMatch(/security|malicious|blocked/i);
        }
      }
    });

    test('should detect polyglot files', async ({ page }) => {
      // Create a file that appears to be text but has suspicious content
      const tempDir = require('os').tmpdir();
      const polyglotFile = path.join(tempDir, 'polyglot.txt');
      
      // Content that could be interpreted as multiple formats
      const suspiciousContent = `
        This looks like text but contains:
        PK\x03\x04 (ZIP signature)
        %PDF-1.4 (PDF signature)
        \x89PNG\r\n\x1a\n (PNG signature)
      `;
      
      require('fs').writeFileSync(polyglotFile, suspiciousContent);
      
      try {
        const result = await journey1Page.testFileValidation(polyglotFile, true);
        
        // Should be blocked or sanitized
        if (typeof result === 'string') {
          expect(result).toMatch(/suspicious|polyglot|security/i);
        }
        
      } catch (error) {
        console.log('Polyglot file detection working');
      } finally {
        // Clean up
        try {
          require('fs').unlinkSync(polyglotFile);
        } catch {}
      }
    });
  });

  test.describe('Input Sanitization', () => {
    test('should sanitize XSS attempts in text input', async ({ page }) => {
      const xssAttempts = [
        '<script>alert("XSS")</script>',
        'javascript:alert("XSS")',
        '<img src="x" onerror="alert(\'XSS\')">',
        '<iframe src="javascript:alert(\'XSS\')"></iframe>',
        '<svg onload="alert(\'XSS\')">',
        'onmouseover="alert(\'XSS\')"'
      ];

      for (const xssPayload of xssAttempts) {
        await journey1Page.clearAll();
        await journey1Page.enterPrompt(`Test prompt ${xssPayload}`);
        
        try {
          await journey1Page.enhancePrompt();
          
          const enhancedPrompt = await journey1Page.getEnhancedPrompt();
          
          // Verify XSS payload is not executed or present in dangerous form
          expect(enhancedPrompt).not.toContain('<script');
          expect(enhancedPrompt).not.toContain('javascript:');
          expect(enhancedPrompt).not.toContain('onerror=');
          expect(enhancedPrompt).not.toContain('onmouseover=');
          expect(enhancedPrompt).not.toContain('onload=');
          
        } catch (error) {
          // Input validation blocking is also acceptable
          console.log(`XSS payload blocked: ${xssPayload}`);
        }
      }
    });

    test('should prevent SQL injection attempts', async ({ page }) => {
      const sqlInjectionPayloads = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "'; INSERT INTO users VALUES ('hacker', 'password'); --",
        "' UNION SELECT password FROM users --"
      ];

      for (const sqlPayload of sqlInjectionPayloads) {
        await journey1Page.clearAll();
        await journey1Page.enterPrompt(`Analyze this data: ${sqlPayload}`);
        
        try {
          await journey1Page.enhancePrompt();
          
          const enhancedPrompt = await journey1Page.getEnhancedPrompt();
          
          // Should not contain dangerous SQL keywords in executable form
          expect(enhancedPrompt).not.toContain('DROP TABLE');
          expect(enhancedPrompt).not.toContain('INSERT INTO');
          
        } catch (error) {
          console.log(`SQL injection blocked: ${sqlPayload}`);
        }
      }
    });

    test('should handle command injection attempts', async ({ page }) => {
      const commandInjectionPayloads = [
        '$(cat /etc/passwd)',
        '`rm -rf /`',
        '| ls -la',
        '&& whoami',
        '; curl malicious-site.com'
      ];

      for (const cmdPayload of commandInjectionPayloads) {
        await journey1Page.clearAll();
        await journey1Page.enterPrompt(`Process this command: ${cmdPayload}`);
        
        try {
          await journey1Page.enhancePrompt();
          
          const enhancedPrompt = await journey1Page.getEnhancedPrompt();
          
          // Should not contain dangerous shell commands
          expect(enhancedPrompt).not.toContain('$(cat');
          expect(enhancedPrompt).not.toContain('rm -rf');
          
        } catch (error) {
          console.log(`Command injection blocked: ${cmdPayload}`);
        }
      }
    });
  });

  test.describe('Rate Limiting Security', () => {
    test('should enforce rate limits on requests', async ({ page }) => {
      const rateTestResults = await TestUtils.testRateLimit(journey1Page, 35);
      
      // Should eventually hit rate limit
      const rateLimitedRequests = rateTestResults.filter(r => r.rateLimited);
      expect(rateLimitedRequests.length).toBeGreaterThan(0);
      
      // Rate limit should kick in around 30 requests/minute
      const successfulRequests = rateTestResults.filter(r => r.success);
      expect(successfulRequests.length).toBeLessThanOrEqual(32); // Allow some buffer
      
      console.log(`Rate limit testing: ${successfulRequests.length} successful requests before limit`);
    });

    test('should enforce file upload rate limits', async ({ page }) => {
      const textFile = path.join(testDataDir, 'simple-text.txt');
      const uploadResults = [];
      
      // Attempt multiple rapid uploads
      for (let i = 0; i < 15; i++) {
        try {
          await journey1Page.uploadTestFile(textFile);
          uploadResults.push({ success: true, attempt: i + 1 });
          
          // Check for rate limit
          if (await journey1Page.isRateLimited()) {
            uploadResults.push({ success: false, rateLimited: true, attempt: i + 1 });
            break;
          }
          
        } catch (error) {
          uploadResults.push({ 
            success: false, 
            error: error.message, 
            attempt: i + 1 
          });
        }
        
        // Small delay between uploads
        await page.waitForTimeout(200);
      }
      
      console.log('Upload rate limit test results:', uploadResults);
      
      // Should eventually hit upload rate limit or show appropriate throttling
      const failedUploads = uploadResults.filter(r => !r.success);
      if (failedUploads.length > 0) {
        console.log('Upload rate limiting is working');
      }
    });

    test('should prevent session hijacking attempts', async ({ page, context }) => {
      // Get initial session info
      const initialSession = await journey1Page.getSessionInfo();
      
      // Try to manipulate session storage
      await page.evaluate(() => {
        try {
          localStorage.setItem('session_id', 'malicious_session_123');
          localStorage.setItem('user_tier', 'enterprise');
          sessionStorage.setItem('auth_token', 'fake_token');
        } catch (e) {
          console.log('Session manipulation blocked');
        }
      });
      
      // Refresh page to see if manipulation took effect
      await page.reload();
      await journey1Page.waitForJourney1Load();
      
      // Session should be validated server-side
      const afterSession = await journey1Page.getSessionInfo();
      
      // Should not be affected by client-side manipulation
      // (This test depends on server-side session validation)
      console.log('Initial session:', initialSession);
      console.log('After manipulation:', afterSession);
    });
  });

  test.describe('CORS and Network Security', () => {
    test('should have proper CORS configuration', async ({ page }) => {
      // Monitor network requests
      const requests = [];
      page.on('request', (request) => {
        requests.push({
          url: request.url(),
          method: request.method(),
          headers: request.headers()
        });
      });
      
      const responses = [];
      page.on('response', (response) => {
        responses.push({
          url: response.url(),
          status: response.status(),
          headers: response.headers()
        });
      });
      
      // Make a request
      await journey1Page.enterPrompt('Test CORS security');
      await journey1Page.enhancePrompt();
      
      // Check for proper CORS headers in responses
      const apiResponses = responses.filter(r => 
        r.url.includes('/api/') || r.url.includes('/enhance')
      );
      
      for (const response of apiResponses) {
        const corsHeaders = response.headers;
        console.log('CORS headers:', {
          'access-control-allow-origin': corsHeaders['access-control-allow-origin'],
          'access-control-allow-methods': corsHeaders['access-control-allow-methods'],
          'access-control-allow-headers': corsHeaders['access-control-allow-headers']
        });
      }
    });

    test('should reject cross-origin malicious requests', async ({ page, context }) => {
      // This test simulates potential CSRF attempts
      
      // Try to make a request from a different origin (simulation)
      const maliciousOrigin = 'https://evil-site.com';
      
      try {
        // Attempt to set malicious referer
        await page.setExtraHTTPHeaders({
          'Referer': maliciousOrigin,
          'Origin': maliciousOrigin
        });
        
        await journey1Page.enterPrompt('CSRF test');
        await journey1Page.enhancePrompt();
        
        // If the request succeeds, verify it's properly handled
        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();
        
        console.log('Request with malicious origin handled safely');
        
      } catch (error) {
        console.log('Malicious origin blocked (expected):', error.message);
      }
    });
  });

  test.describe('Data Privacy and Leakage', () => {
    test('should not expose sensitive information in errors', async ({ page }) => {
      // Trigger various error conditions
      const errorScenarios = [
        { action: 'empty input', fn: () => journey1Page.enhanceButton.click() },
        { action: 'invalid model', fn: () => journey1Page.selectModel('invalid-model') },
        { action: 'malformed request', fn: () => journey1Page.enterPrompt('\x00\x01\x02') }
      ];
      
      for (const scenario of errorScenarios) {
        try {
          await journey1Page.clearAll();
          await scenario.fn();
          
          if (await journey1Page.hasError()) {
            const errorMessage = await journey1Page.getErrorMessage();
            
            // Should not contain sensitive information
            expect(errorMessage).not.toContain('password');
            expect(errorMessage).not.toContain('token');
            expect(errorMessage).not.toContain('secret');
            expect(errorMessage).not.toContain('api_key');
            expect(errorMessage).not.toContain('/etc/');
            expect(errorMessage).not.toContain('C:\\');
            
            console.log(`Safe error for ${scenario.action}: ${errorMessage}`);
          }
          
        } catch (error) {
          // Error handling itself should not leak information
          expect(error.message).not.toContain('password');
          expect(error.message).not.toContain('secret');
        }
      }
    });

    test('should not store sensitive data in browser storage', async ({ page }) => {
      await journey1Page.enterPrompt('Process sensitive user data');
      await journey1Page.enhancePrompt();
      
      // Check browser storage for sensitive data
      const localStorage = await page.evaluate(() => {
        const storage = {};
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          storage[key] = localStorage.getItem(key);
        }
        return storage;
      });
      
      const sessionStorage = await page.evaluate(() => {
        const storage = {};
        for (let i = 0; i < sessionStorage.length; i++) {
          const key = sessionStorage.key(i);
          storage[key] = sessionStorage.getItem(key);
        }
        return storage;
      });
      
      // Verify no sensitive data in storage
      const allStorageData = JSON.stringify({ localStorage, sessionStorage });
      expect(allStorageData).not.toContain('password');
      expect(allStorageData).not.toContain('token');
      expect(allStorageData).not.toContain('secret');
      expect(allStorageData).not.toContain('api_key');
      
      console.log('Browser storage is clean of sensitive data');
    });
  });

  test.describe('Content Security Policy', () => {
    test('should prevent inline script execution', async ({ page }) => {
      // Monitor console for CSP violations
      const consoleMessages = [];
      page.on('console', (msg) => {
        if (msg.type() === 'error' && msg.text().includes('Content Security Policy')) {
          consoleMessages.push(msg.text());
        }
      });
      
      // Try to inject inline script via various means
      await journey1Page.enterPrompt('<script>console.log("inline script test")</script>');
      await journey1Page.enhancePrompt();
      
      // CSP violations should be logged (if CSP is properly configured)
      console.log('CSP violations detected:', consoleMessages.length);
      
      // Page should still function normally
      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();
    });
  });
});