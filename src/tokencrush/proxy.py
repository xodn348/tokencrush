"""OpenAI and Anthropic compatible proxy server with semantic caching and prompt compression."""

import json
import logging
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

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
compressor = None  # Lazy initialization to avoid segfault on startup


def get_openai_target(request: Request) -> str:
    """Get target OpenAI API URL."""
    target = request.headers.get("X-TokenCrush-Target")
    if target:
        return target.rstrip("/")
    return "https://api.openai.com"


def get_anthropic_target(request: Request) -> str:
    """Get target Anthropic API URL."""
    target = request.headers.get("X-TokenCrush-Target")
    if target:
        return target.rstrip("/")
    return "https://api.anthropic.com"


def create_cache_key(messages: list, model: str = "") -> str:
    """Create cache key from messages array."""
    return json.dumps({"model": model, "messages": messages}, sort_keys=True)


def extract_messages(body: Dict[str, Any]) -> list:
    """Extract messages from request body."""
    return body.get("messages", [])


def get_compressor():
    """Lazy load compressor to avoid segfault on startup."""
    global compressor
    if compressor is None:
        compressor = TokenCompressor()
    return compressor


def compress_last_user_message(
    messages: list, rate: float = 0.5, enable_compression: bool = True
) -> tuple[list, Optional[float]]:
    """Compress the last user message in the messages array."""
    if not messages or not enable_compression:
        return messages, None

    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            content = messages[i].get("content", "")
            # Handle string content
            if isinstance(content, str) and len(content) > 100:
                try:
                    comp = get_compressor()
                    result = comp.compress(content, rate=rate)
                    messages[i]["content"] = result.compressed_text
                    return messages, result.ratio
                except Exception:
                    return messages, None
            # Handle list content (Anthropic format)
            elif isinstance(content, list):
                for j, block in enumerate(content):
                    if block.get("type") == "text" and len(block.get("text", "")) > 100:
                        try:
                            comp = get_compressor()
                            result = comp.compress(block["text"], rate=rate)
                            messages[i]["content"][j]["text"] = result.compressed_text
                            return messages, result.ratio
                        except Exception:
                            return messages, None
            break

    return messages, None


async def forward_request(
    target_url: str,
    path: str,
    method: str,
    headers: Dict[str, str],
    body: Optional[Dict[str, Any]] = None,
) -> httpx.Response:
    """Forward request to target API."""
    url = f"{target_url}{path}"

    forward_headers = {
        k: v
        for k, v in headers.items()
        if k.lower() not in ["host", "content-length", "x-tokencrush-target"]
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        if method == "GET":
            response = await client.get(url, headers=forward_headers)
        elif method == "POST":
            response = await client.post(url, headers=forward_headers, json=body)
        else:
            raise HTTPException(status_code=405, detail="Method not allowed")

        return response


# ============== OpenAI Endpoints ==============

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """OpenAI-compatible chat completions endpoint with caching and compression."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    messages = extract_messages(body)
    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    model = body.get("model", "")
    cache_key = create_cache_key(messages, model)
    cached_response = cache.get(cache_key)

    if cached_response:
        try:
            response_data = json.loads(cached_response)
            logger.info("Cache HIT for OpenAI request")
            return JSONResponse(
                content=response_data,
                headers={"x-tokencrush-cache": "hit"},
            )
        except Exception:
            pass

    enable_compression = body.pop("enable_compression", True)
    compression_rate = body.pop("compression_rate", 0.5)
    modified_messages, compression_ratio = compress_last_user_message(
        messages.copy(), rate=compression_rate, enable_compression=enable_compression
    )

    body["messages"] = modified_messages

    target_url = get_openai_target(request)
    logger.info(f"Forwarding OpenAI request to {target_url}")

    try:
        response = await forward_request(
            target_url=target_url,
            path="/v1/chat/completions",
            method="POST",
            headers=dict(request.headers),
            body=body,
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Gateway timeout")
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Bad gateway: {str(e)}")

    if response.status_code != 200:
        try:
            error_content = response.json() if response.content else {"error": "Unknown error"}
        except Exception:
            error_content = {"error": response.text or "Unknown error"}
        return JSONResponse(content=error_content, status_code=response.status_code)

    try:
        response_data = response.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Invalid JSON from target API: {str(e)}")

    cache.set(cache_key, json.dumps(response_data))
    logger.info("Cache MISS - stored OpenAI response")

    return JSONResponse(
        content=response_data,
        headers={"x-tokencrush-cache": "miss"},
    )


@app.get("/v1/models")
async def list_models(request: Request):
    """Forward model listing to target API."""
    target_url = get_openai_target(request)

    try:
        response = await forward_request(
            target_url=target_url,
            path="/v1/models",
            method="GET",
            headers=dict(request.headers),
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Bad gateway: {str(e)}")

    return JSONResponse(
        content=response.json() if response.content else {"data": []},
        status_code=response.status_code,
    )


# ============== Anthropic Endpoints ==============

@app.post("/v1/messages")
async def anthropic_messages(request: Request):
    """Anthropic-compatible messages endpoint with caching and compression."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    messages = extract_messages(body)
    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    model = body.get("model", "")
    cache_key = create_cache_key(messages, model)
    cached_response = cache.get(cache_key)

    if cached_response:
        try:
            response_data = json.loads(cached_response)
            logger.info("Cache HIT for Anthropic request")
            return JSONResponse(
                content=response_data,
                headers={"x-tokencrush-cache": "hit"},
            )
        except Exception:
            pass

    # Compress messages
    modified_messages, compression_ratio = compress_last_user_message(
        messages.copy(), rate=0.5, enable_compression=True
    )
    body["messages"] = modified_messages

    target_url = get_anthropic_target(request)
    logger.info(f"Forwarding Anthropic request to {target_url}")

    try:
        response = await forward_request(
            target_url=target_url,
            path="/v1/messages",
            method="POST",
            headers=dict(request.headers),
            body=body,
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Gateway timeout")
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Bad gateway: {str(e)}")

    if response.status_code != 200:
        try:
            error_content = response.json() if response.content else {"error": "Unknown error"}
        except Exception:
            error_content = {"error": response.text or "Unknown error"}
        return JSONResponse(content=error_content, status_code=response.status_code)

    try:
        response_data = response.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Invalid JSON from target API: {str(e)}")

    cache.set(cache_key, json.dumps(response_data))
    logger.info("Cache MISS - stored Anthropic response")

    return JSONResponse(
        content=response_data,
        headers={"x-tokencrush-cache": "miss"},
    )


# ============== Common Endpoints ==============

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "tokencrush-proxy"}


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "TokenCrush Proxy",
        "version": "0.2.0",
        "endpoints": {
            "openai_chat": "/v1/chat/completions",
            "openai_models": "/v1/models",
            "anthropic_messages": "/v1/messages",
            "health": "/health",
        },
    }
