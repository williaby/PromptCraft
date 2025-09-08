# 🔗 **API INTEGRATION TESTING - IMPLEMENTATION INSTRUCTIONS**

## **Project Overview**

**Task**: Implement comprehensive API integration testing infrastructure for PromptCraft-Hybrid to validate frontend-backend coordination, data flow, and error handling across the complete user workflow.

**Context**: A comprehensive Journey 1 UI testing framework is already complete and operational. This task extends testing coverage to validate the integration between the frontend Gradio interface and the backend Python API services.

---

## **📋 TASK SPECIFICATIONS**

### **Objective**
Create a robust API integration testing framework that validates:
- Frontend UI interactions → Backend API calls → Frontend response handling
- Data consistency between UI and API layers
- Error propagation and handling across the stack
- Performance characteristics of the integrated system

### **Success Criteria**
- ✅ Complete request-response cycle validation for all core user workflows
- ✅ Real API call testing with actual backend services (no mocking)
- ✅ Error propagation testing from backend to frontend
- ✅ Data transformation and consistency validation
- ✅ Performance integration benchmarking
- ✅ CI/CD pipeline integration

---

## **🏗️ TECHNICAL ARCHITECTURE**

### **Current System Architecture**
```
Frontend (Gradio) ←→ Backend (Python/FastAPI) ←→ Database (SQLite/PostgreSQL)
     ↓                      ↓                        ↓
  Port 7860            Internal APIs              Data Storage
```

### **Integration Points to Test**
1. **Journey 1 Enhancement Workflow**: `/api/enhance` endpoint
2. **File Upload Processing**: `/api/upload` endpoint
3. **Authentication & Session**: `/api/auth` endpoints
4. **C.R.E.A.T.E. Framework Analysis**: `/api/analyze` endpoint
5. **Metrics & Analytics**: `/api/metrics` endpoints

---

## **📁 PROJECT STRUCTURE**

### **Required Directory Structure**
```
tests/integration/
├── fixtures/
│   ├── api-client.ts               # API client helper
│   ├── test-data.ts                # Integration test data
│   └── backend-setup.ts            # Backend service management
├── api-ui-coordination.spec.ts     # Core integration tests
├── data-flow-validation.spec.ts    # Request-response validation
├── error-propagation.spec.ts       # Error handling tests
├── performance-integration.spec.ts # End-to-end performance
├── authentication-integration.spec.ts # Auth flow testing
└── file-upload-integration.spec.ts # File processing tests
```

### **Configuration Files**
```
playwright.config.integration.ts    # Integration-specific config
package.json                        # Updated with new scripts
.env.integration                    # Integration test environment
```

---

## **🔧 IMPLEMENTATION REQUIREMENTS**

### **1. Technology Stack**
- **Testing Framework**: Playwright (already established)
- **API Client**: Axios or Fetch for direct API calls
- **Assertion Library**: Playwright's built-in expect
- **Environment**: Node.js with TypeScript
- **Backend**: Python FastAPI (already running)

### **2. Required Dependencies**
Add to `package.json`:
```json
{
  "devDependencies": {
    "axios": "^1.6.0",
    "@types/axios": "^0.14.0",
    "ws": "^8.14.0",
    "@types/ws": "^8.5.0"
  },
  "scripts": {
    "test:integration": "playwright test tests/integration/",
    "test:integration:headed": "playwright test tests/integration/ --headed",
    "test:integration:debug": "playwright test tests/integration/ --debug",
    "test:api-ui": "playwright test tests/integration/api-ui-coordination.spec.ts",
    "test:data-flow": "playwright test tests/integration/data-flow-validation.spec.ts",
    "test:error-propagation": "playwright test tests/integration/error-propagation.spec.ts"
  }
}
```

---

## **📝 DETAILED IMPLEMENTATION SPECIFICATIONS**

### **Core Test File 1: API-UI Coordination**

**File**: `tests/integration/api-ui-coordination.spec.ts`

