from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, status, HTTPException, Response
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient, TimeoutException, ConnectError, HTTPStatusError
from starlette.middleware.authentication import AuthenticationMiddleware
from middlewares.auth import AuthMiddleware

SERVICES = {}
CLIENT = AsyncClient()
@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await CLIENT.aclose()
app = FastAPI(lifespan=lifespan)

middlewares: set = {
    HTTPSRedirectMiddleware,
    (CORSMiddleware, {
        "allow_origins": ("*",),
        "allow_methods": ("*",),
        "allow_headers": ("*",),
        "allow_credentials": True,
    }),
    (AuthenticationMiddleware, {"backend": AuthMiddleware})
}
for middleware in middlewares:
    if isinstance(middleware, tuple):
        app.add_middleware(middleware[0], **middleware[1])
    else:
        app.add_middleware(middleware)

@app.get("/health-check")
async def health_check():
    """
    Health check endpoint to confirm the gateway is running.
    """
    return {"status": "API Gateway is running!"}

@app.api_route('/{service}/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
async def forward_request(service: str, path: str, request: Request):
    """
    Forward a request.
    :param service: endpoint wrapper
    :param path: path to endpoint
    :param request: request object needs to forward
    :return: response from endpoint
    """
    if service not in SERVICES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service {service} not found")
    url = f"{SERVICES[service]}/{path}"
    headers = request.headers
    method = request.method
    body = await request.body()
    client = AsyncClient()
    try:
        response = await client.request(method=method,
                                        url=url,
                                        headers=headers,
                                        content=body,
                                        params=request.query_params)
        return Response(content=response.content, status_code=response.status_code, headers=response.headers)
    except ConnectError as ct:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(ct))
    except TimeoutException as te:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(te))
    except HTTPStatusError as se:
        raise HTTPException(status_code=se.response.status_code, detail=str(se))

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)