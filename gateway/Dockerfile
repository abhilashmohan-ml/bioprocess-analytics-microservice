FROM python:3.13-slim

# ===================================================================
# 🕵️ UNIVERSAL SYSTEM DEPENDENCIES (from root context)
# ===================================================================

# Copy from root build context (now accessible!)
COPY detect-and-install.sh /tmp/detect-and-install.sh
RUN chmod +x /tmp/detect-and-install.sh && \
    /tmp/detect-and-install.sh docker-deps && \
    rm /tmp/detect-and-install.sh

# ===================================================================
# 🐍 PYTHON & APPLICATION SETUP
# ===================================================================

# Set work directory
WORKDIR /app/gateway

# Copy requirements first for better caching
COPY gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY gateway/ .
COPY shared/ /app/shared/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]