**Requirements**:
```typescript
import { test, expect } from '@playwright/test';
import { APIClient } from './fixtures/api-client';

test.describe('API-UI Coordination Tests', () => {
  let apiClient: APIClient;

  test.beforeEach(async ({ page }) => {
    apiClient = new APIClient('http://localhost:7860');
    await page.goto('http://localhost:7860');

    // Navigate to Journey 1
    const journey1Tab = page.locator('button[role="tab"]:has-text("Journey 1")');
    await journey1Tab.click();
  });

  test('should complete enhancement workflow with API validation', async ({ page }) => {
    const testPrompt = 'Create a test prompt for API integration validation';

    // 1. UI Input
    const textInput = page.locator('textarea').first();
    await textInput.fill(testPrompt);

    // 2. Monitor API call
    const apiResponsePromise = page.waitForResponse(response =>
      response.url().includes('/api/enhance') && response.status() === 200
    );

    // 3. Trigger enhancement
    const enhanceButton = page.locator('button:has-text("Enhance")');
    await enhanceButton.click();

    // 4. Validate API response
    const apiResponse = await apiResponsePromise;
    const apiData = await apiResponse.json();

    expect(apiData).toHaveProperty('enhanced_prompt');
    expect(apiData.enhanced_prompt).toBeTruthy();
    expect(apiData.enhanced_prompt.length).toBeGreaterThan(testPrompt.length);

    // 5. Validate UI displays API result
    const outputArea = page.locator('textarea').nth(1);
    const uiContent = await outputArea.inputValue();

    expect(uiContent).toContain(apiData.enhanced_prompt);
    expect(uiContent.length).toBeGreaterThan(0);

    // 6. Validate data consistency
    expect(uiContent.trim()).toBe(apiData.enhanced_prompt.trim());
  });

  test('should handle file upload API integration', async ({ page }) => {
    // Switch to file upload mode
    const fileUploadLabel = page.locator('label:has-text("📁 File Upload")');
    if (await fileUploadLabel.count() > 0) {
      await fileUploadLabel.click();

      // Create test file
      const testFilePath = await createTestFile();

      // Monitor upload API call
      const uploadResponsePromise = page.waitForResponse(response =>
        response.url().includes('/api/upload') && response.status() === 200
      );

      // Upload file via UI
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(testFilePath);

      // Validate API response
      const uploadResponse = await uploadResponsePromise;
      const uploadData = await uploadResponse.json();

      expect(uploadData).toHaveProperty('file_id');
      expect(uploadData).toHaveProperty('processed_content');

      // Validate UI reflects upload success
      const fileIndicator = page.locator('text=uploaded successfully');
      await expect(fileIndicator).toBeVisible({ timeout: 10000 });
    }
  });
});
```

### **Core Test File 2: Data Flow Validation**

**File**: `tests/integration/data-flow-validation.spec.ts`

**Requirements**:
```typescript
test.describe('Data Flow Validation', () => {
  test('should maintain data integrity through complete workflow', async ({ page }) => {
    // Test complex data transformation through API
    const complexPrompt = {
      text: 'Complex business analysis prompt with specific requirements',
      parameters: {
        reasoning_depth: 'comprehensive',
        search_strategy: 'tier2',
        temperature: 0.7
      }
    };

    // UI input with parameters
    await setComplexPromptWithParameters(page, complexPrompt);

    // Monitor API request payload
    const apiRequestPromise = page.waitForRequest(request =>
      request.url().includes('/api/enhance')
    );

    await page.click('button:has-text("Enhance")');

    // Validate request payload
    const apiRequest = await apiRequestPromise;
    const requestData = apiRequest.postDataJSON();

    expect(requestData.prompt).toBe(complexPrompt.text);
    expect(requestData.reasoning_depth).toBe(complexPrompt.parameters.reasoning_depth);
    expect(requestData.temperature).toBe(complexPrompt.parameters.temperature);

    // Validate response data integrity
    const response = await page.waitForResponse(response =>
      response.url().includes('/api/enhance')
    );

    const responseData = await response.json();

    // Check all expected response fields
    expect(responseData).toHaveProperty('enhanced_prompt');
    expect(responseData).toHaveProperty('analysis');
    expect(responseData).toHaveProperty('framework_breakdown');
    expect(responseData.analysis).toHaveProperty('context');
    expect(responseData.analysis).toHaveProperty('request');

    // Validate UI displays all data correctly
    await validateUIDisplaysAllData(page, responseData);
  });
});
```

### **Core Test File 3: Error Propagation Testing**

**File**: `tests/integration/error-propagation.spec.ts`

