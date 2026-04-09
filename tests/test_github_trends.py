"""Tests for GitHub Trending component."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.startpage.components.github_trends import (
    Repository,
    _parse_number,
    _parse_repositories,
    fetch_trending,
    to_markdown_table,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_HTML = """
<html><body>
<article class="Box-row">
  <h2><a href="/torvalds/linux">torvalds / linux</a></h2>
  <p>The Linux kernel</p>
  <span itemprop="programmingLanguage">C</span>
  <a href="/torvalds/linux/stargazers">185,000</a>
  <a href="/torvalds/linux/forks">50,000</a>
  <span class="d-inline-block float-sm-right">1,234 stars today</span>
</article>
<article class="Box-row">
  <h2><a href="/python/cpython">python / cpython</a></h2>
  <p>The Python programming language</p>
  <span itemprop="programmingLanguage">Python</span>
  <a href="/python/cpython/stargazers">62,000</a>
  <a href="/python/cpython/forks">30,000</a>
  <span class="d-inline-block float-sm-right">500 stars today</span>
</article>
</body></html>
"""

EMPTY_HTML = "<html><body></body></html>"


@pytest.fixture
def sample_repos() -> list[Repository]:
    return [
        Repository(
            rank=1,
            full_name="torvalds/linux",
            url="https://github.com/torvalds/linux",
            description="The Linux kernel",
            language="C",
            stars_total=185000,
            stars_today=1234,
        ),
        Repository(
            rank=2,
            full_name="python/cpython",
            url="https://github.com/python/cpython",
            description="The Python programming language",
            language="Python",
            stars_total=62000,
            stars_today=500,
        ),
    ]


# ---------------------------------------------------------------------------
# _parse_number
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_parse_number_plain_integer():
    assert _parse_number("1234") == 1234


@pytest.mark.unit
def test_parse_number_with_commas():
    assert _parse_number("1,234") == 1234


@pytest.mark.unit
def test_parse_number_with_trailing_text():
    assert _parse_number("1,234 stars today") == 1234


@pytest.mark.unit
def test_parse_number_empty_string():
    assert _parse_number("") == 0


@pytest.mark.unit
def test_parse_number_non_numeric():
    assert _parse_number("N/A") == 0


@pytest.mark.unit
def test_parse_number_whitespace_only():
    assert _parse_number("   ") == 0


# ---------------------------------------------------------------------------
# _parse_repositories
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_parse_repositories_returns_correct_count():
    repos = _parse_repositories(SAMPLE_HTML)
    assert len(repos) == 2


@pytest.mark.unit
def test_parse_repositories_first_repo_fields():
    repos = _parse_repositories(SAMPLE_HTML)
    repo = repos[0]
    assert repo.rank == 1
    assert repo.full_name == "torvalds/linux"
    assert repo.url == "https://github.com/torvalds/linux"
    assert repo.description == "The Linux kernel"
    assert repo.language == "C"
    assert repo.stars_total == 185000
    assert repo.stars_today == 1234


@pytest.mark.unit
def test_parse_repositories_second_repo_fields():
    repos = _parse_repositories(SAMPLE_HTML)
    repo = repos[1]
    assert repo.rank == 2
    assert repo.full_name == "python/cpython"
    assert repo.language == "Python"
    assert repo.stars_total == 62000
    assert repo.stars_today == 500


@pytest.mark.unit
def test_parse_repositories_empty_html_returns_empty_list():
    repos = _parse_repositories(EMPTY_HTML)
    assert repos == []


@pytest.mark.unit
def test_parse_repositories_immutable():
    repos = _parse_repositories(SAMPLE_HTML)
    with pytest.raises((AttributeError, TypeError)):
        repos[0].rank = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# fetch_trending
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_trending_returns_repositories():
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.text = AsyncMock(return_value=SAMPLE_HTML)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_session = AsyncMock()
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.startpage.components.github_trends.aiohttp.ClientSession", return_value=mock_session):
        repos = await fetch_trending()

    assert len(repos) == 2
    assert repos[0].full_name == "torvalds/linux"


@pytest.mark.asyncio
async def test_fetch_trending_respects_limit():
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.text = AsyncMock(return_value=SAMPLE_HTML)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_session = AsyncMock()
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.startpage.components.github_trends.aiohttp.ClientSession", return_value=mock_session):
        repos = await fetch_trending(limit=1)

    assert len(repos) == 1


@pytest.mark.asyncio
async def test_fetch_trending_uses_language_in_url():
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.text = AsyncMock(return_value=EMPTY_HTML)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_session = AsyncMock()
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.startpage.components.github_trends.aiohttp.ClientSession", return_value=mock_session):
        await fetch_trending(language="python")

    call_args = mock_session.get.call_args
    assert "python" in call_args[0][0]


# ---------------------------------------------------------------------------
# to_markdown_table
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_to_markdown_table_empty_list():
    result = to_markdown_table([])
    assert result == "_No trending repositories found._"


@pytest.mark.unit
def test_to_markdown_table_contains_header(sample_repos):
    result = to_markdown_table(sample_repos)
    assert "| # | Repository |" in result


@pytest.mark.unit
def test_to_markdown_table_contains_separator(sample_repos):
    result = to_markdown_table(sample_repos)
    lines = result.splitlines()
    assert any(line.startswith("|---") for line in lines)


@pytest.mark.unit
def test_to_markdown_table_contains_repo_link(sample_repos):
    result = to_markdown_table(sample_repos)
    assert "[torvalds/linux](https://github.com/torvalds/linux)" in result


@pytest.mark.unit
def test_to_markdown_table_contains_star_counts(sample_repos):
    result = to_markdown_table(sample_repos)
    assert "185,000" in result
    assert "1,234" in result


@pytest.mark.unit
def test_to_markdown_table_truncates_long_description():
    long_desc = "x" * 100
    repo = Repository(
        rank=1,
        full_name="a/b",
        url="https://github.com/a/b",
        description=long_desc,
        language="Go",
        stars_total=100,
        stars_today=10,
    )
    result = to_markdown_table([repo])
    assert "…" in result


@pytest.mark.unit
def test_to_markdown_table_row_count_matches_repos(sample_repos):
    result = to_markdown_table(sample_repos)
    # header + separator + N data rows
    lines = result.splitlines()
    assert len(lines) == 2 + len(sample_repos)


@pytest.mark.unit
def test_to_markdown_table_missing_language():
    repo = Repository(
        rank=1,
        full_name="a/b",
        url="https://github.com/a/b",
        description="desc",
        language="",
        stars_total=0,
        stars_today=0,
    )
    result = to_markdown_table([repo])
    assert "—" in result
