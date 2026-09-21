"""The one place Zenkai makes an outbound request to a source.

Everything a polite client owes a provider lives here, so no connector can
forget a piece of it:

* an honest, identifiable User-Agent with a contact URL
* robots.txt consulted before the first request to a host, and obeyed
* Crawl-delay honoured where a host specifies one
* a floor on the interval between requests to the same host
* a request timeout, so a hanging source cannot stall a run
* redirects followed, but only a bounded number

It does not attempt authentication, does not send cookies, and does not retry
around a 401, 403 or 429. Those are a provider saying no, and the answer is to
stop, record it, and let a human look — not to try a different way in.
"""
from __future__ import annotations

import logging
import time
import urllib.robotparser as robotparser
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

USER_AGENT = "ZenkaiBot/0.1 (+https://zenkai.dev/bot; opportunity discovery)"
#: Identity robots.txt rules are evaluated against.
ROBOTS_AGENT = "ZenkaiBot"

REQUEST_TIMEOUT = 20.0
MAX_REDIRECTS = 5
#: Minimum gap between two requests to the same host, absent a Crawl-delay.
DEFAULT_MIN_INTERVAL = 1.0
#: Refuse bodies beyond this. A feed is text; anything huge is a wrong turn.
MAX_BYTES = 8 * 1024 * 1024

#: Status codes that mean "do not come back this way". Never retried.
REFUSAL_CODES = frozenset({401, 402, 403, 407, 429, 451})


class FetchRefused(PermissionError):
    """The source declined us. Recorded as a failure; never worked around."""


class FetchFailed(RuntimeError):
    """The request did not succeed for a reason that is not a refusal."""


@dataclass
class FetchedDocument:
    url: str
    final_url: str
    status_code: int
    content_type: str | None
    body: str
    retrieved_at: datetime


class PoliteFetcher:
    """A small HTTP client that behaves itself.

    One instance per run: it caches robots.txt per host and tracks when each
    host was last contacted, both of which only make sense within a run.
    """

    def __init__(
        self,
        client: httpx.Client | None = None,
        min_interval: float = DEFAULT_MIN_INTERVAL,
        respect_robots: bool = True,
    ) -> None:
        self._client = client or httpx.Client(
            follow_redirects=True,
            timeout=REQUEST_TIMEOUT,
            max_redirects=MAX_REDIRECTS,
            headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.5"},
        )
        self._owns_client = client is None
        self._min_interval = min_interval
        self._respect_robots = respect_robots
        self._robots: dict[str, robotparser.RobotFileParser | None] = {}
        self._last_request: dict[str, float] = {}

    # --- Politeness --------------------------------------------------------

    def _robots_for(self, host_root: str) -> robotparser.RobotFileParser | None:
        """Fetch and cache a host's robots.txt.

        A missing or unreadable robots.txt means no rules were published, which
        is not the same as being disallowed. A host that errors on robots.txt
        is given the benefit of the doubt for the feed itself, because refusing
        everything on a 500 would be its own kind of wrong.
        """
        if host_root in self._robots:
            return self._robots[host_root]

        parser: robotparser.RobotFileParser | None = None
        try:
            response = self._client.get(f"{host_root}/robots.txt", timeout=10.0)
            if response.status_code == 200:
                parser = robotparser.RobotFileParser()
                parser.parse(response.text.splitlines())
        except httpx.HTTPError as exc:
            logger.info("robots.txt unavailable for %s: %s", host_root, exc)

        self._robots[host_root] = parser
        return parser

    def _wait_turn(self, host: str, crawl_delay: float | None) -> None:
        gap = max(self._min_interval, crawl_delay or 0.0)
        last = self._last_request.get(host)
        if last is not None:
            remaining = gap - (time.monotonic() - last)
            if remaining > 0:
                time.sleep(remaining)
        self._last_request[host] = time.monotonic()

    def may_fetch(self, url: str) -> tuple[bool, str]:
        """Whether robots.txt permits this URL. Checked before every request."""
        if not self._respect_robots:
            return True, "robots checking disabled for this run"
        parts = urlparse(url)
        if parts.scheme not in {"http", "https"}:
            return False, f"refusing a non-http(s) URL ({parts.scheme or 'no scheme'})"

        parser = self._robots_for(f"{parts.scheme}://{parts.netloc}")
        if parser is None:
            return True, "no robots.txt published"
        if parser.can_fetch(ROBOTS_AGENT, url):
            return True, "permitted by robots.txt"
        return False, "disallowed by robots.txt"

    # --- Retrieval ---------------------------------------------------------

    def get(self, url: str) -> FetchedDocument:
        allowed, reason = self.may_fetch(url)
        if not allowed:
            raise FetchRefused(f"{reason}: {url}")

        parts = urlparse(url)
        parser = self._robots_for(f"{parts.scheme}://{parts.netloc}")
        crawl_delay = None
        if parser is not None:
            try:
                crawl_delay = parser.crawl_delay(ROBOTS_AGENT)
            except Exception:  # a malformed directive must not stop the run
                crawl_delay = None
        self._wait_turn(parts.netloc, float(crawl_delay) if crawl_delay else None)

        try:
            response = self._client.get(url)
        except httpx.HTTPError as exc:
            raise FetchFailed(f"{type(exc).__name__} fetching {url}") from exc

        if response.status_code in REFUSAL_CODES:
            # The provider said no. Recorded and left alone.
            raise FetchRefused(
                f"HTTP {response.status_code} from {url} — the source declined this client"
            )
        if response.status_code >= 400:
            raise FetchFailed(f"HTTP {response.status_code} from {url}")

        if len(response.content) > MAX_BYTES:
            raise FetchFailed(f"response from {url} exceeds {MAX_BYTES} bytes")

        return FetchedDocument(
            url=url,
            final_url=str(response.url),
            status_code=response.status_code,
            content_type=response.headers.get("content-type"),
            body=response.text,
            retrieved_at=datetime.now(timezone.utc),
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> PoliteFetcher:
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
