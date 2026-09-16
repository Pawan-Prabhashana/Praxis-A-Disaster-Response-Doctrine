"""Shared HTTP fetching with a real User-Agent, retries, and a file cache.

A descriptive User-Agent is required by several sources (Overpass returns 406,
HDX/OSM etiquette). Network fetches retry with exponential backoff (tenacity)
and then FAIL LOUDLY — pipelines never silently substitute fabricated data.
"""

from __future__ import annotations

from pathlib import Path

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.logging import get_logger

_log = get_logger("praxis.etl.http")

USER_AGENT = (
    "Praxis-DisasterPlatform/0.2 (+https://github.com/Pawan-Prabhashana/"
    "Praxis-A-Disaster-Response-Doctrine)"
)

# backend/data/raw — git-ignored raw download cache.
CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


class FetchError(RuntimeError):
    """Raised when a real source cannot be fetched after retries."""


def _client(timeout: float) -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
        follow_redirects=True,
    )


@retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((httpx.HTTPError,)),
)
def _get(url: str, *, timeout: float, params: dict | None = None) -> httpx.Response:
    with _client(timeout) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response


def fetch_json(url: str, *, params: dict | None = None, timeout: float = 60.0) -> dict:
    """GET a URL and return parsed JSON, retrying transient failures."""
    try:
        return _get(url, timeout=timeout, params=params).json()
    except (httpx.HTTPError, ValueError) as exc:
        raise FetchError(f"Failed to fetch JSON from {url}: {exc}") from exc


def fetch_text(url: str, *, params: dict | None = None, timeout: float = 60.0) -> str:
    """GET a URL and return the response body as text."""
    try:
        return _get(url, timeout=timeout, params=params).text
    except httpx.HTTPError as exc:
        raise FetchError(f"Failed to fetch text from {url}: {exc}") from exc


@retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((httpx.HTTPError,)),
)
def _download_stream(url: str, dest: Path, *, timeout: float) -> None:
    with _client(timeout) as client, client.stream("GET", url) as response:
        response.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in response.iter_bytes(chunk_size=1 << 16):
                fh.write(chunk)


def download_file(url: str, filename: str, *, force: bool = False, timeout: float = 300.0) -> Path:
    """Download ``url`` into the cache as ``filename`` (idempotent unless force).

    Returns the cached path. Re-runs reuse the cached file so pipelines are
    cheap to repeat; pass ``force=True`` to re-fetch.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE_DIR / filename
    if dest.exists() and dest.stat().st_size > 0 and not force:
        _log.info("etl.cache_hit", filename=filename, bytes=dest.stat().st_size)
        return dest

    _log.info("etl.download_start", url=url, filename=filename)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        _download_stream(url, tmp, timeout=timeout)
    except httpx.HTTPError as exc:
        tmp.unlink(missing_ok=True)
        raise FetchError(f"Failed to download {url}: {exc}") from exc

    tmp.replace(dest)
    _log.info("etl.download_done", filename=filename, bytes=dest.stat().st_size)
    return dest
