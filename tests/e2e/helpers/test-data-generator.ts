/**
 * Automated Test Data Generation and Management System
 * Provides dynamic test data creation for comprehensive UI testing scenarios
 */

import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';

export interface TestScenario {
  id: string;
  category: string;
  prompt: string;
  expectedBehavior: string[];
  complexity: 'minimal' | 'moderate' | 'complex' | 'extreme';
  domain: string;
  tags: string[];
}

export interface FileTestData {
  name: string;
  content: string;
  type: string;
  size: number;
  encoding: string;
  securityLevel: 'safe' | 'caution' | 'restricted';
}

export class TestDataGenerator {
  private static instance: TestDataGenerator;
  private testDataPath: string;
  private scenarios: Map<string, TestScenario> = new Map();
  private fileData: Map<string, FileTestData> = new Map();

  private constructor() {
    this.testDataPath = path.join(__dirname, '../data');
    this.ensureDirectoryExists(this.testDataPath);
    this.initializeTestData();
  }

  public static getInstance(): TestDataGenerator {
    if (!TestDataGenerator.instance) {
      TestDataGenerator.instance = new TestDataGenerator();
    }
    return TestDataGenerator.instance;
  }

  /**
   * Generate C.R.E.A.T.E. Framework Test Scenarios
   */
  public generateCREATETestScenarios(): TestScenario[] {
    const scenarios: TestScenario[] = [
      // Context (C) Testing Scenarios
      {
        id: 'create-context-minimal',
        category: 'context-analysis',
        prompt: 'Write something',
        expectedBehavior: ['request-clarification', 'context-gathering', 'specific-questions'],
        complexity: 'minimal',
        domain: 'general',
        tags: ['context', 'minimal', 'clarification']
      },
      {
        id: 'create-context-rich',
        category: 'context-analysis',
        prompt: 'Write a professional email to the engineering team about the quarterly security review meeting scheduled for Friday, March 15th at 2 PM in Conference Room B, focusing on our recent penetration testing results and required compliance updates for SOC 2 certification',
        expectedBehavior: ['context-leveraging', 'specific-details', 'professional-tone', 'security-domain'],
        complexity: 'complex',
        domain: 'enterprise-security',
        tags: ['context', 'rich', 'professional', 'security']
      },

      // Request (R) Testing Scenarios
      {
        id: 'create-request-vague',
        category: 'request-specification',
        prompt: 'Make it better and more useful',
        expectedBehavior: ['request-specification', 'requirement-gathering', 'improvement-clarification'],
        complexity: 'minimal',
        domain: 'general',
        tags: ['request', 'vague', 'specification']
      },
      {
        id: 'create-request-specific',
        category: 'request-specification',
        prompt: 'Create a 750-word technical blog post explaining microservices architecture benefits for enterprise applications, targeted at CTOs and senior engineers, with 3 specific use cases, implementation considerations, and measurable ROI metrics',
        expectedBehavior: ['clear-requirements', 'technical-accuracy', 'target-audience', 'measurable-outcomes'],
        complexity: 'complex',
        domain: 'enterprise-technology',
        tags: ['request', 'specific', 'technical', 'blog']
      },

      // Examples (E) Testing Scenarios
      {
        id: 'create-examples-code',
        category: 'examples-integration',
        prompt: 'Write a Python function for data validation with error handling and logging',
        expectedBehavior: ['code-examples', 'error-handling-patterns', 'logging-implementation', 'validation-logic'],
        complexity: 'moderate',
        domain: 'software-development',
        tags: ['examples', 'code', 'python', 'validation']
      },
      {
        id: 'create-examples-business',
        category: 'examples-integration',
        prompt: 'Draft a performance review template for software engineers with clear evaluation criteria and growth metrics',
        expectedBehavior: ['template-structure', 'evaluation-examples', 'metrics-definition', 'growth-pathways'],
        complexity: 'moderate',
        domain: 'human-resources',
        tags: ['examples', 'template', 'performance', 'evaluation']
      },

      // Augmentation (A) Testing Scenarios
      {
        id: 'create-augmentation-framework',
        category: 'augmentation-frameworks',
        prompt: 'Design a customer onboarding process for our SaaS platform that increases trial-to-paid conversion rates',
        expectedBehavior: ['framework-application', 'conversion-optimization', 'user-journey-mapping', 'metrics-tracking'],
        complexity: 'complex',
        domain: 'product-management',
        tags: ['augmentation', 'framework', 'onboarding', 'conversion']
      },

      // Tone (T) Testing Scenarios
      {
        id: 'create-tone-professional',
        category: 'tone-evaluation',
        prompt: 'Write a message to inform customers about a security incident that affected user data',
        expectedBehavior: ['professional-tone', 'transparency', 'security-communication', 'trust-building'],
        complexity: 'moderate',
        domain: 'crisis-communication',
        tags: ['tone', 'professional', 'security', 'crisis']
      },
      {
        id: 'create-tone-casual',
        category: 'tone-evaluation',
        prompt: 'Create social media content for our company culture blog showcasing team achievements and office events',
        expectedBehavior: ['casual-tone', 'engaging-content', 'culture-reflection', 'social-media-optimization'],
        complexity: 'moderate',
        domain: 'marketing-social',
        tags: ['tone', 'casual', 'social', 'culture']
      },

      // Evaluation (E) Testing Scenarios
      {
        id: 'create-evaluation-metrics',
        category: 'evaluation-criteria',
        prompt: 'Develop a comprehensive project success framework for software development initiatives with quantifiable metrics',
        expectedBehavior: ['success-metrics', 'quantifiable-outcomes', 'evaluation-criteria', 'project-management'],
        complexity: 'complex',
        domain: 'project-management',
        tags: ['evaluation', 'metrics', 'success', 'project']
      }
    ];

    // Store scenarios for later retrieval
    scenarios.forEach(scenario => {
      this.scenarios.set(scenario.id, scenario);
    });

    return scenarios;
  }