**Requirements**:
```typescript
test.describe('Error Propagation Tests', () => {
  test('should handle API errors gracefully in UI', async ({ page }) => {
    // Test various API error scenarios
    const errorScenarios = [
      {
        name: 'Invalid prompt format',
        payload: { prompt: null },
        expectedError: 'Invalid prompt format'
      },
      {
        name: 'Rate limit exceeded',
        setup: () => triggerRateLimit(),
        expectedError: 'Rate limit exceeded'
      },
      {
        name: 'Service unavailable',
        mockResponse: { status: 503, body: { error: 'Service temporarily unavailable' } },
        expectedError: 'Service temporarily unavailable'
      }
    ];

    for (const scenario of errorScenarios) {
      // Setup error condition
      if (scenario.setup) await scenario.setup();
      if (scenario.mockResponse) {
        await page.route('**/api/enhance', route =>
          route.fulfill(scenario.mockResponse)
        );
      }

      // Trigger the workflow
      await page.fill('textarea', scenario.payload?.prompt || 'test prompt');
      await page.click('button:has-text("Enhance")');

      // Validate error is displayed in UI
      const errorSelector = [
        'div[role="alert"]',
        'div:has-text("error")',
        '.error-message',
        '.notification.error'
      ];

      let errorFound = false;
      for (const selector of errorSelector) {
        const errorElement = page.locator(selector).first();
        if (await errorElement.count() > 0) {
          const errorText = await errorElement.textContent();
          expect(errorText.toLowerCase()).toContain(scenario.expectedError.toLowerCase());
          errorFound = true;
          break;
        }
      }

      expect(errorFound).toBe(true);

      // Clear error state for next test
      await page.reload();
    }
  });
});
```

---

## **🔧 HELPER UTILITIES TO IMPLEMENT**

### **API Client Helper**

**File**: `tests/integration/fixtures/api-client.ts`

```typescript
import axios, { AxiosInstance, AxiosResponse } from 'axios';

export class APIClient {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      }
    });
  }

  async enhance(prompt: string, options: any = {}): Promise<AxiosResponse> {
    return this.client.post('/api/enhance', {
      prompt,
      ...options
    });
  }

  async uploadFile(filePath: string): Promise<AxiosResponse> {
    const formData = new FormData();
    formData.append('file', filePath);

    return this.client.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });
  }

  async getAnalysis(sessionId: string): Promise<AxiosResponse> {
    return this.client.get(`/api/analysis/${sessionId}`);
  }

  async getMetrics(): Promise<AxiosResponse> {
    return this.client.get('/api/metrics');
  }
}
```

### **Backend Setup Helper**

**File**: `tests/integration/fixtures/backend-setup.ts`

```typescript
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export class BackendSetup {
  private backendProcess: any;

  async startBackend(): Promise<void> {
    console.log('Starting backend services...');

    // Start the Python backend
    this.backendProcess = exec('poetry run python -m src.main', {
      env: { ...process.env, PROMPTCRAFT_API_PORT: '7860' }
    });

    // Wait for backend to be ready
    await this.waitForBackendReady();
  }

  async stopBackend(): Promise<void> {
    if (this.backendProcess) {
      this.backendProcess.kill();
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }

  private async waitForBackendReady(): Promise<void> {
    const maxAttempts = 60; // 2 minutes
    let attempts = 0;

    while (attempts < maxAttempts) {
      try {
        const { stdout } = await execAsync('curl -s http://localhost:7860/health || echo "not ready"');
        if (!stdout.includes('not ready')) {
          console.log('Backend is ready!');
          return;
        }
      } catch (error) {
        // Continue trying
      }

      attempts++;
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    throw new Error('Backend failed to start within timeout period');
  }
}
```

---

## **⚙️ CONFIGURATION REQUIREMENTS**

### **Playwright Configuration**

**File**: `playwright.config.integration.ts`

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/integration',
  timeout: 60000, // Longer timeout for integration tests
  expect: {
    timeout: 15000
  },
  fullyParallel: false, // Run sequentially to avoid API conflicts
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Single worker for integration tests
  reporter: [
    ['html', { outputFolder: 'integration-results' }],
    ['json', { outputFile: 'integration-results.json' }]
  ],
  use: {
    baseURL: 'http://localhost:7860',
    trace: 'on-first-retry',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'integration-chromium',
      use: {
        browserName: 'chromium',
        // Additional context for integration testing
        contextOptions: {
          recordVideo: { dir: 'videos/integration/' }
        }
      },
    }
  ],
  globalSetup: require.resolve('./tests/integration/fixtures/global-setup.ts'),
  globalTeardown: require.resolve('./tests/integration/fixtures/global-teardown.ts'),
});
```

### **Environment Configuration**

**File**: `.env.integration`

```env
# Integration Testing Environment
NODE_ENV=integration
PROMPTCRAFT_API_PORT=7860
BACKEND_URL=http://localhost:7860
API_TIMEOUT=30000

# Database (use test database)
DATABASE_URL=sqlite:///./test_integration.db

# Logging
LOG_LEVEL=debug
INTEGRATION_TESTS=true

