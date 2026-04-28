FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY finra/ ./finra/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create data directories
RUN mkdir -p /app/data/{filings,reports,cache,vectorstore}

# CLI entrypoint
ENTRYPOINT ["python", "-m", "finra.cli"]
CMD ["--help"]