  /**
   * Generate File Upload Test Data
   */
  public generateFileTestData(): FileTestData[] {
    const fileData: FileTestData[] = [
      // Safe Files
      {
        name: 'readme.md',
        content: `# Project Documentation

## Overview
This is a test markdown file for validation.

## Features
- Feature 1: Basic functionality
- Feature 2: Advanced options
- Feature 3: Integration capabilities

## Installation
\`\`\`bash
npm install
npm run build
npm start
\`\`\`

## Contributing
Please read our contributing guidelines before submitting changes.
`,
        type: 'markdown',
        size: 0, // Will be calculated
        encoding: 'utf8',
        securityLevel: 'safe'
      },

      // Python Code Files
      {
        name: 'data_processor.py',
        content: `#!/usr/bin/env python3
"""
Data processing module with comprehensive error handling and logging.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Result container for data processing operations."""
    success: bool
    data: Optional[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]

class DataProcessor:
    """Advanced data processor with validation and error handling."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.processed_count = 0
        logger.info("DataProcessor initialized with config: %s", self.config)

    def validate_input(self, data: Any) -> ProcessingResult:
        """Validate input data structure and content."""
        errors = []
        warnings = []

        if not data:
            errors.append("Input data cannot be empty")

        if isinstance(data, dict):
            required_fields = self.config.get('required_fields', [])
            for field in required_fields:
                if field not in data:
                    errors.append(f"Required field missing: {field}")

        return ProcessingResult(
            success=len(errors) == 0,
            data=data if len(errors) == 0 else None,
            errors=errors,
            warnings=warnings
        )

    def process_data(self, data: Any) -> ProcessingResult:
        """Process validated data with comprehensive error handling."""
        try:
            # Validate input first
            validation_result = self.validate_input(data)
            if not validation_result.success:
                return validation_result

            # Process the data
            processed_data = self._transform_data(data)
            self.processed_count += 1

            logger.info("Successfully processed data item %d", self.processed_count)

            return ProcessingResult(
                success=True,
                data=processed_data,
                errors=[],
                warnings=[]
            )

        except Exception as e:
            logger.error("Data processing failed: %s", str(e))
            return ProcessingResult(
                success=False,
                data=None,
                errors=[f"Processing error: {str(e)}"],
                warnings=[]
            )

    def _transform_data(self, data: Any) -> Dict[str, Any]:
        """Internal data transformation logic."""
        if isinstance(data, dict):
            return {
                **data,
                'processed_timestamp': self._get_timestamp(),
                'processor_version': '1.0.0'
            }
        return {'raw_data': data, 'processed_timestamp': self._get_timestamp()}

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

# Example usage
if __name__ == "__main__":
    processor = DataProcessor({
        'required_fields': ['id', 'name'],
        'max_items': 1000
    })

    test_data = {
        'id': '12345',
        'name': 'Test Item',
        'description': 'Sample data for processing'
    }

    result = processor.process_data(test_data)

    if result.success:
        print("Processing successful:", json.dumps(result.data, indent=2))
    else:
        print("Processing failed:", result.errors)
`,
        type: 'python',
        size: 0,
        encoding: 'utf8',
        securityLevel: 'safe'
      },

      // Shell Script Files
      {
        name: 'deploy.sh',
        content: `#!/bin/bash
# Deployment script with comprehensive error handling and logging
# Security Level: Caution - Contains system operations

set -euo pipefail  # Exit on any error, undefined variable, or pipe failure

# Configuration
SCRIPT_DIR="$(cd "$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="\${SCRIPT_DIR}/deploy.log"
APP_NAME="promptcraft-hybrid"
VERSION="1.0.0"

# Logging function
log() {
    local level="\$1"
    shift
    echo "[\$(date '+%Y-%m-%d %H:%M:%S')] [\$level] \$*" | tee -a "\$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR" "\$1"
    exit 1
}

# Validate environment
validate_environment() {
    log "INFO" "Validating deployment environment..."

    # Check required commands
    local required_commands=("docker" "docker-compose" "git" "curl")
    for cmd in "\${required_commands[@]}"; do
        if ! command -v "\$cmd" >/dev/null 2>&1; then
            error_exit "Required command not found: \$cmd"
        fi
    done

    # Check environment variables
    local required_env=("DEPLOY_ENV" "API_KEY")
    for env_var in "\${required_env[@]}"; do
        if [[ -z "\${!env_var:-}" ]]; then
            error_exit "Required environment variable not set: \$env_var"
        fi
    done

    log "INFO" "Environment validation completed successfully"
}

# Build application
build_application() {
    log "INFO" "Building application \$APP_NAME version \$VERSION..."

    # Clean previous builds
    if [[ -d "dist" ]]; then
        rm -rf dist
        log "INFO" "Cleaned previous build artifacts"
    fi

    # Build with error checking
    if ! npm run build; then
        error_exit "Application build failed"
    fi

    log "INFO" "Application build completed successfully"
}

# Deploy to environment
deploy_application() {
    log "INFO" "Deploying to environment: \$DEPLOY_ENV"

    # Create deployment directory
    local deploy_dir="/opt/\$APP_NAME"
    if [[ ! -d "\$deploy_dir" ]]; then
        sudo mkdir -p "\$deploy_dir"
        log "INFO" "Created deployment directory: \$deploy_dir"
    fi

    # Copy application files
    sudo cp -r dist/* "\$deploy_dir/"

    # Update permissions
    sudo chown -R www-data:www-data "\$deploy_dir"
    sudo chmod -R 755 "\$deploy_dir"

    log "INFO" "Application deployed successfully to \$deploy_dir"
}

# Health check
perform_health_check() {
    log "INFO" "Performing post-deployment health check..."

    local health_url="http://localhost:7860/health"
    local max_attempts=30
    local attempt=1

    while [[ \$attempt -le \$max_attempts ]]; do
        if curl -s "\$health_url" >/dev/null 2>&1; then
            log "INFO" "Health check passed on attempt \$attempt"
            return 0
        fi

        log "WARN" "Health check failed, attempt \$attempt/\$max_attempts"
        sleep 10
        ((attempt++))
    done

    error_exit "Health check failed after \$max_attempts attempts"
}

# Main deployment process
main() {
    log "INFO" "Starting deployment of \$APP_NAME version \$VERSION"

    validate_environment
    build_application
    deploy_application
    perform_health_check

    log "INFO" "Deployment completed successfully"
    log "INFO" "Application \$APP_NAME version \$VERSION is now running"
}

# Execute main function with all arguments
main "\$@"
`,
        type: 'shell',
        size: 0,
        encoding: 'utf8',
        securityLevel: 'caution'
      },

      // HTML with potential security concerns
      {
        name: 'sample_page.html',
        content: `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Sample HTML page for security testing">
    <title>Sample Test Page</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            border-bottom: 2px solid #333;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .code-block {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 15px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            overflow-x: auto;
        }
        .warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Security Testing Sample Page</h1>
            <p>This HTML file contains various elements for security validation testing.</p>
        </div>

        <main>
            <section>
                <h2>Safe Content Section</h2>
                <p>This section contains standard HTML elements that should be processed safely:</p>

                <ul>
                    <li>Text content with <strong>formatting</strong></li>
                    <li>Links to <a href="https://example.com" target="_blank" rel="noopener">external sites</a></li>
                    <li>Images with alt text</li>
                    <li>Code examples</li>
                </ul>
            </section>

            <section>
                <h2>Code Example Section</h2>
                <p>Sample code block for syntax highlighting testing:</p>

                <div class="code-block">
function validateUser(userData) {
    // Input validation
    if (!userData || typeof userData !== 'object') {
        throw new Error('Invalid user data provided');
    }

    // Required field validation
    const requiredFields = ['email', 'username'];
    for (const field of requiredFields) {
        if (!userData[field]) {
            throw new Error(\`Missing required field: \${field}\`);
        }
    }

    return true;
}
                </div>
            </section>

            <section>
                <h2>Security Considerations</h2>
                <div class="warning">
                    <strong>Note:</strong> This HTML file is designed for security testing.
                    In a real application, all user-provided HTML content should be sanitized
                    to prevent XSS attacks and other security vulnerabilities.
                </div>

                <p>Security testing areas covered:</p>
                <ul>
                    <li>Script tag handling (should be neutralized)</li>
                    <li>Event attribute sanitization</li>
                    <li>Link target validation</li>
                    <li>Image source validation</li>
                    <li>CSS injection prevention</li>
                </ul>
            </section>

            <!-- This script block should be safely handled by the system -->
            <script type="application/json" id="config-data">
            {
                "testMode": true,
                "version": "1.0.0",
                "features": ["validation", "sanitization", "security-testing"]
            }
            </script>

            <!-- This comment should be preserved but any scripts should be neutralized -->
            <!--
                Note: Any actual JavaScript should be safely handled:
                <script>console.log('This should not execute in upload context');</script>
            -->
        </main>

        <footer>
            <p><small>Generated for security testing purposes. Last updated: <span id="timestamp">2024-01-01</span></small></p>
        </footer>
    </div>

    <!-- Safe script for timestamp - should be handled appropriately -->
    <noscript>
        <p>JavaScript is disabled. Some interactive features may not work.</p>
    </noscript>
</body>
</html>`,
        type: 'html',
        size: 0,
        encoding: 'utf8',
        securityLevel: 'caution'
      },

      // JSON Configuration Files
      {
        name: 'test_config.json',
        content: JSON.stringify({
          "environment": "test",
          "api": {
            "baseUrl": "https://api.test.example.com",
            "timeout": 30000,
            "retries": 3
          },
          "features": {
            "enableAnalytics": false,
            "enableLogging": true,
            "enableCaching": true
          },
          "security": {
            "requireHttps": true,
            "allowedOrigins": ["localhost", "test.example.com"],
            "rateLimiting": {
              "windowMs": 900000,
              "max": 100
            }
          },
          "testing": {
            "mockExternalApis": true,
            "seedDatabase": true,
            "cleanupAfterTests": true
          }
        }, null, 2),
        type: 'json',
        size: 0,
        encoding: 'utf8',
        securityLevel: 'safe'
      }
    ];

    // Calculate sizes and store file data
    fileData.forEach(file => {
      file.size = Buffer.byteLength(file.content, file.encoding as BufferEncoding);
      this.fileData.set(file.name, file);
    });

    return fileData;
  }

