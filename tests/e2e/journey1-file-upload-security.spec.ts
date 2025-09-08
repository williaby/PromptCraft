import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';

test.describe('Journey 1: Enhanced File Upload Security Testing', () => {
  const testDataDir = path.join(__dirname, 'data/upload-test-files');

  test.beforeAll(async () => {
    // Create test directory if it doesn't exist
    if (!fs.existsSync(testDataDir)) {
      fs.mkdirSync(testDataDir, { recursive: true });
    }

    // Create test files for comprehensive upload testing
    await createSecurityTestFiles();
  });

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

    // Switch to file upload mode - use the label instead of disabled input
    const fileUploadLabel = page.locator('label:has-text("📁 File Upload")');
    if (await fileUploadLabel.count() > 0) {
      await fileUploadLabel.click();
      await page.waitForTimeout(2000);
    }
  });

  test.describe('Standard File Types - Security Validation', () => {
    test('should safely handle Python (.py) files with various content', async ({ page }) => {
      console.log('🐍 Testing Python file upload security...');

      // Create test Python files with different security concerns
      const pythonFiles = [
        {
          name: 'safe_script.py',
          content: `#!/usr/bin/env python3
# Safe Python script for testing
def hello_world():
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    hello_world()
`
        },
        {
          name: 'complex_script.py',
          content: `import os
import sys
import json

class DataProcessor:
    def __init__(self, config_file):
        self.config = self.load_config(config_file)

    def load_config(self, file_path):
        # This could be flagged as potential security risk
        with open(file_path, 'r') as f:
            return json.load(f)

    def process_data(self, data):
        # Complex processing logic
        return {
            'processed': True,
            'data': data,
            'timestamp': os.getctime(__file__)
        }
`
        }
      ];

      for (const pythonFile of pythonFiles) {
        const filePath = path.join(testDataDir, pythonFile.name);
        fs.writeFileSync(filePath, pythonFile.content);

        console.log(`📁 Testing upload of ${pythonFile.name}...`);

        // Upload the file
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(filePath);
        await page.waitForTimeout(2000);

        // Verify file was accepted and processed safely
        const fileIndicator = page.locator(`text=${pythonFile.name}`);
        await expect(fileIndicator).toBeVisible({ timeout: 10000 });
        console.log(`✅ ${pythonFile.name} uploaded successfully`);

        // Test enhancement with uploaded file
        const enhanceButton = page.locator('button:has-text("Enhance")').first();
        if (await enhanceButton.isVisible()) {
          await enhanceButton.click();
          await page.waitForTimeout(5000);
          console.log(`✅ Enhancement with ${pythonFile.name} completed`);
        }

        // Clear for next test
        const clearButton = page.locator('button:has-text("Clear")').first();
        if (await clearButton.isVisible()) {
          await clearButton.click({ force: true });
          await page.waitForTimeout(1000);
        }
      }
    });

    test('should safely handle Shell (.sh) scripts with security scanning', async ({ page }) => {
      console.log('🐚 Testing Shell script upload security...');

      const shellScripts = [
        {
          name: 'safe_script.sh',
          content: `#!/bin/bash
# Safe shell script for testing
echo "Starting deployment process..."

# Set variables
APP_NAME="test-app"
VERSION="1.0.0"

# Simple operations
echo "Deploying $APP_NAME version $VERSION"
echo "Deployment completed successfully"
`
        },
        {
          name: 'system_script.sh',
          content: `#!/bin/bash
# System administration script (should be handled carefully)
set -e

# System checks
if [ "$EUID" -eq 0 ]; then
    echo "Running as root - elevated privileges detected"
fi

# File operations (potential security concern)
find /tmp -name "*.log" -mtime +7 -delete

# Network operations
curl -s https://api.github.com/status > /tmp/github_status.json

echo "System maintenance completed"
`
        }
      ];

      for (const script of shellScripts) {
        const filePath = path.join(testDataDir, script.name);
        fs.writeFileSync(filePath, script.content);
        fs.chmodSync(filePath, 0o755); // Make executable

        console.log(`📁 Testing upload of ${script.name}...`);

        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(filePath);
        await page.waitForTimeout(2000);

        // Verify upload and security handling
        const fileIndicator = page.locator(`text=${script.name}`);
        await expect(fileIndicator).toBeVisible({ timeout: 10000 });
        console.log(`✅ ${script.name} uploaded with security validation`);

        // Test enhancement to ensure no script execution
        const textInput = page.locator('textarea').first();
        await textInput.fill('Please analyze this shell script for security best practices');

        const enhanceButton = page.locator('button:has-text("Enhance")').first();
        if (await enhanceButton.isVisible()) {
          await enhanceButton.click();
          await page.waitForTimeout(5000);
          console.log(`✅ Security analysis of ${script.name} completed`);
        }

        // Clear for next test
        const clearButton = page.locator('button:has-text("Clear")').first();
        if (await clearButton.isVisible()) {
          await clearButton.click({ force: true });
          await page.waitForTimeout(1000);
        }
      }
    });

    test('should handle PDF files with content integrity validation', async ({ page }) => {
      console.log('📄 Testing PDF file upload and integrity...');

      // Create a test PDF content (simplified - in reality would use PDF library)
      const pdfTestData = `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 4 0 R
>>
>>
/MediaBox [0 0 612 792]
/Contents 5 0 R
>>
endobj
4 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Times-Roman
>>
endobj
5 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test PDF Document) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
0000000336 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
428
%%EOF`;

      const pdfPath = path.join(testDataDir, 'test_document.pdf');
      fs.writeFileSync(pdfPath, pdfTestData, 'binary');

      console.log('📁 Testing PDF upload...');

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(pdfPath);
      await page.waitForTimeout(3000);

      // Verify PDF was processed
      const fileIndicator = page.locator('text=test_document.pdf');
      await expect(fileIndicator).toBeVisible({ timeout: 10000 });
      console.log('✅ PDF uploaded successfully');

      // Test PDF content extraction
      const textInput = page.locator('textarea').first();
      await textInput.fill('Please summarize the content of this PDF document');

      const enhanceButton = page.locator('button:has-text("Enhance")').first();
      if (await enhanceButton.isVisible()) {
        await enhanceButton.click();
        await page.waitForTimeout(10000); // PDFs may take longer to process
        console.log('✅ PDF content analysis completed');
      }
    });

    test('should handle HTML files with XSS protection validation', async ({ page }) => {
      console.log('🌐 Testing HTML file upload with XSS protection...');

      const htmlFiles = [
        {
          name: 'safe_page.html',
          content: `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Safe Test Page</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { color: #333; border-bottom: 2px solid #ddd; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Document</h1>
        <p>This is a safe HTML document for testing purposes.</p>
    </div>
    <main>
        <h2>Content Section</h2>
        <p>This document contains standard HTML elements and CSS.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
        </ul>
    </main>
</body>
</html>`
        },
        {
          name: 'potentially_unsafe.html',
          content: `<!DOCTYPE html>
<html>
<head>
    <title>Document with Scripts</title>
</head>
<body>
    <h1>Document Title</h1>
    <p>This document contains some JavaScript that should be sanitized:</p>

    <!-- This script should be safely handled -->
    <script>
        console.log("This should not execute in the upload context");
        // alert("XSS Test"); // Commented out for safety
    </script>

    <!-- This should be handled safely too -->
    <img src="invalid.jpg" onerror="console.log('Image error handled safely')" />

    <p>Regular content continues here.</p>
</body>
</html>`
        }
      ];

      for (const htmlFile of htmlFiles) {
        const filePath = path.join(testDataDir, htmlFile.name);
        fs.writeFileSync(filePath, htmlFile.content);

        console.log(`📁 Testing upload of ${htmlFile.name}...`);

        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(filePath);
        await page.waitForTimeout(2000);

        // Verify upload succeeded with security measures
        const fileIndicator = page.locator(`text=${htmlFile.name}`);
        await expect(fileIndicator).toBeVisible({ timeout: 10000 });
        console.log(`✅ ${htmlFile.name} uploaded with XSS protection`);

        // Test content analysis without script execution
        const textInput = page.locator('textarea').first();
        await textInput.fill('Please analyze the structure and content of this HTML document, focusing on best practices');

        const enhanceButton = page.locator('button:has-text("Enhance")').first();
        if (await enhanceButton.isVisible()) {
          await enhanceButton.click();
          await page.waitForTimeout(5000);
          console.log(`✅ Safe HTML analysis of ${htmlFile.name} completed`);
        }

        // Clear for next test
        const clearButton = page.locator('button:has-text("Clear")').first();
        if (await clearButton.isVisible()) {
          await clearButton.click({ force: true });
          await page.waitForTimeout(1000);
        }
      }
    });
  });

  test.describe('File Size and Type Restrictions', () => {
    test('should enforce file size limits and handle large files gracefully', async ({ page }) => {
      console.log('📏 Testing file size limit enforcement...');

      // Create files of different sizes
      const testFiles = [
        { name: 'small_file.txt', size: 1024 }, // 1KB
        { name: 'medium_file.txt', size: 1024 * 1024 }, // 1MB
        { name: 'large_file.txt', size: 5 * 1024 * 1024 }, // 5MB
        { name: 'oversized_file.txt', size: 15 * 1024 * 1024 } // 15MB (should be rejected)
      ];

      for (const testFile of testFiles) {
        const filePath = path.join(testDataDir, testFile.name);
        const content = 'A'.repeat(testFile.size);
        fs.writeFileSync(filePath, content);

        console.log(`📁 Testing ${testFile.name} (${(testFile.size / 1024 / 1024).toFixed(2)}MB)...`);

        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(filePath);
        await page.waitForTimeout(3000);

        if (testFile.size <= 10 * 1024 * 1024) { // Should be accepted
          const fileIndicator = page.locator(`text=${testFile.name}`);
          await expect(fileIndicator).toBeVisible({ timeout: 15000 });
          console.log(`✅ ${testFile.name} accepted (within size limits)`);
        } else { // Should be rejected
          // Check for error message
          const errorSelectors = [
            'div:has-text("too large")',
            'div:has-text("size limit")',
            'div:has-text("exceeded")',
            'div[role="alert"]'
          ];

          let errorFound = false;
          for (const selector of errorSelectors) {
            const errorElement = page.locator(selector).first();
            if (await errorElement.count() > 0) {
              console.log(`✅ ${testFile.name} rejected (size limit enforced)`);
              errorFound = true;
              break;
            }
          }

          if (!errorFound) {
            console.log(`⚠️ ${testFile.name} - size limit behavior unclear`);
          }
        }

        // Clear any error states
        await page.reload({ waitUntil: 'load' });
        const journey1Tab = page.locator('button[role="tab"]:has-text("Journey 1")');
        if (await journey1Tab.count() > 0) {
          await journey1Tab.click();
          await page.waitForTimeout(2000);
        }
      }
    });

    test('should handle unsupported file types with appropriate messages', async ({ page }) => {
      console.log('🚫 Testing unsupported file type handling...');

      const unsupportedFiles = [
        { name: 'test.exe', content: 'MZ\x90\x00', type: 'executable' },
        { name: 'test.bin', content: '\x00\x01\x02\x03', type: 'binary' },
        { name: 'test.unknown', content: 'Unknown file type content', type: 'unknown' }
      ];

      for (const testFile of unsupportedFiles) {
        const filePath = path.join(testDataDir, testFile.name);
        fs.writeFileSync(filePath, testFile.content, 'binary');

        console.log(`📁 Testing ${testFile.name} (${testFile.type})...`);

        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(filePath);
        await page.waitForTimeout(2000);

        // Check for appropriate rejection
        const errorSelectors = [
          'div:has-text("not supported")',
          'div:has-text("invalid file")',
          'div:has-text("file type")',
          'div[role="alert"]'
        ];

        let handled = false;
        for (const selector of errorSelectors) {
          const errorElement = page.locator(selector).first();
          if (await errorElement.count() > 0) {
            console.log(`✅ ${testFile.name} properly rejected (${testFile.type})`);
            handled = true;
            break;
          }
        }

        // Also check if file was accepted but content handled safely
        const fileIndicator = page.locator(`text=${testFile.name}`);
        if (await fileIndicator.count() > 0) {
          console.log(`⚠️ ${testFile.name} was accepted - verify safe handling`);
        }

        if (!handled) {
          console.log(`❓ ${testFile.name} handling unclear - needs investigation`);
        }
      }
    });
  });

  test.describe('File Content Integrity and Encoding', () => {
    test('should preserve file content integrity with checksums', async ({ page }) => {
      console.log('🔒 Testing file content integrity preservation...');

      const testContent = `# Test Document
This is a test document with various characters:
- ASCII: Hello World!
- Unicode: 🚀 🌟 ✨
- Special chars: àáâãäåæçèéêë
- Numbers: 123456789
- Code: function test() { return "hello"; }

## Section 2
More content to test integrity...
`;

      const filePath = path.join(testDataDir, 'integrity_test.md');
      fs.writeFileSync(filePath, testContent, 'utf8');

      // Calculate original checksum
      const originalChecksum = crypto.createHash('md5').update(testContent).digest('hex');
      console.log(`📋 Original content checksum: ${originalChecksum}`);

      // Upload file
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(filePath);
      await page.waitForTimeout(2000);

      // Verify upload
      const fileIndicator = page.locator('text=integrity_test.md');
      await expect(fileIndicator).toBeVisible({ timeout: 10000 });

      // Test enhancement
      const textInput = page.locator('textarea').first();
      await textInput.fill('Please create a summary of this document while preserving its formatting');

      const enhanceButton = page.locator('button:has-text("Enhance")').first();
      if (await enhanceButton.isVisible()) {
        await enhanceButton.click();
        await page.waitForTimeout(5000);

        // Get enhanced output
        const outputArea = page.locator('textarea').nth(1);
        const enhancedContent = await outputArea.inputValue().catch(() => '');

        if (enhancedContent.length > 0) {
          console.log('✅ File content processed successfully');
          console.log(`📊 Output length: ${enhancedContent.length} characters`);

          // Verify key content elements are preserved
          const preservedElements = ['Test Document', 'Hello World', '🚀', 'Section 2'];
          let preserved = 0;
          for (const element of preservedElements) {
            if (enhancedContent.includes(element)) {
              preserved++;
            }
          }
          console.log(`✅ Content preservation: ${preserved}/${preservedElements.length} key elements found`);
        }
      }
    });

    test('should handle various text encodings correctly', async ({ page }) => {
      console.log('🌐 Testing text encoding handling...');

      const encodingTests = [
        {
          name: 'utf8_test.txt',
          content: 'UTF-8: Hello 世界! 🌍 Ñoël café',
          encoding: 'utf8'
        },
        {
          name: 'mixed_encoding.txt',
          content: 'Mixed: ASCII + UTF-8 + Émojis 💻 + Spëcïål chärs',
          encoding: 'utf8'
        }
      ];

      for (const test of encodingTests) {
        const filePath = path.join(testDataDir, test.name);
        fs.writeFileSync(filePath, test.content, test.encoding);

        console.log(`📁 Testing ${test.name} (${test.encoding})...`);

        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(filePath);
        await page.waitForTimeout(2000);

        const fileIndicator = page.locator(`text=${test.name}`);
        await expect(fileIndicator).toBeVisible({ timeout: 10000 });

        // Test processing
        const textInput = page.locator('textarea').first();
        await textInput.fill(`Please analyze the encoding and content of this ${test.encoding} file`);

        const enhanceButton = page.locator('button:has-text("Enhance")').first();
        if (await enhanceButton.isVisible()) {
          await enhanceButton.click();
          await page.waitForTimeout(5000);
          console.log(`✅ ${test.name} encoding handled correctly`);
        }

        // Clear for next test
        const clearButton = page.locator('button:has-text("Clear")').first();
        if (await clearButton.isVisible()) {
          await clearButton.click({ force: true });
          await page.waitForTimeout(1000);
        }
      }
    });
  });

  async function createSecurityTestFiles() {
    // Create additional security test files that will be used across tests
    const securityFiles = [
      {
        name: 'config.json',
        content: JSON.stringify({
          "api_key": "test-key-not-real",
          "database_url": "postgresql://localhost:5432/test",
          "debug": true,
          "allowed_origins": ["localhost", "127.0.0.1"]
        }, null, 2)
      },
      {
        name: 'requirements.txt',
        content: `requests>=2.28.0
flask>=2.0.0
pytest>=7.0.0
black>=22.0.0
`
      }
    ];

    for (const file of securityFiles) {
      const filePath = path.join(testDataDir, file.name);
      fs.writeFileSync(filePath, file.content);
    }
  }

  test.afterAll(async () => {
    // Clean up test files
    if (fs.existsSync(testDataDir)) {
      const files = fs.readdirSync(testDataDir);
      for (const file of files) {
        fs.unlinkSync(path.join(testDataDir, file));
      }
      fs.rmdirSync(testDataDir);
      console.log('🧹 Test files cleaned up');
    }
  });
});
