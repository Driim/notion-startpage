import asyncio
import datetime
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


async def main():
    load_dotenv()

    notion = AsyncClient(auth=os.environ["NOTION_TOKEN"])
    page_id = os.environ["PAGE_ID"]
    city = os.environ["CITY"]
    block_id = os.environ["BLOCK_ID"]
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

    results = await asyncio.gather(*tasks)

    weather_block, currency_blocks, crypto_blocks, calendar_events, rss_block, fact = (
        results
    )

    children = [*weather_block]
    children.extend(currency_blocks)
    children.extend(crypto_blocks)
    children.extend(calendar_events)
    children.extend(rss_block)
    new_day = create_header_1_block(formatted_date, children)

    await append_block_to_page(notion, page_id, new_day, after=block_id)
    await notion.blocks.update(
        block_id, callout={"rich_text": [{"text": {"content": fact}}]}
    )


if __name__ == "__main__":
    asyncio.run(main())
