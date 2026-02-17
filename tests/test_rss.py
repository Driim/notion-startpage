"""Tests for RSS feed component."""

from datetime import datetime
from time import struct_time
from unittest.mock import MagicMock, patch

import pytest

from src.startpage.components.rss import (
    Article,
    Feed,
    fetch_articles_from_feeds,
    fetch_feed,
    get_published_datetime,
)


@pytest.fixture
def sample_feeds():
    """Create sample feeds for testing."""
    return [
        Feed(name="TechNews", url="https://example.com/tech/feed", priority=1),
        Feed(name="Business", url="https://example.com/biz/feed", priority=2),
    ]


@pytest.fixture
def sample_banned_tags():
    """Create sample banned tags set."""
    return {"sponsored", "advertisement"}


def test_feed_dataclass():
    """Test Feed dataclass initialization."""
    feed = Feed(name="Test", url="https://example.com/feed", priority=1)
    assert feed.name == "Test"
    assert feed.url == "https://example.com/feed"
    assert feed.priority == 1


def test_article_dataclass():
    """Test Article dataclass initialization."""
    feed = Feed(name="Test", url="https://example.com/feed", priority=1)
    now = datetime.now()
    article = Article(
        feed=feed,
        title="Test Article",
        description="Test description",
        full_text="Full text",
        link="https://example.com/article",
        published=now,
        authors=["John Doe"],
        tags=["tech"],
        priority=1,
    )
    assert article.title == "Test Article"
    assert article.feed == feed
    assert article.published == now


def test_get_published_datetime_with_valid_struct_time():
    """Test parsing datetime from struct_time."""
    # Create a valid struct_time
    test_time = struct_time((2024, 1, 15, 12, 30, 0, 0, 15, 0))
    entry = {"published_parsed": test_time}

    result = get_published_datetime(entry)

    assert isinstance(result, datetime)
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 15


def test_get_published_datetime_with_missing_field():
    """Test get_published_datetime returns current time when field is missing."""
    entry = {}
    result = get_published_datetime(entry)

    assert isinstance(result, datetime)
    # Should return approximately now (within a few seconds)
    assert (datetime.now(result.tzinfo) - result).total_seconds() < 5


def test_get_published_datetime_with_invalid_format():
    """Test get_published_datetime with invalid format."""
    entry = {"published_parsed": "invalid"}
    result = get_published_datetime(entry)

    assert isinstance(result, datetime)


@patch("src.startpage.components.rss.feedparser.parse")
def test_fetch_articles_from_feeds_success(mock_parse, sample_feeds):
    """Test successful article fetching from multiple feeds."""
    # Mock feedparser response
    mock_parse.return_value = MagicMock(
        entries=[
            {
                "title": "Article 1",
                "summary": "Summary 1",
                "content": [{"value": "Full content 1"}],
                "link": "https://example.com/1",
                "published_parsed": struct_time((2024, 1, 15, 12, 0, 0, 0, 15, 0)),
                "authors": [{"name": "Author 1"}],
                "tags": [{"term": "tech"}],
            },
            {
                "title": "Article 2",
                "summary": "Summary 2",
                "link": "https://example.com/2",
                "published_parsed": struct_time((2024, 1, 15, 13, 0, 0, 0, 15, 0)),
                "authors": [],
                "tags": [],
            },
        ]
    )

    # Create timezone-aware datetime to match rss.py
    import pytz

    tz = pytz.UTC
    with patch(
        "src.startpage.components.rss.start_of_the_day",
        tz.localize(datetime(2024, 1, 15)),
    ):
        articles = fetch_articles_from_feeds(sample_feeds, set())

    # Should get articles from both feeds (2 feeds × 2 entries = 4 articles)
    assert len(articles) == 4
    assert all(isinstance(article, Article) for article in articles)


@patch("src.startpage.components.rss.feedparser.parse")
def test_fetch_articles_from_feeds_filters_banned_tags(mock_parse, sample_feeds):
    """Test that articles with banned tags are filtered out."""
    mock_parse.return_value = MagicMock(
        entries=[
            {
                "title": "Good Article",
                "summary": "Good summary",
                "link": "https://example.com/good",
                "published_parsed": struct_time((2024, 1, 15, 12, 0, 0, 0, 15, 0)),
                "authors": [],
                "tags": [{"term": "tech"}],
            },
            {
                "title": "Sponsored Article",
                "summary": "Sponsored content",
                "link": "https://example.com/sponsored",
                "published_parsed": struct_time((2024, 1, 15, 12, 0, 0, 0, 15, 0)),
                "authors": [],
                "tags": [{"term": "sponsored"}],
            },
        ]
    )

    # Create timezone-aware datetime to match rss.py
    import pytz

    tz = pytz.UTC
    with patch(
        "src.startpage.components.rss.start_of_the_day",
        tz.localize(datetime(2024, 1, 15)),
    ):
        articles = fetch_articles_from_feeds(sample_feeds, {"sponsored"})

    # Should only get non-sponsored articles (1 good article × 2 feeds = 2)
    assert len(articles) == 2
    assert all("Sponsored" not in article.title for article in articles)