# API Keys (use test keys)
OPENROUTER_API_KEY=test_key_for_integration
```

---

## **🧪 TESTING SCENARIOS TO IMPLEMENT**

### **Priority 1: Core Workflows**
1. **Complete Enhancement Workflow**
   - UI input → API processing → UI display
   - Parameter passing and validation
   - Response data consistency

2. **File Upload Integration**
   - File selection → Upload API → Processing feedback
   - Multiple file handling
   - Error scenarios (file too large, unsupported format)

3. **Authentication Flow**
   - Login → Session creation → API authentication
   - Session expiration handling
   - Permission validation

### **Priority 2: Error Handling**
1. **Network Errors**
   - Connection timeouts
   - Service unavailable scenarios
   - Network interruption during processing

2. **API Errors**
   - Invalid request format
   - Rate limiting
   - Server errors (500, 503)

3. **Data Validation Errors**
   - Malformed responses
   - Missing required fields
   - Type conversion errors

### **Priority 3: Performance Integration**
1. **Response Time Validation**
   - End-to-end workflow timing
   - API response time vs UI update timing
   - Performance under different load conditions

2. **Resource Usage**
   - Memory consumption during long processes
   - Concurrent request handling
   - Background process monitoring

---

## **📊 SUCCESS METRICS & VALIDATION**

### **Test Coverage Requirements**
- ✅ 100% of core user workflows covered
- ✅ All major API endpoints tested with UI integration
- ✅ Error scenarios covered for all integration points
- ✅ Performance benchmarks established for integrated flows

### **Quality Gates**
- All integration tests pass consistently (95%+ success rate)
- Response times within acceptable thresholds (<10s for standard workflows)
- Error handling provides clear user feedback
- No data loss or corruption in any workflow

### **Documentation Requirements**
- Test execution instructions and troubleshooting guide
- API endpoint documentation for testing team reference
- Error scenario catalog with expected behaviors
- Performance benchmark documentation

---

## **🔄 CI/CD INTEGRATION**

### **Pipeline Integration**
Add to existing `.github/workflows/ui-testing-pipeline.yml`:

```yaml
integration-tests:
  name: API Integration Tests
  runs-on: ubuntu-latest
  needs: smoke-tests
  timeout-minutes: 30

  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Start backend services
      run: |
        poetry run python -m src.main &
        timeout 120 bash -c 'until curl -s http://localhost:7860; do sleep 2; done'

    - name: Run integration tests
      run: |
        npm run test:integration
      env:
        NODE_ENV: integration

    - name: Upload integration test results
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: integration-test-results
        path: |
          integration-results/
          integration-results.json
        retention-days: 30
```

---

## **📋 DELIVERABLES CHECKLIST**

### **Code Deliverables**
- [ ] Complete integration test suite (6+ test files)
- [ ] Helper utilities (API client, backend setup, test data)
- [ ] Configuration files (Playwright config, environment)
- [ ] NPM scripts for test execution

### **Documentation Deliverables**
- [ ] Implementation documentation with examples
- [ ] Troubleshooting guide for common issues
- [ ] API endpoint reference for testing
- [ ] Performance benchmark baseline documentation

### **Quality Assurance**
- [ ] All tests pass locally and in CI
- [ ] Test coverage report generated
- [ ] Performance benchmarks established
- [ ] Error handling scenarios validated

---

## **🚀 GETTING STARTED**

### **Initial Setup Steps**
1. **Clone repository** and switch to integration testing branch
2. **Install dependencies** and configure environment
3. **Start backend services** and validate connectivity
4. **Implement core API client** helper utility first
5. **Begin with simple API-UI coordination test**
6. **Iteratively add complexity** and additional test scenarios

### **Development Approach**
- Start with the simplest integration scenario (basic enhancement workflow)
- Build helper utilities as you encounter repeated patterns
- Use the existing Journey 1 UI patterns as a foundation
- Focus on data consistency validation throughout
- Add comprehensive error handling as scenarios are identified

### **Questions & Support**
- Existing Journey 1 UI test files provide excellent patterns to follow
- Backend API documentation should be available in `docs/` folder
- Use the established browser automation patterns from Journey 1 tests
- Leverage existing test data generators where applicable

---

**Expected Timeline**: 2-3 weeks for complete implementation
**Team Size**: 1-2 developers with Playwright and API testing experience
**Dependencies**: Backend services must be operational, Journey 1 UI tests provide patterns

**Status**: Ready to begin implementation
**Priority**: P1 - High priority for complete testing coverage**
