# Development Philosophy (MANDATORY)

## Core Principles

### 1. Reuse First

Check existing repositories for solutions BEFORE building:

- **CI/CD & DevOps**: Copy from ledgerbase repository
- **Documentation Templates**: Reuse from FISProject repository
- **GitHub Actions**: Use workflows from .github repository
- **UI Components**: Leverage existing promptcraft_app.py

### 2. Configure, Don't Build

Use existing tools and services instead of custom development:

- **Orchestration**: Use Zen MCP Server instead of custom orchestration
- **Analysis**: Integrate Heimdall MCP Server rather than building analysis tools
- **Security**: Use AssuredOSS packages when available
- **Infrastructure**: Leverage external Qdrant, Ubuntu VM deployment

### 3. Focus on Unique Value

Build ONLY what's truly unique to PromptCraft:

- **Claude.md Generation Logic**: Unique file generation capabilities
- **Prompt Composition Intelligence**: Smart prompt enhancement
- **User Preference Learning**: Personalized AI assistance
- **C.R.E.A.T.E. Framework Implementation**: Structured knowledge methodology

## Mandatory Standards

### Security Requirements

- **Local Encryption**: Use encrypted .env files (following ledgerbase encryption.py pattern)
- **Key Management**: GPG key for encryption, SSH key for signed commits
- **Validation**: Environment MUST validate both keys are present
- **Dependencies**: Use AssuredOSS packages when available
- **No Secrets**: Never commit secrets or keys to repository

### Performance Standards

- **API Response Time**: p95 < 2s for Claude.md generation
- **Memory Usage**: < 2GB per container
- **Test Coverage**: Minimum 80% for all Python code
- **External Dependencies**: Qdrant vector database at 192.168.1.16:6333

### Code Review Checklist

Before submitting any PR, verify:

- [ ] **Reuse Check**: Could this use existing code from ledgerbase/FISProject?
- [ ] **Zen/Heimdall Usage**: Is orchestration done through MCP servers?
- [ ] **Security**: Are secrets in encrypted .env? GPG/SSH keys validated?
- [ ] **Focus**: Does this contribute to unique value (Claude.md generation)?
- [ ] **Naming**: Do all components follow naming conventions?
- [ ] **Knowledge Files**: Do they follow the C.R.E.A.T.E. Framework and style guide?

## Configuration Philosophy

- **External Vector DB**: Use Qdrant on Unraid (192.168.1.16:6333)
- **Ubuntu VM Deployment**: Application services on 192.168.1.205
- **Zen MCP Integration**: ALL orchestration through MCP servers
- **Minimal Cloud Dependencies**: Cost-effective hybrid model
- **Free Mode Support**: Toggle for cost-conscious development
