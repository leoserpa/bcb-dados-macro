"""Resilient HTTP client configuration for BCB APIs."""

from __future__ import annotations

from itertools import takewhile

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_TIMEOUT_SECONDS = 30
RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)


class ExponentialRetry(Retry):
    """Retry policy whose consecutive waits are exactly 2, 4 and 8 seconds."""

    def get_backoff_time(self) -> float:
        consecutive_errors = len(
            list(
                takewhile(
                    lambda item: item.redirect_location is None,
                    reversed(self.history),
                )
            )
        )
        if consecutive_errors == 0:
            return 0.0
        backoff = self.backoff_factor * (2 ** (consecutive_errors - 1))
        return float(min(self.backoff_max, backoff))


def create_http_session() -> requests.Session:
    """Create a requests session with retry and connection pooling."""
    retry = ExponentialRetry(
        total=3,
        connect=3,
        read=3,
        status=3,
        allowed_methods=frozenset({"GET"}),
        status_forcelist=RETRYABLE_STATUS_CODES,
        backoff_factor=2,
        backoff_max=8,
        respect_retry_after_header=False,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": "bcb-macro-lakehouse/0.1",
        }
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session