  /**
   * Generate Performance Test Scenarios
   */
  public generatePerformanceTestData(): TestScenario[] {
    const performanceScenarios: TestScenario[] = [
      {
        id: 'perf-short-prompt',
        category: 'performance-baseline',
        prompt: 'Create a simple greeting message',
        expectedBehavior: ['fast-response', 'under-3-seconds', 'basic-enhancement'],
        complexity: 'minimal',
        domain: 'general',
        tags: ['performance', 'baseline', 'fast']
      },
      {
        id: 'perf-medium-prompt',
        category: 'performance-standard',
        prompt: 'Write a comprehensive project status report for the quarterly business review, including progress updates, risk assessments, budget analysis, and recommendations for the next quarter',
        expectedBehavior: ['standard-response', 'under-10-seconds', 'detailed-enhancement'],
        complexity: 'moderate',
        domain: 'business',
        tags: ['performance', 'standard', 'business']
      },
      {
        id: 'perf-long-prompt',
        category: 'performance-stress',
        prompt: `Create a comprehensive strategic business plan for a fintech startup that will revolutionize personal finance management through AI-powered insights, automated investment recommendations, and integrated financial health monitoring. The plan should include detailed market analysis of the competitive landscape including established players like Mint, Personal Capital, YNAB, and emerging fintech competitors such as Robinhood, Acorns, and Betterment. Include comprehensive financial projections for the first five years with monthly granularity for year one and quarterly for subsequent years, covering revenue streams from freemium subscriptions, premium features, financial advisor marketplace commissions, and white-label licensing opportunities. Develop a detailed go-to-market strategy that addresses customer acquisition through digital marketing channels, strategic partnerships with banks and credit unions, influencer collaborations with financial education content creators, and referral programs that incentivize existing users to bring in new customers. The technology architecture section should cover cloud infrastructure requirements with considerations for AWS, Azure, and Google Cloud platforms, security compliance requirements including PCI DSS, SOC 2 Type II, and various state and federal financial services regulations, API integrations with banking systems, investment platforms, and credit monitoring services, machine learning infrastructure for personalized recommendations and predictive financial modeling, and mobile-first application development with cross-platform compatibility. Include a comprehensive team building plan that outlines key roles including engineering leadership, data science specialists, regulatory compliance officers, customer success managers, and business development professionals, with detailed hiring timelines, compensation structures, equity distribution strategies, and performance evaluation frameworks. The fundraising strategy should identify target investors including fintech-focused venture capital firms, angel investors with domain expertise, strategic investors from the financial services industry, and government grants or programs supporting financial technology innovation, with detailed valuation methodologies, funding milestone requirements, and investor relations management strategies.`,
        expectedBehavior: ['extended-response', 'under-30-seconds', 'comprehensive-enhancement'],
        complexity: 'extreme',
        domain: 'fintech-strategy',
        tags: ['performance', 'stress', 'extreme', 'fintech']
      }
    ];

    performanceScenarios.forEach(scenario => {
      this.scenarios.set(scenario.id, scenario);
    });

    return performanceScenarios;
  }

