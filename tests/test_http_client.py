from urllib3.util.retry import RequestHistory

from src.utils.http_client import ExponentialRetry, create_http_session


def test_retry_backoff_is_two_four_eight_seconds() -> None:
    history_item = RequestHistory("GET", "https://example.test", None, 503, None)

    waits = [
        ExponentialRetry(
            backoff_factor=2,
            backoff_max=8,
            history=(history_item,) * attempt,
        ).get_backoff_time()
        for attempt in (1, 2, 3)
    ]

    assert waits == [2.0, 4.0, 8.0]


def test_http_session_retries_only_expected_statuses() -> None:
    session = create_http_session()
    retry = session.get_adapter("https://").max_retries

    assert retry.total == 3
    assert retry.status_forcelist == (429, 500, 502, 503, 504)
    assert retry.allowed_methods == frozenset({"GET"})
    session.close()
