"""Polite standard-library HTTP client with retries and pacing."""

from __future__ import annotations

import random
import time
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, Request, build_opener


class FetchError(RuntimeError):
    pass


class HttpClient:
    def __init__(self, delay: float = 0.5, retries: int = 4, timeout: float = 30.0) -> None:
        if delay < 0:
            raise ValueError("delay must be non-negative")
        self.delay = delay
        self.retries = retries
        self.timeout = timeout
        self._last_request = 0.0
        self._opener = build_opener(HTTPCookieProcessor(CookieJar()))

    def _pace(self) -> None:
        remaining = self.delay - (time.monotonic() - self._last_request)
        if remaining > 0:
            time.sleep(remaining)

    def get(self, url: str, referer: str | None = None) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
        }
        if referer:
            headers["Referer"] = referer

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            self._pace()
            try:
                request = Request(url, headers=headers)
                with self._opener.open(request, timeout=self.timeout) as response:
                    self._last_request = time.monotonic()
                    charset = response.headers.get_content_charset() or "utf-8"
                    return response.read().decode(charset, errors="replace")
            except HTTPError as error:
                self._last_request = time.monotonic()
                last_error = error
                if error.code not in {403, 408, 429, 500, 502, 503, 504}:
                    break
            except (URLError, TimeoutError) as error:
                self._last_request = time.monotonic()
                last_error = error
            if attempt < self.retries:
                time.sleep(min(30.0, 2**attempt + random.random()))
        raise FetchError(f"failed to fetch {url}: {last_error}") from last_error
