# PromptCraft Development Container
# Optimized for Codespaces prebuilds and development workflow

FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Set environment variables for Poetry and Python
ENV POETRY_VERSION=2.1.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    POETRY_VENV_IN_PROJECT=true \
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

# Switch to promptcraft user for Poetry installation
USER promptcraft

# Install Poetry as promptcraft user
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    echo 'export PATH="/home/promptcraft/.local/bin:$PATH"' >> ~/.bashrc

# Set PATH for current session and configure Poetry
ENV PATH="/home/promptcraft/.local/bin:$PATH"
RUN poetry config virtualenvs.create true && \
    poetry config virtualenvs.in-project true && \
    poetry config installer.parallel true

# Set working directory
WORKDIR /workspace

# Copy Poetry configuration files (for dependency caching in prebuilds)
COPY --chown=promptcraft:promptcraft pyproject.toml poetry.lock ./

# Install dependencies (this layer is cached in prebuilds)
RUN poetry install --sync --no-interaction && \
    rm -rf $POETRY_CACHE_DIR

# Install pre-commit hooks (also cached in prebuilds)
RUN poetry run pre-commit install-hooks || true

# Install additional development tools via Poetry
RUN poetry self add poetry-plugin-export

# Set up development environment indicators
RUN echo "✅ PromptCraft development environment prepared" > /home/promptcraft/.prebuild-ready

# Default command for development
CMD ["bash"]
