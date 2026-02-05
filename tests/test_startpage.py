"""Tests for main StartPage orchestration."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.startpage.startpage import main


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables."""
    env_vars = {
        "NOTION_TOKEN": "test_token_123",
        "PAGE_ID": "test_page_id",
        "BLOCK_ID": "test_block_id",
        "CITY": "London",
        "ICLOUD_USERNAME": "test@example.com",
        "ICLOUD_APP_PASSWORD": "test_password",
        "TIMEZONE": "Europe/London",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


@pytest.mark.asyncio
@patch("src.startpage.startpage.AsyncClient")
@patch("src.startpage.startpage.get_weather")
@patch("src.startpage.startpage.get_currency_rates")
@patch("src.startpage.startpage.get_icloud_calendar_events")
@patch("src.startpage.startpage.fetch_feed")
@patch("src.startpage.startpage.get_random_fact")
@patch("src.startpage.startpage.append_block_to_page")
@patch("src.startpage.startpage.load_dotenv")
async def test_main_success(
    mock_load_dotenv,
    mock_append,
    mock_fact,
    mock_rss,
    mock_calendar,
    mock_currency,
    mock_weather,
    mock_client,
    mock_env_vars,
):
    """Test successful execution of main function."""
    # Setup mocks
    mock_notion = MagicMock()
    mock_notion.blocks.update = AsyncMock()
    mock_client.return_value = mock_notion

    # Mock component responses
    mock_weather.return_value = [
        {
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "☀️ London"}}]},
        }
    ]
    mock_currency.return_value = [
        {
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "Currencies"}}]},
        }
    ]
    mock_calendar.return_value = [
        {
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "Events"}}]},
        }
    ]
    mock_rss.return_value = [
        {
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "Tech News"}}]},
        }
    ]
    mock_fact.return_value = "Interesting fact of the day"
    mock_append.return_value = None

    # Execute main
    await main()

    # Verify all components were called
    mock_load_dotenv.assert_called_once()
    mock_weather.assert_called_once_with("London")
    assert mock_currency.call_count == 2  # Called for currencies and crypto
    mock_calendar.assert_called_once()
    mock_rss.assert_called_once()
    mock_fact.assert_called_once()
    mock_append.assert_called_once()
    mock_notion.blocks.update.assert_called_once()


@pytest.mark.asyncio
@patch("src.startpage.startpage.load_dotenv")
async def test_main_missing_city_env_var(mock_load_dotenv, monkeypatch):
    """Test main raises ValueError when CITY is missing."""
    monkeypatch.setenv("NOTION_TOKEN", "test_token")
    monkeypatch.setenv("PAGE_ID", "test_page")
    monkeypatch.setenv("BLOCK_ID", "test_block")
    monkeypatch.delenv("CITY", raising=False)

    with pytest.raises(ValueError, match="CITY, PAGE_ID, and BLOCK_ID must be set"):
        await main()


@pytest.mark.asyncio
@patch("src.startpage.startpage.load_dotenv")
async def test_main_missing_page_id(mock_load_dotenv, monkeypatch):
    """Test main raises ValueError when PAGE_ID is missing."""
    monkeypatch.setenv("NOTION_TOKEN", "test_token")
    monkeypatch.setenv("CITY", "London")
    monkeypatch.setenv("BLOCK_ID", "test_block")
    monkeypatch.delenv("PAGE_ID", raising=False)

    with pytest.raises(ValueError, match="CITY, PAGE_ID, and BLOCK_ID must be set"):
        await main()


@pytest.mark.asyncio
@patch("src.startpage.startpage.load_dotenv")
async def test_main_missing_block_id(mock_load_dotenv, monkeypatch):
    """Test main raises ValueError when BLOCK_ID is missing."""
    monkeypatch.setenv("NOTION_TOKEN", "test_token")
    monkeypatch.setenv("CITY", "London")
    monkeypatch.setenv("PAGE_ID", "test_page")
    monkeypatch.delenv("BLOCK_ID", raising=False)

    with pytest.raises(ValueError, match="CITY, PAGE_ID, and BLOCK_ID must be set"):
        await main()


