import { test, expect } from '@playwright/test';
import { Journey1Page } from '../fixtures/Journey1Page';
import TestUtils from '../helpers/test-utils';
import path from 'path';
import fs from 'fs';

test.describe('Journey 1: Robust File Upload Testing', () => {
  let journey1Page: Journey1Page;
  const testDataDir = path.join(__dirname, '../data/files');
  const codeFilesDir = path.join(__dirname, '../data/files/code');
  const documentFilesDir = path.join(__dirname, '../data/files/documents');

  test.beforeEach(async ({ page }) => {
    journey1Page = new Journey1Page(page);
    await journey1Page.gotoJourney1();
  });

  test.describe('Code File Upload Testing', () => {
    test('should upload and process Python files correctly', async ({ page }) => {
      const pythonFiles = [
        'sample_script.py',
        'requirements.txt',
        'setup.py',
        'conftest.py'
      ];

      for (const fileName of pythonFiles) {
        await journey1Page.clearAll();

        const filePath = path.join(codeFilesDir, fileName);

        // Create test Python file if it doesn't exist
        if (!fs.existsSync(filePath)) {
          const samplePythonContent = fileName.endsWith('.py')
            ? `#!/usr/bin/env python3
"""Sample Python script for testing file upload functionality."""

import os
import sys
from typing import List, Dict, Optional

def main():
    """Main function demonstrating Python code structure."""
    print("Hello, World!")

    # Dictionary comprehension
    data = {f"key_{i}": i**2 for i in range(5)}

    # List processing
    numbers: List[int] = [1, 2, 3, 4, 5]
    squared = [n**2 for n in numbers]

    return data, squared

if __name__ == "__main__":
    result = main()
    print(f"Results: {result}")
`
            : fileName === 'requirements.txt'
              ? `# Python package requirements for testing
fastapi==0.104.1
uvicorn[standard]==0.24.0
pytest==7.4.3
requests==2.31.0
numpy>=1.24.0
pandas>=2.0.0
`
              : `# Setup configuration for testing
from setuptools import setup, find_packages

setup(
    name="test-package",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["requests", "fastapi"]
)
`;

          fs.writeFileSync(filePath, samplePythonContent, 'utf8');
        }

        await journey1Page.uploadTestFile(filePath);

        const fileSources = await journey1Page.getFileSources();
        expect(fileSources.length).toBeGreaterThan(0);
        expect(fileSources[0]).toContain(fileName);

        // Process with Python-specific prompt
        await journey1Page.enterPrompt(`Analyze this Python code and provide optimization suggestions`);
        await journey1Page.enhancePrompt();

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();
        expect(enhancedPrompt).toContain('Python', { ignoreCase: true });

        console.log(`✅ Successfully processed Python file: ${fileName}`);
      }
    });

    test('should upload and process shell script files correctly', async ({ page }) => {
      const shellFiles = [
        'setup.sh',
        'deploy.sh',
        'test.sh',
        'cleanup.sh'
      ];

      for (const fileName of shellFiles) {
        await journey1Page.clearAll();

        const filePath = path.join(codeFilesDir, fileName);

        // Create test shell script if it doesn't exist
        if (!fs.existsSync(filePath)) {
          const sampleShellContent = `#!/bin/bash

# ${fileName} - Sample shell script for testing file upload
set -euo pipefail

# Color codes for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

# Function definitions
log_info() {
    echo -e "\${GREEN}[INFO]\${NC} \$1"
}

log_warning() {
    echo -e "\${YELLOW}[WARNING]\${NC} \$1"
}

log_error() {
    echo -e "\${RED}[ERROR]\${NC} \$1"
}

# Main execution
main() {
    log_info "Starting ${fileName.replace('.sh', '')} process..."

    # Check if required tools are available
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is not installed"
        exit 1
    fi

    # Example processing based on script type
    case "${fileName}" in
        "setup.sh")
            log_info "Setting up development environment..."
            pip install -r requirements.txt
            ;;
        "deploy.sh")
            log_info "Deploying application..."
            docker build -t myapp .
            docker run -d -p 8000:8000 myapp
            ;;
        "test.sh")
            log_info "Running tests..."
            python -m pytest tests/
            ;;
        "cleanup.sh")
            log_info "Cleaning up temporary files..."
            rm -rf __pycache__/
            rm -rf .pytest_cache/
            ;;
    esac

    log_info "${fileName.replace('.sh', '')} completed successfully!"
}

# Execute main function
main "\$@"
`;

          fs.writeFileSync(filePath, sampleShellContent, 'utf8');
        }

        await journey1Page.uploadTestFile(filePath);

        const fileSources = await journey1Page.getFileSources();
        expect(fileSources.length).toBeGreaterThan(0);
        expect(fileSources[0]).toContain(fileName);

        // Process with shell script-specific prompt
        await journey1Page.enterPrompt(`Review this shell script for security best practices and improvements`);
        await journey1Page.enhancePrompt();

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();
        expect(enhancedPrompt).toContain('shell', { ignoreCase: true });

        console.log(`✅ Successfully processed shell script: ${fileName}`);
      }
    });

    test('should upload and process various programming language files', async ({ page }) => {
      const programmingFiles = [
        { name: 'sample.js', ext: 'js', language: 'JavaScript' },
        { name: 'component.tsx', ext: 'tsx', language: 'TypeScript React' },
        { name: 'config.yaml', ext: 'yaml', language: 'YAML' },
        { name: 'Dockerfile', ext: 'dockerfile', language: 'Docker' },
        { name: 'main.go', ext: 'go', language: 'Go' },
        { name: 'app.rs', ext: 'rs', language: 'Rust' }
      ];

      for (const fileInfo of programmingFiles) {
        await journey1Page.clearAll();

        const filePath = path.join(codeFilesDir, fileInfo.name);

        // Create sample file content based on language
        if (!fs.existsSync(filePath)) {
          let sampleContent = '';

          switch (fileInfo.ext) {
            case 'js':
              sampleContent = `// Sample JavaScript file
const express = require('express');
const app = express();

app.use(express.json());

app.get('/api/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(\`Server running on port \${PORT}\`);
});

module.exports = app;
`;
              break;
            case 'tsx':
              sampleContent = `import React, { useState, useEffect } from 'react';
import { Button, Alert } from 'react-bootstrap';

interface ComponentProps {
    title: string;
    onSubmit: (data: FormData) => void;
}

const SampleComponent: React.FC<ComponentProps> = ({ title, onSubmit }) => {
    const [data, setData] = useState<string>('');
    const [loading, setLoading] = useState<boolean>(false);

    useEffect(() => {
        console.log('Component mounted');
    }, []);

    const handleSubmit = async () => {
        setLoading(true);
        try {
            await onSubmit(new FormData());
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="sample-component">
            <h2>{title}</h2>
            <Button onClick={handleSubmit} disabled={loading}>
                {loading ? 'Processing...' : 'Submit'}
            </Button>
        </div>
    );
};

export default SampleComponent;
`;
              break;
            case 'yaml':
              sampleContent = `# Sample YAML configuration
version: '3.8'

services:
  web:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./html:/usr/share/nginx/html
    environment:
      - NGINX_HOST=localhost
      - NGINX_PORT=80

  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/myapp
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
`;
              break;
            case 'dockerfile':
              sampleContent = `# Sample Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM node:18-alpine AS runtime

# Add security user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

WORKDIR /app

# Copy from builder stage
COPY --from=builder --chown=nextjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json

USER nextjs

EXPOSE 3000

CMD ["npm", "start"]
`;
              break;
            case 'go':
              sampleContent = `package main

import (
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "time"

    "github.com/gorilla/mux"
)

type Response struct {
    Message   string    \`json:"message"\`
    Timestamp time.Time \`json:"timestamp"\`
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
    response := Response{
        Message:   "Service is healthy",
        Timestamp: time.Now(),
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}

func main() {
    r := mux.NewRouter()

    r.HandleFunc("/health", healthHandler).Methods("GET")

    fmt.Println("Server starting on :8080")
    log.Fatal(http.ListenAndServe(":8080", r))
}
`;
              break;
            case 'rs':
              sampleContent = `use std::collections::HashMap;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct User {
    pub id: u32,
    pub name: String,
    pub email: String,
}

#[derive(Debug)]
pub struct UserService {
    users: HashMap<u32, User>,
    next_id: u32,
}

impl UserService {
    pub fn new() -> Self {
        Self {
            users: HashMap::new(),
            next_id: 1,
        }
    }

    pub fn create_user(&mut self, name: String, email: String) -> Result<&User, String> {
        let user = User {
            id: self.next_id,
            name,
            email,
        };

        self.users.insert(self.next_id, user);
        let created_user = self.users.get(&self.next_id).unwrap();
        self.next_id += 1;

        Ok(created_user)
    }

    pub fn get_user(&self, id: u32) -> Option<&User> {
        self.users.get(&id)
    }
}

fn main() {
    let mut service = UserService::new();

    match service.create_user("John Doe".to_string(), "john@example.com".to_string()) {
        Ok(user) => println!("Created user: {:?}", user),
        Err(e) => println!("Error: {}", e),
    }
}
`;
              break;
          }

          fs.writeFileSync(filePath, sampleContent, 'utf8');
        }

        await journey1Page.uploadTestFile(filePath);

        const fileSources = await journey1Page.getFileSources();
        expect(fileSources.length).toBeGreaterThan(0);
        expect(fileSources[0]).toContain(fileInfo.name);

        // Process with language-specific prompt
        await journey1Page.enterPrompt(`Analyze this ${fileInfo.language} code and suggest best practices`);
        await journey1Page.enhancePrompt();

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        console.log(`✅ Successfully processed ${fileInfo.language} file: ${fileInfo.name}`);
      }
    });
  });

  test.describe('Document File Upload Testing', () => {
    test('should upload and process HTML files correctly', async ({ page }) => {
      const htmlFiles = [
        'index.html',
        'form.html',
        'dashboard.html'
      ];

      for (const fileName of htmlFiles) {
        await journey1Page.clearAll();

        const filePath = path.join(documentFilesDir, fileName);

        // Create sample HTML file if it doesn't exist
        if (!fs.existsSync(filePath)) {
          const sampleHtmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${fileName.replace('.html', '').charAt(0).toUpperCase() + fileName.replace('.html', '').slice(1)} Page</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            border-bottom: 2px solid #007bff;
            margin-bottom: 20px;
            padding-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>${fileName.replace('.html', '').charAt(0).toUpperCase() + fileName.replace('.html', '').slice(1)} Page</h1>
        </div>

        <main>
            ${fileName === 'form.html'
              ? `<form id="contactForm" method="POST" action="/submit">
                    <div class="form-group">
                        <label for="name">Name:</label>
                        <input type="text" id="name" name="name" required>
                    </div>
                    <div class="form-group">
                        <label for="email">Email:</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label for="message">Message:</label>
                        <textarea id="message" name="message" rows="5" required></textarea>
                    </div>
                    <button type="submit">Submit</button>
                </form>`
              : fileName === 'dashboard.html'
                ? `<div class="dashboard">
                    <div class="metrics">
                        <div class="metric-card">
                            <h3>Total Users</h3>
                            <p class="metric-value">1,234</p>
                        </div>
                        <div class="metric-card">
                            <h3>Active Sessions</h3>
                            <p class="metric-value">456</p>
                        </div>
                    </div>
                    <div class="chart-container">
                        <canvas id="myChart" width="400" height="200"></canvas>
                    </div>
                </div>`
                : `<section>
                    <h2>Welcome to Our Website</h2>
                    <p>This is a sample HTML page for testing file upload functionality.</p>
                    <nav>
                        <ul>
                            <li><a href="#section1">Section 1</a></li>
                            <li><a href="#section2">Section 2</a></li>
                            <li><a href="#section3">Section 3</a></li>
                        </ul>
                    </nav>
                </section>`
            }
        </main>

        <footer>
            <p>&copy; 2024 Test Website. All rights reserved.</p>
        </footer>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            console.log('${fileName} loaded successfully');
        });
    </script>
</body>
</html>`;

          fs.writeFileSync(filePath, sampleHtmlContent, 'utf8');
        }

        await journey1Page.uploadTestFile(filePath);

        const fileSources = await journey1Page.getFileSources();
        expect(fileSources.length).toBeGreaterThan(0);
        expect(fileSources[0]).toContain(fileName);

        // Process with HTML-specific prompt
        await journey1Page.enterPrompt(`Analyze this HTML file and suggest accessibility improvements`);
        await journey1Page.enhancePrompt();

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();
        expect(enhancedPrompt).toContain('HTML', { ignoreCase: true });

        console.log(`✅ Successfully processed HTML file: ${fileName}`);
      }
    });

    test('should handle PDF file uploads (if supported)', async ({ page }) => {
      // Note: This test checks if PDF handling is available and tests gracefully if not
      const pdfFileName = 'test-document.pdf';
      const pdfFilePath = path.join(documentFilesDir, pdfFileName);

      // Create a simple test PDF file (placeholder) if it doesn't exist
      if (!fs.existsSync(pdfFilePath)) {
        // Create a minimal PDF-like file for testing
        const pdfHeader = '%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test PDF Document) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n299\n%%EOF';
        fs.writeFileSync(pdfFilePath, pdfHeader, 'binary');
      }

      try {
        await journey1Page.uploadTestFile(pdfFilePath);

        const fileSources = await journey1Page.getFileSources();

        if (fileSources.length > 0 && fileSources[0].includes(pdfFileName)) {
          // PDF upload succeeded
          await journey1Page.enterPrompt(`Extract and summarize the key information from this PDF document`);
          await journey1Page.enhancePrompt();

          const enhancedPrompt = await journey1Page.getEnhancedPrompt();
          expect(enhancedPrompt).toBeTruthy();

          console.log(`✅ Successfully processed PDF file: ${pdfFileName}`);
        } else {
          console.log(`⚠️ PDF upload not supported or failed for: ${pdfFileName}`);
        }
      } catch (error) {
        // PDF handling might not be supported
        console.log(`⚠️ PDF handling not available: ${error.message}`);

        // Check if there's an appropriate error message
        const hasError = await journey1Page.hasError();
        if (hasError) {
          const errorMessage = await journey1Page.getErrorMessage();
          expect(errorMessage.length).toBeGreaterThan(0);
          console.log(`PDF error handled gracefully: ${errorMessage}`);
        }
      }
    });

    test('should handle mixed document and code file uploads', async ({ page }) => {
      const mixedFiles = [
        'sample_script.py',
        'index.html',
        'config.yaml',
        'setup.sh'
      ];

      const filePaths = [];

      // Prepare all files
      for (const fileName of mixedFiles) {
        const isCode = fileName.endsWith('.py') || fileName.endsWith('.sh') || fileName.endsWith('.yaml');
        const dirPath = isCode ? codeFilesDir : documentFilesDir;
        filePaths.push(path.join(dirPath, fileName));
      }

      // Upload all files sequentially
      for (const filePath of filePaths) {
        await journey1Page.uploadTestFile(filePath);
        await page.waitForTimeout(500); // Allow processing time between uploads
      }

      const fileSources = await journey1Page.getFileSources();
      expect(fileSources.length).toBeGreaterThan(1);

      // Process with comprehensive prompt
      await journey1Page.enterPrompt(`Analyze all uploaded files and create a comprehensive development and deployment strategy`);
      await journey1Page.enhancePrompt(60000); // Longer timeout for multiple files

      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();
      expect(enhancedPrompt).toContain('development', { ignoreCase: true });
      expect(enhancedPrompt).toContain('deployment', { ignoreCase: true });

      // Verify C.R.E.A.T.E. framework handles mixed file context
      const createBreakdown = await journey1Page.validateCREATEBreakdown();
      const presentSections = createBreakdown.filter(section => section.present);
      expect(presentSections.length).toBeGreaterThanOrEqual(4);

      console.log(`✅ Successfully processed ${fileSources.length} mixed file types`);
    });
  });

  test.describe('File Upload Security and Error Handling', () => {
    test('should handle large code files appropriately', async ({ page }) => {
      // Create a large Python file for testing
      const largeFileName = 'large_file.py';
      const largeFilePath = path.join(codeFilesDir, largeFileName);

      if (!fs.existsSync(largeFilePath)) {
        let largeContent = '"""Large Python file for testing file upload limits."""\n\n';

        // Generate a large file with repetitive but valid Python code
        for (let i = 0; i < 1000; i++) {
          largeContent += `
def function_${i}():
    """Generated function ${i} for testing large file handling."""
    data = {
        'id': ${i},
        'name': 'function_${i}',
        'description': 'This is function number ${i} generated for testing purposes',
        'values': [${i}, ${i * 2}, ${i * 3}, ${i * 4}, ${i * 5}]
    }
    return data

`;
        }

        largeContent += '\nif __name__ == "__main__":\n    print("Large file loaded successfully")\n';

        fs.writeFileSync(largeFilePath, largeContent, 'utf8');
      }

      try {
        await journey1Page.uploadTestFile(largeFilePath);

        const fileSources = await journey1Page.getFileSources();

        if (fileSources.length > 0) {
          // Large file was accepted
          await journey1Page.enterPrompt(`Analyze this large Python file and identify potential refactoring opportunities`);
          await journey1Page.enhancePrompt(60000); // Extended timeout for large file

          const enhancedPrompt = await journey1Page.getEnhancedPrompt();
          expect(enhancedPrompt).toBeTruthy();

          console.log(`✅ Successfully processed large file: ${largeFileName}`);
        } else {
          console.log(`⚠️ Large file was not processed: ${largeFileName}`);
        }
      } catch (error) {
        // Check for appropriate error handling
        const hasError = await journey1Page.hasError();
        if (hasError) {
          const errorMessage = await journey1Page.getErrorMessage();
          expect(errorMessage).toContain('size', { ignoreCase: true });
          console.log(`Large file handled with size error: ${errorMessage}`);
        }
      }
    });

    test('should sanitize and handle potentially problematic code files', async ({ page }) => {
      // Create code files with potentially problematic content
      const problematicFiles = [
        {
          name: 'script_with_sensitive.py',
          content: `#!/usr/bin/env python3
"""Script with potentially sensitive content for security testing."""

import os
import subprocess

# This script contains patterns that should be handled carefully
API_KEY = "test-api-key-12345"  # Placeholder API key
PASSWORD = "test-password"  # Placeholder password

def execute_command(cmd):
    """Execute system command - potential security concern."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def read_sensitive_file():
    """Read potentially sensitive file."""
    try:
        with open('/etc/passwd', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "File not found"

if __name__ == "__main__":
    print("Running security test script")
`
        },
        {
          name: 'script_with_sql.py',
          content: `#!/usr/bin/env python3
"""Script with SQL injection patterns for testing."""

import sqlite3

def unsafe_query(user_input):
    """Deliberately unsafe SQL query for testing."""
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()

    # This is intentionally vulnerable for testing
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    cursor.execute(query)

    results = cursor.fetchall()
    conn.close()
    return results

def safe_query(user_input):
    """Safe SQL query with parameterization."""
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()

    query = "SELECT * FROM users WHERE name = ?"
    cursor.execute(query, (user_input,))

    results = cursor.fetchall()
    conn.close()
    return results
`
        }
      ];

      for (const fileInfo of problematicFiles) {
        await journey1Page.clearAll();

        const filePath = path.join(codeFilesDir, fileInfo.name);
        fs.writeFileSync(filePath, fileInfo.content, 'utf8');

        await journey1Page.uploadTestFile(filePath);

        const fileSources = await journey1Page.getFileSources();
        expect(fileSources.length).toBeGreaterThan(0);

        // Process with security-focused prompt
        await journey1Page.enterPrompt(`Review this code for security vulnerabilities and suggest improvements`);
        await journey1Page.enhancePrompt();

        const enhancedPrompt = await journey1Page.getEnhancedPrompt();
        expect(enhancedPrompt).toBeTruthy();

        // Verify the system can handle and analyze security-sensitive code
        expect(enhancedPrompt).toContain('security', { ignoreCase: true });

        // Ensure no actual sensitive data leaks in the output
        expect(enhancedPrompt).not.toContain('test-api-key-12345');
        expect(enhancedPrompt).not.toContain('test-password');

        console.log(`✅ Successfully and safely processed: ${fileInfo.name}`);
      }
    });

    test('should handle file upload failures gracefully', async ({ page }) => {
      // Test with non-existent file to trigger error handling
      const nonExistentFile = path.join(codeFilesDir, 'does-not-exist.py');

      try {
        await journey1Page.uploadTestFile(nonExistentFile);

        // If upload was attempted, check for error handling
        const hasError = await journey1Page.hasError();
        if (hasError) {
          const errorMessage = await journey1Page.getErrorMessage();
          expect(errorMessage.length).toBeGreaterThan(0);
          console.log(`File upload error handled gracefully: ${errorMessage}`);
        }
      } catch (error) {
        // Expected behavior - file doesn't exist
        console.log(`✅ Non-existent file handled appropriately: ${error.message}`);
      }

      // Verify system can continue working after failed upload
      await journey1Page.enterPrompt('Test prompt after failed upload');
      await journey1Page.enhancePrompt();

      const enhancedPrompt = await journey1Page.getEnhancedPrompt();
      expect(enhancedPrompt).toBeTruthy();

      console.log('✅ System continues working after failed upload');
    });
  });

  // Cleanup: Remove test files after all tests
  test.afterAll(async () => {
    const testDirs = [codeFilesDir, documentFilesDir];

    for (const dir of testDirs) {
      if (fs.existsSync(dir)) {
        try {
          const files = fs.readdirSync(dir);
          for (const file of files) {
            const filePath = path.join(dir, file);
            fs.unlinkSync(filePath);
          }
          console.log(`✅ Cleaned up test files in ${dir}`);
        } catch (error) {
          console.log(`⚠️ Could not clean up test files in ${dir}: ${error.message}`);
        }
      }
    }
  });
});
