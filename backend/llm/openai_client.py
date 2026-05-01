"""
llm/openai_client.py - Thin async OpenAI wrapper.
Supports both regular and streaming completions.
Compatible with NVIDIA's OpenAI-compatible API endpoint.
"""
from __future__ import annotations

from typing import AsyncGenerator, List, Dict

from openai import AsyncOpenAI, APIError, RateLimitError
from config import settings

def get_client():
    """
    Returns an AsyncOpenAI client using the current settings.
    We re-instantiate or use settings values to ensure we pick up .env changes.
    """
    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


async def chat_completion(messages: List[Dict]) -> str:
    """
    Blocking (non-streaming) chat completion.
    Returns the full assistant reply as a string.
    """
    client = get_client()
    try:
        response = await client.chat.completions.create(
            model=settings.model_name,
            messages=messages,
            temperature=0.7,
        )
        return response.choices[0].message.content or ""
    except RateLimitError:
        return "Rate limit reached. Please wait a moment and try again."
    except APIError as e:
        return f"API error: {e.message}"
    except Exception as e:
        return f"Error: {str(e)}"


async def stream_completion(messages: List[Dict]) -> AsyncGenerator[str, None]:
    """
    Streaming chat completion.
    Yields text chunks as they arrive.
    """
    client = get_client()
    try:
        stream = await client.chat.completions.create(
            model=settings.model_name,
            messages=messages,
            temperature=0.7,
            stream=True,
        )
        async for chunk in stream:
            try:
                # NVIDIA sometimes sends chunks with empty choices (usage frames, etc.)
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
            except (IndexError, AttributeError):
                continue

    except RateLimitError:
        yield "Rate limit reached. Please wait a moment and try again."
    except APIError as e:
        yield f"API error: {e.message}"
    except Exception as e:
        yield f"Error: {str(e)}"
