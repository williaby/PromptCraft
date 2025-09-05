# PromptCraft-Hybrid E2E Testing Suite

Comprehensive end-to-end testing for PromptCraft-Hybrid using Playwright to validate UI functionality, user journeys, security, and performance.

## 🎯 Overview

This testing suite provides comprehensive validation of:
- **Core UI functionality** across all four user journeys
- **Security measures** including file upload validation and input sanitization
- **Performance benchmarks** for load times and API responses
- **API integration** with health checks and error handling
- **Cross-browser compatibility** (Chrome, Firefox, Safari, Edge)
- **Mobile responsiveness** and accessibility compliance

## 📁 Project Structure

```
tests/e2e/
├── fixtures/           # Page Object Models
│   ├── BasePage.ts     # Common page interactions
│   ├── Journey1Page.ts # Smart Templates page
│   └── global-setup.ts # Test environment setup
├── helpers/            # Test utilities
│   └── test-utils.ts   # Common testing functions
├── journeys/           # Journey-specific tests
│   └── test-journey1-smart-templates.spec.ts
├── data/               # Test data files
│   ├── files/          # Sample upload files
│   └── malicious/      # Security test files
└── *.spec.ts          # Test suites
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ installed
- PromptCraft application running on `localhost:7860`
- Python backend running on `localhost:7862`

### Installation

```bash
# Install dependencies
npm install

# Install Playwright browsers
npm run test:e2e:install

# Install system dependencies (Linux/macOS)
npm run test:e2e:install-deps
```

### Running Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run tests with browser UI visible
npm run test:e2e:headed

# Run tests with debug mode
npm run test:e2e:debug

# Run specific test suites
npm run test:e2e:journey1    # Journey 1: Smart Templates
npm run test:e2e:security   # Security tests
npm run test:e2e:performance # Performance tests
npm run test:e2e:api        # API integration tests

# View test results
npm run test:e2e:report
```

## 🧪 Test Categories

### 1. Application Launch Tests (`test-app-launch.spec.ts`)
- Application loading and startup
- Tab navigation functionality
- Responsive design validation
- Session state management

### 2. Journey 1: Smart Templates (`journeys/test-journey1-smart-templates.spec.ts`)
- Basic prompt enhancement with C.R.E.A.T.E. framework
- File upload functionality (TXT, MD, CSV, JSON)
- Model selection and cost tracking
- Copy and export features
- Error handling and edge cases

### 3. Security Tests (`test-security.spec.ts`)
- File upload security (size limits, type validation)
- Malicious content detection
- XSS and injection prevention
- Rate limiting enforcement
- CORS validation

### 4. Performance Tests (`test-performance.spec.ts`)
- Page load performance benchmarks
- API response time validation
- Memory usage monitoring
- Concurrent user handling
- Network condition testing

### 5. API Integration (`test-api-integration.spec.ts`)
- Health check endpoints
- Error handling and recovery
- Authentication flow validation
- External service integration

## 📊 Test Data

### Sample Files (`data/files/`)
- `simple-text.txt` - Basic text file for upload testing
- `test-document.md` - Markdown with formatting and code blocks
- `sample-data.csv` - Employee data for CSV processing tests
- `config-sample.json` - Configuration file for JSON parsing
- `large-content.txt` - Large file for performance testing

### Security Test Files (`data/malicious/`)
- `fake-text-with-script.txt` - Contains XSS attempts and malicious patterns
- `oversized-file.txt` - 15MB file to test size limits

## 🔧 Configuration

### Playwright Configuration (`playwright.config.ts`)

Key settings:
- **Base URL**: `http://localhost:7860`
- **Browsers**: Chrome, Firefox, Safari, Edge, Mobile Chrome/Safari
- **Timeouts**: 60s global, 30s navigation, 10s actions
- **Retries**: 2 on CI, 0 locally
- **Reporters**: HTML, JSON, JUnit for CI integration

### Environment Variables

```bash
# Application ports
PROMPTCRAFT_API_PORT=7862

# Test environment
NODE_ENV=test

# Optional: Enable additional debugging
DEBUG=pw:*
```

## 📈 Success Metrics

### Performance Benchmarks
- **Page Load**: < 5 seconds total, < 3 seconds DOM ready
- **API Response**: < 30 seconds for complex prompts, < 10 seconds for simple
- **File Processing**: < 15 seconds for typical files
- **Memory**: < 50% growth during extended sessions

### Quality Standards
- **Test Coverage**: > 80% of UI interactions
- **Reliability**: < 2% test flakiness
- **Browser Support**: Chrome, Firefox, Safari, Edge
- **Mobile Support**: iOS Safari, Android Chrome
- **Security**: Zero critical vulnerabilities

### Rate Limiting
- **Requests**: 30 per minute, 200 per hour
- **File Uploads**: 50 per hour
- **Concurrent Users**: 5+ simultaneous users supported

## 🛠️ Development Workflow

### Adding New Tests

1. **Create test file**: Follow naming convention `test-[feature].spec.ts`
2. **Use Page Objects**: Extend existing page classes or create new ones
3. **Include test data**: Add sample files to `data/` directories
4. **Add to npm scripts**: Include convenient run commands

### Best Practices

- **Page Object Model**: Use page objects for UI interactions
- **Test Independence**: Each test should be independent and repeatable
- **Descriptive Names**: Test names should clearly describe what they validate
- **Screenshots**: Take screenshots on failures for debugging
- **Performance**: Measure and validate response times

### Debugging Tests

```bash
# Run with browser visible
npm run test:e2e:headed

# Step-by-step debugging
npm run test:e2e:debug

# Generate test code
npm run test:e2e:codegen

# View trace files
npm run test:e2e:trace
```

## 🚨 Troubleshooting

### Common Issues

1. **Application not running**
   ```bash
   # Start PromptCraft application
   poetry run python -m src.main
   ```

2. **Port conflicts**
   - Ensure ports 7860 and 7862 are available
   - Check for other services using these ports

3. **Browser installation**
   ```bash
   # Reinstall browsers
   npm run test:e2e:install
   ```

4. **Test failures**
   - Check test reports: `npm run test:e2e:report`
   - Review screenshots in `test-results/`
   - Check application logs

### Performance Issues

- **Slow tests**: Check network conditions and system resources
- **Timeouts**: Increase timeout values in `playwright.config.ts`
- **Memory**: Monitor system memory during test execution

## 📋 CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: npm ci
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Start application
        run: |
          poetry run python -m src.main &
          sleep 30  # Wait for startup
      - name: Run E2E tests
        run: npm run test:e2e
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: test-results/
```

## 📝 Contributing

1. **Test Coverage**: Ensure new features have corresponding tests
2. **Security**: Include security validation for new functionality
3. **Performance**: Add performance benchmarks for new features
4. **Documentation**: Update this README for new test categories

## 📞 Support

For issues with the testing suite:
- Check existing issues in the repository
- Review test output and screenshots
- Ensure application is running correctly
- Verify browser and system requirements

---

*This comprehensive testing suite ensures PromptCraft-Hybrid meets high standards for functionality, security, and performance across all supported platforms and browsers.*