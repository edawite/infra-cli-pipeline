FROM python:3.11-slim

LABEL maintainer="infra-cli-pipeline developers"

# Install dependencies
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src ./src
COPY config ./config

# Create a non‑root user to run the application
RUN groupadd -r infra && useradd --no-log-init -r -g infra infra \
    && chown -R infra:infra /app

USER infra

ENV PYTHONPATH=/app/src

# Expose metrics port (configurable via YAML)
EXPOSE 8000

ENTRYPOINT ["python", "-m", "infra_cli.main"]
CMD ["--help"]