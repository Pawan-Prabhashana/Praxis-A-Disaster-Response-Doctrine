"""Thin async LLM client for brief narration (Anthropic Messages API).

A minimal ``httpx`` wrapper — no heavyweight SDK — so the API image stays lean
and provider flexibility comes from ``PRAXIS_LLM_BASE_URL`` (any Anthropic
Messages-compatible endpoint). One bounded call per brief, wrapped in a tenacity
retry with a timeout. When narration is disabled or no key is present, this
module is never invoked (the generator uses the template), and nothing here runs
at import time — so the app and tests work fully offline with no key.
"""

from __future__ import annotations

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.core.logging import get_logger

log = get_logger("praxis.brief.llm")


class LlmError(RuntimeError):
    """Raised when the LLM call fails or returns an unusable response."""


class LlmClient:
    """Calls the Anthropic Messages API for a single-turn completion."""

    def __init__(self, settings: Settings) -> None:
        if not settings.llm_api_key:
            raise LlmError("LLM API key is not configured")
        self._model = settings.llm_model
        self._max_tokens = settings.llm_max_tokens
        self._timeout = settings.llm_timeout_s
        self._base_url = settings.llm_base_url.rstrip("/")
        self._headers = {
            "x-api-key": settings.llm_api_key,
            "anthropic-version": settings.llm_api_version,
            "content-type": "application/json",
        }

    async def complete(self, system: str, user: str) -> str:
        """Return the text of a single completion, retrying transient failures."""

        @retry(
            reraise=True,
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.5, max=4),
            retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        )
        async def _call() -> str:
            payload = {
                "model": self._model,
                "max_tokens": self._max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/v1/messages", headers=self._headers, json=payload
                )
                resp.raise_for_status()
                data = resp.json()
            return _extract_text(data)

        try:
            return await _call()
        except Exception as exc:  # collapse any failure into one typed error
            log.warning("brief.llm_call_failed", error=str(exc))
            raise LlmError(str(exc)) from exc


def _extract_text(data: dict) -> str:
    """Pull the concatenated text blocks out of a Messages API response."""
    blocks = data.get("content") or []
    text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
    if not text.strip():
        raise LlmError("LLM returned an empty completion")
    return text