@pytest.mark.asyncio
@patch("src.startpage.startpage.load_dotenv")
async def test_main_missing_icloud_username(mock_load_dotenv, monkeypatch):
    """Test main raises ValueError when ICLOUD_USERNAME is missing."""
    monkeypatch.setenv("NOTION_TOKEN", "test_token")
    monkeypatch.setenv("CITY", "London")
    monkeypatch.setenv("PAGE_ID", "test_page")
    monkeypatch.setenv("BLOCK_ID", "test_block")
    monkeypatch.setenv("ICLOUD_APP_PASSWORD", "password")
    monkeypatch.delenv("ICLOUD_USERNAME", raising=False)

    with pytest.raises(
        ValueError, match="ICLOUD_USERNAME and ICLOUD_APP_PASSWORD must be set"
    ):
        await main()


@pytest.mark.asyncio
@patch("src.startpage.startpage.load_dotenv")
async def test_main_missing_icloud_password(mock_load_dotenv, monkeypatch):
    """Test main raises ValueError when ICLOUD_APP_PASSWORD is missing."""
    monkeypatch.setenv("NOTION_TOKEN", "test_token")
    monkeypatch.setenv("CITY", "London")
    monkeypatch.setenv("PAGE_ID", "test_page")
    monkeypatch.setenv("BLOCK_ID", "test_block")
    monkeypatch.setenv("ICLOUD_USERNAME", "test@example.com")
    monkeypatch.delenv("ICLOUD_APP_PASSWORD", raising=False)

    with pytest.raises(
        ValueError, match="ICLOUD_USERNAME and ICLOUD_APP_PASSWORD must be set"
    ):
        await main()


@pytest.mark.asyncio
@patch("src.startpage.startpage.AsyncClient")
@patch("src.startpage.startpage.get_weather")
@patch("src.startpage.startpage.get_currency_rates")
@patch("src.startpage.startpage.get_icloud_calendar_events")
@patch("src.startpage.startpage.fetch_feed")
@patch("src.startpage.startpage.get_random_fact")
@patch("src.startpage.startpage.append_block_to_page")
@patch("src.startpage.startpage.load_dotenv")
async def test_main_uses_default_timezone(
    mock_load_dotenv,
    mock_append,
    mock_fact,
    mock_rss,
    mock_calendar,
    mock_currency,
    mock_weather,
    mock_client,
    monkeypatch,
):
    """Test main uses UTC as default timezone when not specified."""
    # Setup minimal env vars
    monkeypatch.setenv("NOTION_TOKEN", "test_token")
    monkeypatch.setenv("CITY", "London")
    monkeypatch.setenv("PAGE_ID", "test_page")
    monkeypatch.setenv("BLOCK_ID", "test_block")
    monkeypatch.setenv("ICLOUD_USERNAME", "test@example.com")
    monkeypatch.setenv("ICLOUD_APP_PASSWORD", "test_password")
    monkeypatch.delenv("TIMEZONE", raising=False)

    # Setup mocks
    mock_notion = MagicMock()
    mock_notion.blocks.update = AsyncMock()
    mock_client.return_value = mock_notion

    mock_weather.return_value = [{}]
    mock_currency.return_value = [{}]
    mock_calendar.return_value = [{}]
    mock_rss.return_value = [{}]
    mock_fact.return_value = "fact"
    mock_append.return_value = None

    await main()

    # Verify calendar was called with UTC timezone
    call_kwargs = mock_calendar.call_args.kwargs
    assert call_kwargs["timezone"] == "UTC"


