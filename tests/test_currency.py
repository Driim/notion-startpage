from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.startpage.components.currency import get_currency_rates


@pytest.mark.asyncio
async def test_get_currency_rates_success():
    """Test get_currency_rates for a successful API call."""
    mock_response_data = {"rub": {"usd": 0.013, "eur": 0.011}}

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = mock_response_data

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        )
    )

    with patch("aiohttp.ClientSession", return_value=mock_session):
        blocks = await get_currency_rates(
            text="Курсы", base="rub", targets=["usd", "eur"]
        )

        assert len(blocks) == 3
        assert blocks[0]["type"] == "heading_2"
        assert blocks[0]["heading_2"]["rich_text"][0]["text"]["content"] == "Курсы"

        assert blocks[1]["type"] == "bulleted_list_item"
        assert (
            blocks[1]["bulleted_list_item"]["rich_text"][0]["text"]["content"]
            == "1 USD = 76.92 RUB"
        )

        assert blocks[2]["type"] == "bulleted_list_item"
        assert (
            blocks[2]["bulleted_list_item"]["rich_text"][0]["text"]["content"]
            == "1 EUR = 90.91 RUB"
        )

        mock_session.get.assert_called_once_with(
            "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/rub.json"
        )


@pytest.mark.asyncio
async def test_get_currency_rates_with_date():
    """Test get_currency_rates with a specific date."""
    mock_response_data = {"rub": {"usd": 0.013}}

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = mock_response_data

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        )
    )

    with patch("aiohttp.ClientSession", return_value=mock_session):
        await get_currency_rates(
            text="Курсы", base="rub", targets=["usd"], date="2023-01-01"
        )

        mock_session.get.assert_called_once_with(
            "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@2023-01-01/v1/currencies/rub.json"
        )


@pytest.mark.asyncio
async def test_get_currency_rates_api_error():
    """Test get_currency_rates for a non-200 status code."""
    mock_response = AsyncMock()
    mock_response.status = 404

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        )
    )

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(Exception, match="Failed to fetch currency data: 404"):
            await get_currency_rates(text="Курсы", base="rub", targets=["usd"])


@pytest.mark.asyncio
async def test_get_currency_rates_target_not_available():
    """Test get_currency_rates when a target currency is not in the response."""
    mock_response_data = {"rub": {"usd": 0.013}}

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = mock_response_data

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        )
    )

    with patch("aiohttp.ClientSession", return_value=mock_session):
        blocks = await get_currency_rates(text="Курсы", base="rub", targets=["eur"])

        assert len(blocks) == 2
        assert blocks[1]["type"] == "bulleted_list_item"
        assert (
            blocks[1]["bulleted_list_item"]["rich_text"][0]["text"]["content"]
            == "Rate for EUR not available"
        )
