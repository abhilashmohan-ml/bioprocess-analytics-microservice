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

# 1.  requirements  (cache layer)
COPY services/auth/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 2.  code
COPY services/auth/ ./auth_service/
COPY shared/        ./shared/
RUN chmod 755 /app

# 3.  permissions  ⬅  NEW:  allow traversal
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod 755 /app              # ← critical: appuser can ENTER /app

# 4.  runtime user
USER appuser

ENV PYTHONPATH=/app:/app/shared

# 5.  health check  (runs as appuser)
HEALTHCHECK --interval=30s --timeout=15s --start-period=15s --retries=10 \
  CMD python -c \
  "import sys, requests, auth_service.app.main as m; \
   print('✅ module imported'); \
   r = requests.get('http://localhost:9001/healthz', timeout=5); \
   r.raise_for_status(); \
   print('✅ health OK')"

# 6.  start
CMD ["uvicorn", "auth_service.app.main:app", \
     "--host", "0.0.0.0", "--port", "9001", "--workers", "1"]