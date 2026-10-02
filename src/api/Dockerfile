FROM python:3-slim

LABEL org.opencontainers.image.source="https://github.com/MikolajKocik/lex-agent-rpa"
LABEL org.opencontainers.image.description="Lex Agent RPA Microservice"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER root
RUN useradd -m appuser

WORKDIR /app

COPY --chown=appuser:appuser pyproject.toml .
COPY --chown=appuser:appuser src/ .


RUN pip install --no-cache-dir .

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" \
    || exit 1

EXPOSE 8080
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
