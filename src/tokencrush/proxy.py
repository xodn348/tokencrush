"""OpenAI-compatible proxy server with semantic caching and prompt compression."""

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
    description="OpenAI-compatible proxy with semantic caching and prompt compression",
    version="0.1.0",
)

cache = SemanticCache()
compressor = None  # Lazy initialization to avoid segfault on startup


def get_target_api(request: Request) -> str:
    """Get target API URL from header or environment variable."""
    target = request.headers.get("X-TokenCrush-Target")
    if target:
        return target.rstrip("/")

    target = os.getenv("OPENAI_API_BASE")
    if target:
        return target.rstrip("/")

    return "https://api.openai.com"


def create_cache_key(messages: list) -> str:
    """Create cache key from messages array."""
    return json.dumps(messages, sort_keys=True)


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
    """Compress the last user message in the messages array.

    Returns:
        Tuple of (modified_messages, compression_ratio)
    """
    if not messages or not enable_compression:
        return messages, None

    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            content = messages[i].get("content", "")
            if content:
                try:
                    comp = get_compressor()
                    result = comp.compress(content, rate=rate)
                    messages[i]["content"] = result.compressed_text
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

    async with httpx.AsyncClient(timeout=60.0) as client:
        if method == "GET":
            response = await client.get(url, headers=forward_headers)
        elif method == "POST":
            response = await client.post(url, headers=forward_headers, json=body)
        else:
            raise HTTPException(status_code=405, detail="Method not allowed")

        return response


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

    cache_key = create_cache_key(messages)
    cached_response = cache.get(cache_key)

    if cached_response:
        try:
            response_data = json.loads(cached_response)
            return JSONResponse(
                content=response_data,
                headers={
                    "x-tokencrush-cache": "hit",
                    "x-tokencrush-compression-ratio": "0.0",
                    "x-tokencrush-tokens-saved": "0",
                },
            )
        except Exception:
            pass

    enable_compression = body.pop("enable_compression", True)
    compression_rate = body.pop("compression_rate", 0.5)
    modified_messages, compression_ratio = compress_last_user_message(
        messages.copy(), rate=compression_rate, enable_compression=enable_compression
    )

    body["messages"] = modified_messages

    target_url = get_target_api(request)
    logger.info(f"Forwarding request to {target_url}")

    try:
        response = await forward_request(
            target_url=target_url,
            path="/v1/chat/completions",
            method="POST",
            headers=dict(request.headers),
            body=body,
        )
        logger.info(
            f"Received response: status={response.status_code}, content_length={len(response.content)}"
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Gateway timeout")
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Bad gateway: {str(e)}")

    if response.status_code != 200:
        try:
            error_content = (
                response.json() if response.content else {"error": "Unknown error"}
            )
        except Exception:
            error_content = {
                "error": response.text or "Unknown error",
                "status_code": response.status_code,
            }
        return JSONResponse(
            content=error_content,
            status_code=response.status_code,
        )

    try:
        response_data = response.json()
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Invalid JSON from target API: {str(e)}"
        )

    cache.set(cache_key, json.dumps(response_data))

    original_tokens = 0
    compressed_tokens = 0
    if compression_ratio:
        usage = response_data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        original_tokens = (
            int(prompt_tokens / compression_ratio)
            if compression_ratio > 0
            else prompt_tokens
        )
        compressed_tokens = prompt_tokens

    tokens_saved = original_tokens - compressed_tokens

    return JSONResponse(
        content=response_data,
        headers={
            "x-tokencrush-cache": "miss",
            "x-tokencrush-compression-ratio": f"{compression_ratio:.2f}"
            if compression_ratio
            else "0.0",
            "x-tokencrush-tokens-saved": str(tokens_saved),
        },
    )


@app.get("/v1/models")
async def list_models(request: Request):
    """Forward model listing to target API."""
    target_url = get_target_api(request)

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


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "tokencrush-proxy"}


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "TokenCrush Proxy",
        "version": "0.1.0",
        "endpoints": {
            "chat": "/v1/chat/completions",
            "models": "/v1/models",
            "health": "/health",
        },
    }
