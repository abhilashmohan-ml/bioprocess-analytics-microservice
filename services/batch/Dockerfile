FROM python:3.13-slim

# ===================================================================
# 🕵️  Universal OS dependencies
# ===================================================================
COPY detect-and-install.sh /tmp/detect-and-install.sh
RUN chmod +x /tmp/detect-and-install.sh && \
    /tmp/detect-and-install.sh docker-deps && \
    rm /tmp/detect-and-install.sh

# ===================================================================
# 🐍  Python & app
# ===================================================================
WORKDIR /app

# 1.  requirements layer (cached)
COPY services/batch/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 2.  application code
COPY services/batch/ ./batch_service/
COPY shared/        ./shared/
RUN chmod 755 /app

# 3.  non-root user + permissions (🔥 critical fix)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod 755 /app                 # allow traversal

# 4.  runtime user
USER appuser

ENV PYTHONPATH=/app:/app/shared

# 5.  health check (runs as appuser)
HEALTHCHECK --interval=30s --timeout=15s --start-period=15s --retries=10 \
  CMD python -c \
  "import sys, requests, batch_service.app.main as m; \
   print('✅ module imported'); \
   r = requests.get('http://localhost:9003/healthz', timeout=5); \
   r.raise_for_status(); \
   print('✅ health OK')"

# 6.  start
CMD ["uvicorn", "batch_service.app.main:app", \
     "--host", "0.0.0.0", "--port", "9003", "--workers", "1"]