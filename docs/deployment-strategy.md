# Documentation Deployment Strategy

This project uses a dual-environment documentation deployment strategy to support both development preview
and production-ready documentation.

## Deployment Environments

### Development Environment

- **Trigger**: Push to `feature/phase-1-development` branch
- **Workflow**: `.github/workflows/deploy-docs.yml`
- **Environment**: `development`
- **Build Mode**: Lenient (allows broken links)
- **Purpose**: Preview documentation changes during development
- **Concurrency**: Cancels previous builds to ensure latest changes

### Production Environment

- **Trigger**: Push to `main` branch
- **Workflow**: `.github/workflows/deploy-docs-production.yml`
- **Environment**: `github-pages`
- **Build Mode**: Strict (fails on warnings)
- **Purpose**: Stable, high-quality documentation for releases
- **Concurrency**: Queue builds to prevent conflicts

## GitHub Pages Configuration

To enable both environments:

1. **Repository Settings**:
   - Go to Settings → Pages
   - Set Source to "GitHub Actions"

2. **Environment Protection** (Recommended):
   - Go to Settings → Environments
   - Create `development` environment (no protection rules)
   - Create `github-pages` environment with protection rules:
     - Required reviewers for production deployments
     - Deployment branch restrictions to `main` only

## Workflow Features

### Development Workflow

- ✅ Fast feedback on documentation changes
- ✅ Allows broken links during development
- ✅ Cancels previous builds for efficiency
- ✅ Clear labeling as development preview

### Production Workflow

- ✅ Strict quality checks (fails on warnings)
- ✅ Stable deployment from main branch
- ✅ Environment protection for safety
- ✅ Full build validation

## Usage

### For Development

1. Push changes to `feature/phase-1-development`
2. Documentation automatically deploys with development preview
3. Check deployment URL in Actions output

### For Production

1. Merge changes to `main` branch
2. Production documentation builds with strict validation
3. Deploys to primary GitHub Pages URL

## Benefits

- **Continuous Preview**: See documentation changes immediately
- **Quality Gates**: Production requires all warnings resolved
- **Branch Strategy**: Supports feature → development → main workflow
- **Environment Safety**: Production protected from accidental deployments
- **Single Pages Site**: Uses GitHub's free Pages allocation efficiently
