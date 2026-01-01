# Multi-stage build for Screen Party server
FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy workspace configuration
COPY pyproject.toml uv.lock* ./

# Copy all packages
COPY common/ ./common/
COPY server/ ./server/

# Install dependencies (only server + common)
RUN uv sync --frozen --no-dev --no-install-project --package screen-party-server

# Production stage
FROM python:3.13-slim

WORKDIR /app

# Copy uv from builder
COPY --from=builder /bin/uv /bin/uv
COPY --from=builder /bin/uvx /bin/uvx

# Copy installed packages and project files
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/common /app/common
COPY --from=builder /app/server /app/server
COPY --from=builder /app/pyproject.toml /app/pyproject.toml

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/server/src:/app/common/src"
ENV SERVER_HOST="0.0.0.0"
ENV SERVER_PORT="8765"

# Expose server port
EXPOSE 8765

# Run server
CMD ["python", "-m", "screen_party_server.server"]
