"""StartPage application main orchestrator.

This module coordinates fetching data from multiple sources (weather, calendar,
currency, RSS feeds, and random facts) and publishes them to a Notion page as a
daily summary.
"""

import asyncio
import datetime
import logging
import os

from dotenv import load_dotenv
from notion_client import AsyncClient

from startpage.components.calendar import get_icloud_calendar_events
from startpage.components.currency import get_currency_rates
from startpage.components.fact import get_random_fact
from startpage.components.rss import Feed, fetch_feed
from startpage.components.weather import get_weather
from startpage.utils.blocks import (
    append_block_to_page,
    create_header_1_block,
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for StartPage application.

    Orchestrates the following tasks concurrently:
    - Fetches weather information for configured city
    - Fetches currency and cryptocurrency rates
    - Retrieves iCloud calendar events for today
    - Aggregates RSS feed articles from multiple sources
    - Fetches a random fact

    All data is formatted as Notion blocks and appended to the configured
    Notion page.

    Raises:
        ValueError: If required environment variables are not set.
        Exception: If any component fails to fetch or process data.
    """
    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting StartPage application")
    notion = AsyncClient(auth=os.environ["NOTION_TOKEN"])
    page_id = os.environ.get("PAGE_ID")
    city = os.environ.get("CITY")
    block_id = os.environ.get("BLOCK_ID")
    if not city or not page_id or not block_id:
        raise ValueError("CITY, PAGE_ID, and BLOCK_ID must be set")

    username = os.environ.get("ICLOUD_USERNAME")
    password = os.environ.get("ICLOUD_APP_PASSWORD")
    if not username or not password:
        raise ValueError("ICLOUD_USERNAME and ICLOUD_APP_PASSWORD must be set")

    timezone = os.environ.get("TIMEZONE", "UTC")

    now = datetime.datetime.now()
    formatted_date = now.strftime("%A %d of %B")

    feeds = [
        Feed(name="TechCrunch", url="https://techcrunch.com/feed/", priority=2),
        Feed(name="BigThinking", url="https://bigthinking.io/feed", priority=1),
        Feed(name="Product Hunt", url="https://www.producthunt.com/feed", priority=2),
        Feed(
            name="Hacker News Launches",
            url="https://news.ycombinator.com/launches",
            priority=1,
        ),
        Feed(
            name="Andrew Chen", url="https://andrewchen.substack.com/feed", priority=1
        ),
        Feed(
            name="Benedict Evans",
            url="http://ben-evans.com/benedictevans?format=rss",
            priority=1,
        ),
        Feed(
            name="Irrational Exuberance",
            url="https://irrationalexuberance.libsyn.com/rss",
            priority=1,
        ),
        Feed(
            name="Pragmatic Engineer",
            url="https://pragmaticengineer.com/feed/",
            priority=1,
        ),
        Feed(
            name="Peter Steinberger",
            url="https://steipete.me/rss.xml",
            priority=1,
        ),
        Feed(
            name="Mario Zechner",
            url="https://mariozechner.at/rss.xml",
            priority=1,
        ),
    ]
    banned_tags = {"sponsored", "advertisement", "government & policy", "smartglasses"}

    tasks = [
        get_weather(city),
        get_currency_rates("Currencies (₽)", "rub", ["usd", "eur"]),
        get_currency_rates("Cryptocurrencies ($)", "usd", ["btc", "eth"]),
        get_icloud_calendar_events(
            "Today's Events", username=username, password=password, timezone=timezone
        ),
        fetch_feed("Tech News", feeds, banned_tags=banned_tags, max_articles=5),
        get_random_fact(),
    ]

    logger.info("Fetching data from all sources concurrently")
    results = await asyncio.gather(*tasks)

    weather_block, currency_blocks, crypto_blocks, calendar_events, rss_block, fact = (
        results
    )

    logger.info("All data fetched successfully, building Notion page")
    children = [*weather_block]
    children.extend(currency_blocks)
    children.extend(crypto_blocks)
    children.extend(calendar_events)
    children.extend(rss_block)
    new_day = create_header_1_block(formatted_date, children)

    logger.info(f"Appending new day section: {formatted_date}")
    await append_block_to_page(notion, page_id, new_day, after=block_id)

    logger.info("Updating fact block")
    await notion.blocks.update(
        block_id, callout={"rich_text": [{"text": {"content": fact}}]}
    )

    logger.info("StartPage update completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
