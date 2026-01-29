"""OpenAI and Anthropic compatible proxy server with semantic caching and prompt compression."""

import json
import logging
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from tokencrush.cache import SemanticCache
from tokencrush.compressor import TokenCompressor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TokenCrush Proxy",
    description="OpenAI and Anthropic compatible proxy with semantic caching and prompt compression",
    version="0.2.0",
)

cache = SemanticCache()
compressor = None


def get_compressor():
    """Lazy load compressor."""
    global compressor
    if compressor is None:
        compressor = TokenCompressor()
    return compressor


def create_cache_key(messages: list, model: str = "") -> str:
    """Create cache key from messages array."""
    return json.dumps({"model": model, "messages": messages}, sort_keys=True)


def compress_messages(messages: list, rate: float = 0.5) -> tuple[list, Optional[float]]:
    """Compress user messages."""
    if not messages:
        return messages, None

    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            content = messages[i].get("content", "")
            if isinstance(content, str) and len(content) > 100:
                try:
                    result = get_compressor().compress(content, rate=rate)
                    messages[i]["content"] = result.compressed_text
                    return messages, result.ratio
                except Exception:
                    pass
            elif isinstance(content, list):
                for j, block in enumerate(content):
                    if block.get("type") == "text" and len(block.get("text", "")) > 100:
                        try:
                            result = get_compressor().compress(block["text"], rate=rate)
                            messages[i]["content"][j]["text"] = result.compressed_text
                            return messages, result.ratio
                        except Exception:
                            pass
            break
    return messages, None


async def forward_to_api(
    target_url: str,
    path: str,
    method: str,
    headers: Dict[str, str],
    body: Optional[Dict[str, Any]] = None,
) -> httpx.Response:
    """Forward request to target API."""
    url = f"{target_url}{path}"
    
    forward_headers = {
        k: v for k, v in headers.items()
        if k.lower() not in ["host", "content-length", "transfer-encoding"]
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        if method == "GET":
            return await client.get(url, headers=forward_headers)
        elif method == "POST":
            return await client.post(url, headers=forward_headers, json=body)
        else:
            return await client.request(method, url, headers=forward_headers, json=body)


# ============== OpenAI Endpoints ==============

@app.post("/v1/chat/completions")
async def openai_chat(request: Request):
    """OpenAI chat completions with caching."""
    body = await request.json()
    messages = body.get("messages", [])
    model = body.get("model", "")
    
    # Check cache
    cache_key = create_cache_key(messages, model)
    cached = cache.get(cache_key)
    if cached:
        logger.info("OpenAI Cache HIT")
        return JSONResponse(json.loads(cached), headers={"x-tokencrush-cache": "hit"})
    
    # Compress and forward
    body["messages"], _ = compress_messages(messages.copy())
    
    response = await forward_to_api(
        "https://api.openai.com",
        "/v1/chat/completions",
        "POST",
        dict(request.headers),
        body
    )
    
    if response.status_code == 200:
        data = response.json()
        cache.set(cache_key, json.dumps(data))
        logger.info("OpenAI Cache MISS - stored")
        return JSONResponse(data, headers={"x-tokencrush-cache": "miss"})
    
    return JSONResponse(response.json(), status_code=response.status_code)


@app.get("/v1/models")
async def openai_models(request: Request):
    """Forward to OpenAI models endpoint."""
    response = await forward_to_api(
        "https://api.openai.com",
        "/v1/models",
        "GET",
        dict(request.headers)
    )
    return JSONResponse(response.json(), status_code=response.status_code)


# ============== Anthropic Endpoints ==============

@app.post("/v1/messages")
async def anthropic_messages(request: Request):
    """Anthropic messages with caching."""
    body = await request.json()
    messages = body.get("messages", [])
    model = body.get("model", "")
    
    # Check cache
    cache_key = create_cache_key(messages, model)
    cached = cache.get(cache_key)
    if cached:
        logger.info("Anthropic Cache HIT")
        return JSONResponse(json.loads(cached), headers={"x-tokencrush-cache": "hit"})
    
    # Compress and forward
    body["messages"], _ = compress_messages(messages.copy())
    
    response = await forward_to_api(
        "https://api.anthropic.com",
        "/v1/messages",
        "POST",
        dict(request.headers),
        body
    )
    
    if response.status_code == 200:
        data = response.json()
        cache.set(cache_key, json.dumps(data))
        logger.info("Anthropic Cache MISS - stored")
        return JSONResponse(data, headers={"x-tokencrush-cache": "miss"})
    
    return JSONResponse(response.json(), status_code=response.status_code)


# Also handle without /v1/ prefix (some SDKs use this)
@app.post("/messages")
async def anthropic_messages_alt(request: Request):
    """Anthropic messages (alternate path)."""
    return await anthropic_messages(request)


# ============== Catch-All for Unknown Endpoints ==============

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(request: Request, path: str):
    """Forward unknown requests to appropriate API."""
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except:
            pass
    
    # Determine target based on headers or path
    auth_header = request.headers.get("authorization", "")
    anthropic_key = request.headers.get("x-api-key", "")
    
    if anthropic_key or "anthropic" in path.lower():
        target = "https://api.anthropic.com"
    else:
        target = "https://api.openai.com"
    
    logger.info(f"Catch-all: {request.method} /{path} -> {target}")
    
    response = await forward_to_api(
        target,
        f"/{path}",
        request.method,
        dict(request.headers),
        body
    )
    
    try:
        return JSONResponse(response.json(), status_code=response.status_code)
    except:
        return JSONResponse({"raw": response.text}, status_code=response.status_code)


# ============== Health ==============

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "tokencrush-proxy"}
