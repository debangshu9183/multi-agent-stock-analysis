FROM python:3.13-slim

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for Docker layer caching
COPY pyproject.toml uv.lock* ./

# Install dependencies (no dev dependencies)
RUN uv sync --frozen --no-dev

# Copy application code
COPY main.py .
COPY database.py .
COPY tools/ ./tools/
COPY agents/ ./agents/
COPY tasks/ ./tasks/
COPY frontend/ ./frontend/

# Create CrewAI storage directory
RUN mkdir -p /app/crewai_storage

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
