# PromptCraft Development Container
# Optimized for Codespaces prebuilds and development workflow.

FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Bring in uv from its official image to avoid maintaining a custom installer.
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /usr/local/bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for PromptCraft.
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

# Create promptcraft user matching container expectations.
RUN groupadd -r promptcraft && \
    useradd -r -g promptcraft -u 1000 -m -s /bin/bash promptcraft && \
    mkdir -p /opt/venv && \
    chown -R promptcraft:promptcraft /opt/venv

USER promptcraft
WORKDIR /workspace

# Copy lockfile inputs first so this layer caches in prebuilds.
COPY --chown=promptcraft:promptcraft pyproject.toml uv.lock ./

# Install all dependencies including dev groups, install pre-commit hooks,
# and drop a marker that prebuilds completed.
RUN uv sync --frozen --all-groups && \
    (uv run --frozen pre-commit install-hooks || true) && \
    echo "PromptCraft development environment prepared" > /home/promptcraft/.prebuild-ready

CMD ["bash"]
