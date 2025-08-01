# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and config
COPY src ./src
COPY config ./config

# Create non-root user and adjust permissions
RUN groupadd -r infra && useradd -r -g infra infra && chown -R infra:infra /app

ENV PYTHONPATH=/app/src
EXPOSE 8000

USER infra

ENTRYPOINT ["python", "-m", "infra_cli.main"]
CMD ["--help"]
