import time
from fastapi import Request, Response
from prometheus_client import (
    Counter,
    Histogram,
    Summary,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# HTTP metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests handled by the API",
    ["method", "handler", "status"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency histogram in seconds",
    ["method", "handler"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Agent metrics
LAR_AGENT_EXECUTION_SECONDS = Summary(
    "lar_agent_execution_seconds",
    "Time spent executing an autonomous agent task in seconds"
)

LAR_LLM_REQUESTS_TOTAL = Counter(
    "lar_llm_requests_total",
    "Total LLM calls categorized by status code or result",
    ["model", "status"]
)

LAR_AGENT_TOOL_CALLS_TOTAL = Counter(
    "lar_agent_tool_calls_total",
    "Total agent tool executions categorized by tool name and status",
    ["tool_name", "status"]
)

LAR_LLM_TOKENS_TOTAL = Counter(
    "lar_llm_tokens_total",
    "Total tokens consumed by LLM calls categorized by model and token type (input/output)",
    ["model", "type"]
)


def setup_metrics(app):
    """Rejestruje middleware oraz endpoint /metrics w aplikacji FastAPI."""
    
    @app.middleware("http")
    async def prometheus_middleware(request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.perf_counter() - start_time
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method, handler=request.url.path, status=str(status_code)
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method, handler=request.url.path
            ).observe(duration)

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
