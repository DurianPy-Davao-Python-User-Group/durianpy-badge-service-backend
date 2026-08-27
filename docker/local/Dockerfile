FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    just \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binary from official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Pre-create config directories in container
RUN mkdir -p /root/.aws /root/.ssh

# Set working directory
WORKDIR /workspace

# Configure environment variables for Python and uv
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH="/workspace/.venv/bin:$PATH"

# Copy dependency manifests first for Docker layer caching
COPY pyproject.toml uv.lock ./

# Install project dependencies (including dev group)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy application source code
COPY . .

# Complete sync to install current package in editable mode
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Keep container alive without automatically launching background services
CMD ["sleep", "infinity"]
