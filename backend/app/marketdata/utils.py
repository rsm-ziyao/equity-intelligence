import time
from typing import Callable
import httpx
from .exceptions import ProviderRateLimitError, ProviderError


def request_with_retry(client: httpx.Client, method: str, url: str, max_retries: int = 5, **kwargs) -> httpx.Response:
    """Simple exponential-backoff retry wrapper around httpx.Client.request.

    Retries on network errors and 429 responses. Raises ProviderRateLimitError
    when throttled beyond retries.
    """
    backoff = 0.5
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.request(method, url, **kwargs)
        except httpx.RequestError as e:
            if attempt == max_retries:
                raise ProviderError(f"HTTP request failed: {e}")
            time.sleep(backoff)
            backoff *= 2
            continue

        if resp.status_code == 429:
            # provider rate limit
            if attempt == max_retries:
                raise ProviderRateLimitError("rate limited by provider")
            # try again after backoff (some providers include Retry-After header)
            retry_after = 0
            try:
                retry_after = int(resp.headers.get("Retry-After", 0))
            except Exception:
                retry_after = 0
            wait = retry_after if retry_after > 0 else backoff
            time.sleep(wait)
            backoff *= 2
            continue

        # success or other HTTP error
        if resp.is_error:
            # surface provider message when possible
            try:
                j = resp.json()
                msg = j.get("Error Message") or j.get("Note") or resp.text
            except Exception:
                msg = resp.text
            raise ProviderError(f"HTTP {resp.status_code}: {msg}")

        return resp