  /**
   * Get test scenario by ID
   */
  public getScenario(id: string): TestScenario | undefined {
    return this.scenarios.get(id);
  }

  /**
   * Get scenarios by category
   */
  public getScenariosByCategory(category: string): TestScenario[] {
    return Array.from(this.scenarios.values()).filter(scenario =>
      scenario.category === category
    );
  }

  /**
   * Get scenarios by complexity
   */
  public getScenariosByComplexity(complexity: TestScenario['complexity']): TestScenario[] {
    return Array.from(this.scenarios.values()).filter(scenario =>
      scenario.complexity === complexity
    );
  }

  /**
   * Write test file to disk
   */
  public async writeTestFile(fileName: string): Promise<string> {
    const fileData = this.fileData.get(fileName);
    if (!fileData) {
      throw new Error(`File data not found: ${fileName}`);
    }

    const filePath = path.join(this.testDataPath, 'generated', fileName);
    this.ensureDirectoryExists(path.dirname(filePath));

    fs.writeFileSync(filePath, fileData.content, fileData.encoding as BufferEncoding);
    return filePath;
  }

  /**
   * Clean up generated test files
   */
  public cleanupGeneratedFiles(): void {
    const generatedDir = path.join(this.testDataPath, 'generated');
    if (fs.existsSync(generatedDir)) {
      const files = fs.readdirSync(generatedDir);
      files.forEach(file => {
        fs.unlinkSync(path.join(generatedDir, file));
      });
      fs.rmdirSync(generatedDir);
    }
  }

