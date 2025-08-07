from fastapi import FastAPI, Request
import httpx

app = FastAPI(title="API Gateway", docs_url="/docs")

SERVICE_MAP = {
    "/auth": "http://auth:9001",
    "/users": "http://user:9002",
    "/batches": "http://batch:9003",
    "/qc-batches": "http://batch:9003",
}

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(full_path: str, request: Request):
    segments = full_path.split("/")
    prefix = "/" + segments[0]
    backend = SERVICE_MAP.get(prefix)
    if not backend:
        return {"error": "No such service"}, 404
    url = backend + ("" if full_path == prefix else "/" + "/".join(segments[1:]))
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            request.method, url,
            headers={k: v for k, v in request.headers.items() if k != "host"},
            content=await request.body()
        )
    return resp.json()
