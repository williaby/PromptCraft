# PromptCraft Development Container
# Optimized for Codespaces prebuilds and development workflow

FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Set environment variables for uv and Python
ENV UV_VERSION=0.8.17 \
    UV_PROJECT_ENVIRONMENT=/workspace/.venv \
    UV_CACHE_DIR=/tmp/uv_cache \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for PromptCraft
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    redis-server \
    libmagic-dev \
    markdownlint-cli \
    yamllint \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create promptcraft user matching container expectations
RUN groupadd -r promptcraft && \
    useradd -r -g promptcraft -u 1000 -m -s /bin/bash promptcraft && \
    mkdir -p /opt/venv && \
    chown -R promptcraft:promptcraft /opt/venv

# Switch to promptcraft user for uv installation
USER promptcraft

# Install uv as promptcraft user
RUN curl -LsSf https://astral.sh/uv/${UV_VERSION}/install.sh | sh && \
    echo 'export PATH="/home/promptcraft/.local/bin:$PATH"' >> ~/.bashrc

# Set PATH for current session
ENV PATH="/home/promptcraft/.local/bin:$PATH"

# Set working directory
WORKDIR /workspace

# Copy project configuration files (for dependency caching in prebuilds)
COPY --chown=promptcraft:promptcraft pyproject.toml uv.lock ./

# Install dependencies (this layer is cached in prebuilds)
RUN uv sync --frozen --no-install-project && \
    rm -rf $UV_CACHE_DIR

# Install pre-commit hooks (also cached in prebuilds)
RUN uv run --frozen pre-commit install-hooks || true

# Set up development environment indicators
RUN echo "✅ PromptCraft development environment prepared" > /home/promptcraft/.prebuild-ready

# Default command for development
CMD ["bash"]
