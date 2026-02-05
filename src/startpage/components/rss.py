"""RSS feed aggregation and article filtering component.

This module provides functionality to fetch, parse, filter, and format RSS feed
articles for display in Notion. It supports multiple feeds, priority-based sorting,
tag-based filtering, and per-feed article limits.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from time import mktime, struct_time

import feedparser
import pytz

logger = logging.getLogger(__name__)

tz = pytz.timezone(os.getenv("TIMEZONE", "UTC"))
now = datetime.now(tz)
start_of_the_day = now.replace(hour=0, minute=0, second=0, microsecond=0)


@dataclass
class Feed:
    """Represents an RSS feed source.

    Attributes:
        name: Display name for the feed.
        url: RSS feed URL.
        priority: Feed priority (lower number = higher priority).
    """

    name: str
    url: str
    priority: int


@dataclass
class Article:
    """Represents a parsed RSS article.

    Attributes:
        feed: Source feed object.
        title: Article title.
        description: Short article summary.
        full_text: Complete article content.
        link: Article URL.
        published: Publication datetime.
        authors: List of author names.
        tags: List of article tags.
        priority: Inherited from feed priority.
    """

    feed: Feed
    title: str
    description: str
    full_text: str
    link: str
    published: datetime
    authors: list
    tags: list
    priority: int


def get_published_datetime(entry) -> datetime:
    """Extract and parse publication datetime from RSS entry.

    Args:
        entry: RSS feed entry dictionary.

    Returns:
        Parsed datetime object, or current time if parsing fails.
    """
    published_parsed = entry.get("published_parsed", None)

    if published_parsed and hasattr(published_parsed, "tm_year"):
        if isinstance(published_parsed, struct_time):
            return tz.localize(datetime.fromtimestamp(mktime(published_parsed)))

    return now


def fetch_articles_from_feeds(
    feeds: list[Feed], banned_tags: set[str]
) -> list[Article]:
    """Fetch and parse articles from multiple RSS feeds.

    Filters out articles published before today and articles containing banned tags.

    Args:
        feeds: List of Feed objects to fetch from.
        banned_tags: Set of lowercase tag strings to filter out.

    Returns:
        List of Article objects published today without banned tags.
    """
    articles = []

    for feed in feeds:
        news = feedparser.parse(feed.url)

        for entry in news.entries:
            published = get_published_datetime(entry)
            if published < start_of_the_day:
                continue

            tags = set(
                [
                    str(tag.get("term", "") or "").lower()
                    for tag in (entry.get("tags") or [])
                ]
            )
            if banned_tags.intersection(tags):
                continue

            title = str(entry.get("title", ""))
            content = entry.get("content", [{}])
            full_text = str(
                content[0].get("value", entry.get("summary", ""))
                if content
                else entry.get("summary", "")
            )
            description = str(entry.get("summary", ""))
            link = str(entry.get("link", ""))
            authors = [
                author.get("name", "") for author in (entry.get("authors") or [])
            ]

            article = Article(
                feed=feed,
                title=title,
                description=description,
                full_text=full_text,
                link=link,
                published=published,
                authors=authors,
                tags=list(tags),
                priority=feed.priority,
            )

            articles.append(article)

    return articles


async def fetch_feed(
    header: str, feeds: list[Feed], banned_tags: set[str], max_articles: int = 5
):
    """Fetch, filter, and format RSS articles as Notion blocks.

    Articles are sorted by priority and publication date. At most 2 articles
    per feed are selected.

    Args:
        header: Section header text for Notion display.
        feeds: List of Feed objects to aggregate.
        banned_tags: Set of lowercase tags to filter out.
        max_articles: Maximum number of articles to return (default: 5).

    Returns:
        List of Notion block dictionaries containing the header and article links.
    """
    articles = []

    # TODO: Consider using aiohttp and async feedparser for concurrent fetching
    articles = fetch_articles_from_feeds(feeds, banned_tags)

    articles.sort(key=lambda x: (x.priority, x.published))

    # Select up to max_articles articles, max 2 per feed
    selected_articles = []
    feed_count = {}

    for article in articles:
        feed_name = article.feed.name

        if feed_count.get(feed_name, 0) < 2:
            selected_articles.append(article)
            feed_count[feed_name] = feed_count.get(feed_name, 0) + 1

            if len(selected_articles) == max_articles:
                break

    blocks = [
        {
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": header}}]},
        }
    ]

    for article in selected_articles:
        text = f"[{article.feed.name}] {article.title}"
        logger.info(f"Selected article: {article.title} from feed: {article.feed.name}")
        blocks.append(
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": text, "link": {"url": article.link}},
                        }
                    ]
                },
            }
        )

    return blocks
