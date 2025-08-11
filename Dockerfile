# Multi-stage build for TutorialMaker
FROM python:3.9-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.9-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /home/app/.local

# Copy application code
COPY . .

# Set ownership and permissions
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Make sure scripts in .local are usable
ENV PATH=/home/app/.local/bin:$PATH

# Expose default port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/api/status')" || exit 1

# Default command
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "5000"]