  /**
   * Generate test data summary report
   */
  public generateSummaryReport(): string {
    const scenarios = Array.from(this.scenarios.values());
    const files = Array.from(this.fileData.values());

    const report = {
      timestamp: new Date().toISOString(),
      scenarios: {
        total: scenarios.length,
        byCategory: this.groupBy(scenarios, 'category'),
        byComplexity: this.groupBy(scenarios, 'complexity'),
        byDomain: this.groupBy(scenarios, 'domain')
      },
      files: {
        total: files.length,
        byType: this.groupBy(files, 'type'),
        bySecurityLevel: this.groupBy(files, 'securityLevel'),
        totalSize: files.reduce((sum, file) => sum + file.size, 0)
      }
    };

    return JSON.stringify(report, null, 2);
  }

  private initializeTestData(): void {
    // Initialize all test data sets
    this.generateCREATETestScenarios();
    this.generateFileTestData();
    this.generatePerformanceTestData();
  }

  private ensureDirectoryExists(dirPath: string): void {
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
  }

  private groupBy<T>(array: T[], key: keyof T): Record<string, number> {
    return array.reduce((groups, item) => {
      const value = String(item[key]);
      groups[value] = (groups[value] || 0) + 1;
      return groups;
    }, {} as Record<string, number>);
  }
}

// Export singleton instance
export const testDataGenerator = TestDataGenerator.getInstance();

// Export utility functions
export function generateTestId(): string {
  return crypto.randomBytes(8).toString('hex');
}

export function generateTestTimestamp(): string {
  return new Date().toISOString().replace(/[:.]/g, '-');
}

export function calculateChecksum(content: string): string {
  return crypto.createHash('md5').update(content).digest('hex');
}
