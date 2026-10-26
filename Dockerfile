# syntax=docker/dockerfile:1
#   docker build -t loanlab:dev .
#   docker run --rm -p 5080:5080 loanlab:dev

# ---- build stage: wheels only; compilers never reach the final image ----
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---- runtime stage ----
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DATABASE_URL=sqlite:////tmp/loanlab.sqlite3

RUN groupadd --system app && useradd --system --gid app --no-create-home app
WORKDIR /app

# dependencies first: this layer stays cached until requirements.txt changes
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# application code last: it changes on every commit
COPY --chown=app:app loanlab ./loanlab

USER app
EXPOSE 5080

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5080/api/health', timeout=2).status == 200 else 1)"

# --preload: build the app (create tables, seed) once, then fork the workers.
# --worker-tmp-dir: gunicorn needs a writable directory; the root filesystem is read-only in k8s.
CMD ["gunicorn", "loanlab.api:create_app()", "--preload", "--bind", "0.0.0.0:5080", \
     "--workers", "2", "--threads", "4", "--worker-tmp-dir", "/dev/shm", \
     "--graceful-timeout", "20", "--access-logfile", "-"]
