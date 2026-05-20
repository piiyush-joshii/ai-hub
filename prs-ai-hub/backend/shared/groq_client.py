"""
Shared Groq client with primary + fallback models.

Primary (default): llama-3.3-70b-versatile — strong JSON mode for validation agents.
Fallback chain (default): openai/gpt-oss-120b → openai/gpt-oss-20b → llama-3.1-8b-instant
See https://console.groq.com/docs/models
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger(__name__)

_client: Groq | None = None
MAX_RETRIES = 3
_RETRYABLE_MARKERS = (
    "429",
    "rate_limit",
    "timeout",
    "503",
    "502",
    "500",
    "overloaded",
    "temporarily",
    "capacity",
)

DEFAULT_PRIMARY = "llama-3.3-70b-versatile"
# GPT-OSS 120B: best quality OSS fallback on Groq; then 20B for speed; 8B last resort.
DEFAULT_FALLBACKS = "openai/gpt-oss-120b,openai/gpt-oss-20b,llama-3.1-8b-instant"


def _validate_api_key() -> str:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key or "your_groq_api_key" in key or key == "gsk_your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY is missing or still the placeholder in prs-ai-hub/.env. "
            "Get a key at https://console.groq.com and restart the backend."
        )
    return key


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=_validate_api_key())
    return _client


def _models_to_try() -> list[str]:
    primary = os.getenv("GROQ_MODEL", DEFAULT_PRIMARY).strip() or DEFAULT_PRIMARY
    raw_fallbacks = os.getenv("GROQ_FALLBACK_MODELS", DEFAULT_FALLBACKS)
    fallbacks = [m.strip() for m in raw_fallbacks.split(",") if m.strip()]
    models = [primary]
    for model in fallbacks:
        if model not in models:
            models.append(model)
    return models


def _is_retryable(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(marker in text for marker in _RETRYABLE_MARKERS)


def _is_auth_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "invalid_api_key" in text or "401" in text or "invalid api key" in text


def _parse_json_response(raw: str) -> dict:
    text = (raw or "{}").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        clean = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            raise ValueError(
                "Model returned invalid or truncated JSON."
            ) from e


def _invoke_model(
    model: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int,
) -> dict:
    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.0,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or "{}"
    return _parse_json_response(raw)


def _call_groq_sync(system_prompt: str, user_message: str) -> dict:
    max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "4096"))
    models = _models_to_try()
    errors: list[str] = []

    for model in models:
        for attempt in range(MAX_RETRIES):
            try:
                result = _invoke_model(model, system_prompt, user_message, max_tokens)
                if model != models[0]:
                    logger.warning("Groq primary model failed; succeeded with fallback: %s", model)
                else:
                    logger.debug("Groq call succeeded with primary model: %s", model)
                return result
            except ValueError as e:
                if _is_auth_error(e) or "GROQ_API_KEY" in str(e):
                    raise ValueError(
                        "Groq rejected the API key. Update GROQ_API_KEY in prs-ai-hub/.env and restart."
                    ) from e
                errors.append(f"{model} (attempt {attempt + 1}): {e}")
                break
            except Exception as e:
                if _is_auth_error(e):
                    raise ValueError(
                        "Groq rejected the API key. Update GROQ_API_KEY in prs-ai-hub/.env and restart."
                    ) from e
                msg = f"{model} (attempt {attempt + 1}): {e}"
                errors.append(msg)
                if attempt < MAX_RETRIES - 1 and _is_retryable(e):
                    time.sleep(2**attempt)
                    continue
                break

    detail = "; ".join(errors[-4:]) if errors else "unknown error"
    raise RuntimeError(
        f"All Groq models failed ({', '.join(models)}). Last errors: {detail}"
    )


async def call_groq(system_prompt: str, user_message: str) -> dict:
    return await asyncio.to_thread(_call_groq_sync, system_prompt, user_message)