@patch("src.startpage.components.rss.feedparser.parse")
def test_fetch_articles_from_feeds_filters_old_articles(mock_parse, sample_feeds):
    """Test that articles published before today are filtered out."""
    mock_parse.return_value = MagicMock(
        entries=[
            {
                "title": "Today Article",
                "summary": "Published today",
                "link": "https://example.com/today",
                "published_parsed": struct_time((2024, 1, 15, 12, 0, 0, 0, 15, 0)),
                "authors": [],
                "tags": [],
            },
            {
                "title": "Old Article",
                "summary": "Published yesterday",
                "link": "https://example.com/old",
                "published_parsed": struct_time((2024, 1, 14, 12, 0, 0, 0, 14, 0)),
                "authors": [],
                "tags": [],
            },
        ]
    )

    # Create timezone-aware datetime to match rss.py
    import pytz

    tz = pytz.UTC
    with patch(
        "src.startpage.components.rss.start_of_the_day",
        tz.localize(datetime(2024, 1, 15)),
    ):
        articles = fetch_articles_from_feeds(sample_feeds, set())

    # Should only get today's articles (1 today article × 2 feeds = 2)
    assert len(articles) == 2
    assert all("Today" in article.title for article in articles)


@pytest.mark.asyncio
@patch("src.startpage.components.rss.fetch_articles_from_feeds")
async def test_fetch_feed_success(mock_fetch, sample_feeds):
    """Test successful feed fetching and formatting."""
    # Create mock articles
    mock_articles = [
        Article(
            feed=sample_feeds[0],
            title="Article 1",
            description="Desc 1",
            full_text="Full 1",
            link="https://example.com/1",
            published=datetime(2024, 1, 15, 12, 0),
            authors=["Author 1"],
            tags=["tech"],
            priority=1,
        ),
        Article(
            feed=sample_feeds[1],
            title="Article 2",
            description="Desc 2",
            full_text="Full 2",
            link="https://example.com/2",
            published=datetime(2024, 1, 15, 13, 0),
            authors=["Author 2"],
            tags=["business"],
            priority=2,
        ),
    ]
    mock_fetch.return_value = mock_articles

    result = await fetch_feed("Tech News", sample_feeds, set(), max_articles=5)

    assert isinstance(result, list)
    assert len(result) > 0
    # First block should be header
    assert result[0]["type"] == "heading_2"
    assert result[0]["heading_2"]["rich_text"][0]["text"]["content"] == "Tech News"
    # Following blocks should be articles
    assert result[1]["type"] == "bulleted_list_item"


@pytest.mark.asyncio
@patch("src.startpage.components.rss.fetch_articles_from_feeds")
async def test_fetch_feed_respects_max_articles(mock_fetch, sample_feeds):
    """Test that fetch_feed respects max_articles limit."""
    # Create 10 mock articles
    mock_articles = []
    for i in range(10):
        feed_idx = i % 2
        mock_articles.append(
            Article(
                feed=sample_feeds[feed_idx],
                title=f"Article {i}",
                description=f"Desc {i}",
                full_text=f"Full {i}",
                link=f"https://example.com/{i}",
                published=datetime(2024, 1, 15, 12, i),
                authors=[],
                tags=[],
                priority=sample_feeds[feed_idx].priority,
            )
        )
    mock_fetch.return_value = mock_articles

    result = await fetch_feed("Tech News", sample_feeds, set(), max_articles=3)

    # Should have header + 3 articles = 4 blocks
    assert len(result) == 4
    assert result[0]["type"] == "heading_2"
    assert all(result[i]["type"] == "bulleted_list_item" for i in range(1, 4))


@pytest.mark.asyncio
@patch("src.startpage.components.rss.fetch_articles_from_feeds")
async def test_fetch_feed_max_2_per_feed(mock_fetch, sample_feeds):
    """Test that at most 2 articles per feed are selected."""
    # Create 6 articles from the same feed
    mock_articles = []
    for i in range(6):
        mock_articles.append(
            Article(
                feed=sample_feeds[0],
                title=f"Article {i}",
                description=f"Desc {i}",
                full_text=f"Full {i}",
                link=f"https://example.com/{i}",
                published=datetime(2024, 1, 15, 12, i),
                authors=[],
                tags=[],
                priority=1,
            )
        )
    mock_fetch.return_value = mock_articles

    result = await fetch_feed("Tech News", sample_feeds, set(), max_articles=10)

    # Should have header + 2 articles (max per feed) = 3 blocks
    assert len(result) == 3


@pytest.mark.asyncio
@patch("src.startpage.components.rss.fetch_articles_from_feeds")
async def test_fetch_feed_with_empty_results(mock_fetch, sample_feeds):
    """Test fetch_feed with no articles."""
    mock_fetch.return_value = []

    result = await fetch_feed("Tech News", sample_feeds, set(), max_articles=5)

    # Should only have header block
    assert len(result) == 1
    assert result[0]["type"] == "heading_2"


@pytest.mark.asyncio
@patch("src.startpage.components.rss.fetch_articles_from_feeds")
async def test_fetch_feed_sorts_by_priority_and_date(mock_fetch, sample_feeds):
    """Test that articles are sorted by priority first, then by date."""
    # Create articles with different priorities and dates
    mock_articles = [
        Article(
            feed=sample_feeds[1],  # priority 2
            title="Low Priority New",
            description="",
            full_text="",
            link="https://example.com/1",
            published=datetime(2024, 1, 15, 14, 0),
            authors=[],
            tags=[],
            priority=2,
        ),
        Article(
            feed=sample_feeds[0],  # priority 1
            title="High Priority Old",
            description="",
            full_text="",
            link="https://example.com/2",
            published=datetime(2024, 1, 15, 12, 0),
            authors=[],
            tags=[],
            priority=1,
        ),
    ]
    mock_fetch.return_value = mock_articles

    result = await fetch_feed("Tech News", sample_feeds, set(), max_articles=5)

    # First article (after header) should be high priority one
    assert (
        "High Priority Old"
        in result[1]["bulleted_list_item"]["rich_text"][0]["text"]["content"]
    )