@pytest.mark.asyncio
@patch("src.startpage.startpage.AsyncClient")
@patch("src.startpage.startpage.get_weather")
@patch("src.startpage.startpage.get_currency_rates")
@patch("src.startpage.startpage.get_icloud_calendar_events")
@patch("src.startpage.startpage.fetch_feed")
@patch("src.startpage.startpage.get_random_fact")
@patch("src.startpage.startpage.append_block_to_page")
@patch("src.startpage.startpage.load_dotenv")
async def test_main_concurrent_execution(
    mock_load_dotenv,
    mock_append,
    mock_fact,
    mock_rss,
    mock_calendar,
    mock_currency,
    mock_weather,
    mock_client,
    mock_env_vars,
):
    """Test that main executes all component tasks concurrently."""
    # Setup mocks
    mock_notion = MagicMock()
    mock_notion.blocks.update = AsyncMock()
    mock_client.return_value = mock_notion

    # Create async functions that track call order
    call_order = []

    async def weather_fn(*args, **kwargs):
        call_order.append("weather")
        await asyncio.sleep(0.01)
        return [{}]

    async def currency_fn(*args, **kwargs):
        call_order.append("currency")
        await asyncio.sleep(0.01)
        return [{}]

    async def calendar_fn(*args, **kwargs):
        call_order.append("calendar")
        await asyncio.sleep(0.01)
        return [{}]

    async def rss_fn(*args, **kwargs):
        call_order.append("rss")
        await asyncio.sleep(0.01)
        return [{}]

    async def fact_fn(*args, **kwargs):
        call_order.append("fact")
        await asyncio.sleep(0.01)
        return "fact"

    mock_weather.side_effect = weather_fn
    mock_currency.side_effect = currency_fn
    mock_calendar.side_effect = calendar_fn
    mock_rss.side_effect = rss_fn
    mock_fact.side_effect = fact_fn
    mock_append.return_value = None

    await main()

    # Verify all components were called (order doesn't matter with asyncio.gather)
    assert len(call_order) >= 5  # weather, 2x currency, calendar, rss, fact


@pytest.mark.asyncio
@patch("src.startpage.startpage.AsyncClient")
@patch("src.startpage.startpage.get_weather")
@patch("src.startpage.startpage.get_currency_rates")
@patch("src.startpage.startpage.get_icloud_calendar_events")
@patch("src.startpage.startpage.fetch_feed")
@patch("src.startpage.startpage.get_random_fact")
@patch("src.startpage.startpage.load_dotenv")
async def test_main_passes_correct_rss_feeds(
    mock_load_dotenv,
    mock_fact,
    mock_rss,
    mock_calendar,
    mock_currency,
    mock_weather,
    mock_client,
    mock_env_vars,
):
    """Test that main passes correct RSS feed configuration."""
    # Setup mocks
    mock_notion = MagicMock()
    mock_notion.blocks.update = AsyncMock()
    mock_client.return_value = mock_notion

    mock_weather.return_value = [{}]
    mock_currency.return_value = [{}]
    mock_calendar.return_value = [{}]
    mock_rss.return_value = [{}]
    mock_fact.return_value = "fact"

    # Mock append_block_to_page to avoid issues
    with patch("src.startpage.startpage.append_block_to_page"):
        await main()

    # Verify RSS was called with correct parameters
    assert mock_rss.called
    call_args = mock_rss.call_args
    assert call_args.args[0] == "Tech News"
    feeds = call_args.args[1]
    assert len(feeds) > 0
    assert all(hasattr(feed, "name") and hasattr(feed, "url") for feed in feeds)
    banned_tags = call_args.kwargs["banned_tags"]
    assert "sponsored" in banned_tags
    assert call_args.kwargs["max_articles"] == 5


@pytest.mark.asyncio
@patch("src.startpage.startpage.AsyncClient")
@patch("src.startpage.startpage.get_weather")
@patch("src.startpage.startpage.get_currency_rates")
@patch("src.startpage.startpage.get_icloud_calendar_events")
@patch("src.startpage.startpage.fetch_feed")
@patch("src.startpage.startpage.get_random_fact")
@patch("src.startpage.startpage.append_block_to_page")
@patch("src.startpage.startpage.load_dotenv")
async def test_main_updates_fact_block(
    mock_load_dotenv,
    mock_append,
    mock_fact,
    mock_rss,
    mock_calendar,
    mock_currency,
    mock_weather,
    mock_client,
    mock_env_vars,
):
    """Test that main updates the fact block correctly."""
    # Setup mocks
    mock_notion = MagicMock()
    mock_notion.blocks.update = AsyncMock()
    mock_client.return_value = mock_notion

    mock_weather.return_value = [{}]
    mock_currency.return_value = [{}]
    mock_calendar.return_value = [{}]
    mock_rss.return_value = [{}]
    test_fact = "This is a test fact"
    mock_fact.return_value = test_fact
    mock_append.return_value = None

    await main()

    # Verify fact block was updated with correct content
    mock_notion.blocks.update.assert_called_once()
    call_args = mock_notion.blocks.update.call_args
    assert call_args.args[0] == "test_block_id"
    assert call_args.kwargs["callout"]["rich_text"][0]["text"]["content"] == test_fact
