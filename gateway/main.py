"""
Gateway (reverse-proxy) for the bioprocess-analytics-micro stack.
Runs on port 8080.
"""

from fastapi import FastAPI, Request, Response
import httpx

app = FastAPI(title="API Gateway", version="1.0.0", docs_url="/docs")

SERVICE_MAP = {
    "/auth": "http://auth:9001",
    "/users": "http://user:9002",
    "/batches": "http://batch:9003",
    "/qc-batches": "http://batch:9003",
}

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def gateway_proxy(request: Request, full_path: str) -> Response:
    segments = full_path.split("/", 1)
    prefix = "/" + segments[0]
    backend = SERVICE_MAP.get(prefix)
    if not backend:
        return Response(status_code=404, content="No such service")

    path_remain = "" if len(segments) == 1 else segments[1]
    upstream_url = f"{backend}/{path_remain}"

    async with httpx.AsyncClient(timeout=30) as client:
        upstream_resp = await client.request(
            request.method,
            upstream_url,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            params=request.query_params,
            content=await request.body(),
        )

    return Response(
        status_code=upstream_resp.status_code,
        content=upstream_resp.content,
        headers={k: v for k, v in upstream_resp.headers.items() if k.lower() != "content-encoding"},
    )