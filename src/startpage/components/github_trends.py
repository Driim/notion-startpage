"""GitHub Trending repositories component.

Fetches and parses https://github.com/trending and returns a markdown table
with the top trending repositories for a given language and time range.
"""

import logging
from dataclasses import dataclass

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_GITHUB_TRENDING_URL = "https://github.com/trending"
_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass(frozen=True)
class Repository:
    """A trending GitHub repository.

    Attributes:
        rank: Position on the trending list (1-based).
        full_name: owner/repo string.
        url: Full GitHub URL.
        description: Repository description.
        language: Primary programming language.
        stars_total: Total star count.
        stars_today: Stars gained today.
    """

    rank: int
    full_name: str
    url: str
    description: str
    language: str
    stars_total: int
    stars_today: int


def _parse_number(text: str) -> int:
    """Convert '1,234' or '1,234 stars today' to int."""
    if not text or not text.strip():
        return 0
    cleaned = text.strip().replace(",", "").split()[0]
    try:
        return int(cleaned)
    except ValueError:
        return 0


def _parse_repositories(html: str) -> list[Repository]:
    """Parse GitHub Trending HTML into a list of Repository objects."""
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.select("article.Box-row")

    repos = []
    for rank, article in enumerate(articles, start=1):
        h2 = article.select_one("h2 a")
        if not h2:
            continue

        parts = [p.strip() for p in h2.get_text(separator="/").split("/") if p.strip()]
        if len(parts) < 2:
            continue

        owner, name = parts[0], parts[1]
        full_name = f"{owner}/{name}"

        desc_el = article.select_one("p")
        description = desc_el.get_text(strip=True) if desc_el else ""

        lang_el = article.select_one("[itemprop='programmingLanguage']")
        language = lang_el.get_text(strip=True) if lang_el else ""

        stars_link = article.select("a[href$='/stargazers']")
        stars_total = _parse_number(stars_link[0].get_text()) if stars_link else 0

        today_el = article.select_one("span.d-inline-block.float-sm-right")
        stars_today = _parse_number(today_el.get_text()) if today_el else 0

        repos.append(
            Repository(
                rank=rank,
                full_name=full_name,
                url=f"https://github.com/{full_name}",
                description=description,
                language=language,
                stars_total=stars_total,
                stars_today=stars_today,
            )
        )

    return repos


async def fetch_trending(
    language: str = "",
    since: str = "daily",
    limit: int = 10,
) -> list[Repository]:
    """Fetch trending repositories from GitHub.

    Args:
        language: Programming language filter (e.g. 'python'). Empty means all.
        since: Time range — 'daily', 'weekly', or 'monthly'.
        limit: Maximum number of repositories to return.

    Returns:
        List of Repository objects ordered by trending rank.

    Raises:
        aiohttp.ClientError: If the HTTP request fails.
    """
    url = f"{_GITHUB_TRENDING_URL}/{language}" if language else _GITHUB_TRENDING_URL
    params = {"since": since}

    async with aiohttp.ClientSession(headers=_REQUEST_HEADERS) as session:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
            response.raise_for_status()
            html = await response.text()

    repos = _parse_repositories(html)
    logger.info("Fetched %d trending repositories (language=%r, since=%r)", len(repos), language, since)
    return repos[:limit]


def to_markdown_table(repos: list[Repository]) -> str:
    """Format a list of repositories as a markdown table.

    Args:
        repos: List of Repository objects.

    Returns:
        Markdown-formatted table string.
    """
    if not repos:
        return "_No trending repositories found._"

    header = "| # | Repository | Language | ⭐ Total | ⭐ Today | Description |"
    separator = "|---|-----------|----------|---------|---------|-------------|"

    rows = []
    for r in repos:
        name_link = f"[{r.full_name}]({r.url})"
        desc = r.description[:80] + "…" if len(r.description) > 80 else r.description
        rows.append(
            f"| {r.rank} | {name_link} | {r.language or '—'} "
            f"| {r.stars_total:,} | {r.stars_today:,} | {desc} |"
        )

    return "\n".join([header, separator, *rows])
