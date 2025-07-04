# PromptCraft-Hybrid: CI/CD Pipeline Architecture

Version: 2.1
Status: Defined
Audience: Developers, DevOps, Architects

## 1\. Introduction & Philosophy

This document outlines the Continuous Integration (CI) and Continuous Deployment (CD) pipeline for the PromptCraft-Hybrid project. Our philosophy is to create a secure, automated "assembly line" for our code. Every change is subjected to a rigorous set of automated quality and security gates, ensuring that what we deploy is reliable, safe, and high-quality. This pipeline integrates our specific suite of GitHub applications to provide comprehensive feedback directly within the development workflow.

## 2\. The Developer Experience: Automated Checks

When a developer opens a Pull Request, they will see a series of automated checks. A PR is not considered ready for human review until these automated checks are passing.

**Key Integrated Checks on Pull Requests:**

* **Aikido PR Checks:** Provides a unified view of security issues.
* **Codecov:** Reports on unit test coverage.
* **GitGuardian:** Scans for inadvertently committed secrets.
* **Semgrep:** Performs deep static code analysis.
* **GitHub Actions:** Runs our custom validation jobs.

## 3\. Stage 1: Continuous Integration (CI) Workflow

This workflow runs on every pull request targeting the develop branch. It is a mandatory quality gate.

### GitHub Actions Workflow: .github/workflows/ci.yml

#### Job 1: Lint & Test

* **Purpose:** Ensures code style consistency and functional correctness.
* **Steps:**
  1. Checkout Code & Setup Environment.
  2. Install Dependencies (poetry install, npm install).
  3. Lint Code (black, ruff, eslint).
  4. Run Unit Tests (pytest \--cov).
  5. Upload Coverage to Codecov using codecov/codecov-action@v4.

#### Job 2: Comprehensive Security Scan

* **Purpose:** To identify security vulnerabilities *before* merge. Runs in parallel to "Lint & Test".
* **Steps:**
  1. Checkout Code.
  2. **Secrets Scan:** Run GitGuardian/ggshield-action@v1.
  3. **Static Application Security Testing (SAST):** Run semgrep/semgrep-action@v2.
  4. **Software Composition Analysis (SCA):** Run the **Aikido Security** action to scan dependencies.
  5. **Harden Runner:** Wrap jobs with step-security/harden-runner@v2 to secure the pipeline itself.

#### Job 3: Build & Scan Docker Images

* **Purpose:** Ensures services are containerizable and free of known OS-level vulnerabilities. Depends on the success of "Lint & Test".
* **Steps:**
  1. Checkout Code.
  2. Login to GitHub Container Registry (GHCR).
  3. For each service in docker-compose.yml:
     a. Build the Docker image.
     b. Scan Image: Use a tool like Trivy or Aikido's container scanning to scan the newly built image for OS vulnerabilities. The job will fail if any Critical vulnerabilities are found.
     c. Push Image: If the scan passes, push the image to GHCR, tagged with the Git SHA.

## 4\. Vulnerability Triage & Management Policy

The security scans integrated into our CI pipeline are a critical line of defense. The following policy dictates how findings must be handled before a PR can be merged.

* **Critical/High Findings:** Any Critical or High severity vulnerability found by GitGuardian, Semgrep, or Aikido during the CI run **MUST be fixed within the PR** before it can be merged. There are no exceptions.
* **Medium/Low Findings:** Medium or Low severity findings can, at the human reviewer's discretion, be addressed by creating a new, properly triaged issue in the project backlog. The PR can be approved as long as the new issue is created and linked in the PR comments.

## 5\. Stage 2: Deploy to Staging

This workflow is triggered automatically upon a successful merge to the develop branch.

* **Process:** An automated workflow deploys the newly built and scanned images to the staging environment.
* **Post-Deployment Integration:** The deployed services are configured with the **Sentry Staging DSN** to immediately start capturing errors and performance data in a non-production environment.

## 6\. Stage 3: Release to Production

This workflow is triggered **manually** via a workflow\_dispatch event on the main branch, providing a crucial human approval gate.

### 6.1. Deployment Job

* **Environment:** Uses GitHub Environments with a required manual approval step.
* **Runner:** Runs on a protected, self-hosted runner with access to the production server.

### 6.2. Automated Deployment Process

1. **Approval Gate:** The workflow pauses until a designated approver clicks "Approve" in the GitHub Actions UI.
2. **Tag Release:** Creates a new Git tag (e.g., v1.2.0) to mark the release point.
3. **Connect to Production Server:** Uses SSH with protected secrets.
4. **Programmatic Update:** A script (e.g., using sed or yq) programmatically updates the image: tag in the docker-compose.prod.yml file to the specific Git SHA tag of the image validated in staging.
5. **Restart Services:** Runs docker compose \-f docker-compose.prod.yml up \-d to restart the application stack.

### 6.3. Post-Deployment Health Check & Automated Rollback

This is our most important operational safety net.

1. **Health Check:** After the docker compose up command, the workflow pauses for 30-60 seconds, then executes a health check script. This script hits a /health endpoint on each critical service.
2. **Automated Rollback:** If any health check fails (returns a non-200 status code), the workflow **immediately triggers a rollback**. The rollback script re-applies the *previous* known-good docker-compose.prod.yml configuration and restarts the services.
3. **Alerting:** A failed health check and subsequent rollback **must** immediately trigger a high-priority alert in the designated Sentry and Slack channels, notifying the on-call team of the failed deployment.

## 7\. Continuous Dependency Management with Renovate

**Renovate** runs on a schedule to keep our dependencies up-to-date.

* **Process:** Renovate opens PRs for outdated dependencies. These PRs are subjected to the full CI workflow.
* **Policy:**
  * PRs for **minor and patch** version updates that pass all CI checks can be merged by developers after a quick review of the changelog.
  * PRs for **major** version updates **cannot be auto-merged**. They require a detailed manual review for breaking changes and must be handled with the same rigor as a new feature.
