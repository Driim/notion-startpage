from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.startpage.components.fact import get_random_fact


@pytest.mark.asyncio
async def test_get_random_fact_success():
    """Test get_random_fact for a successful API call."""
    mock_response_data = {"text": "Cats sleep 70% of their lives."}

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
        fact = await get_random_fact()

        assert fact == "Cats sleep 70% of their lives."
        mock_session.get.assert_called_once_with(
            "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en",
            headers={"Accept": "application/json"},
        )


@pytest.mark.asyncio
async def test_get_random_fact_with_whitespace():
    """Test get_random_fact strips whitespace from the fact text."""
    mock_response_data = {"text": "  Some fact with spaces.  \n"}

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
        fact = await get_random_fact()

        assert fact == "Some fact with spaces."


@pytest.mark.asyncio
async def test_get_random_fact_missing_text_field():
    """Test get_random_fact when 'text' field is missing from response."""
    mock_response_data = {"other_field": "value"}

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
        fact = await get_random_fact()

        assert fact == ""


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [404, 500, 503])
async def test_get_random_fact_api_error(status_code):
    """Test get_random_fact for various API error status codes."""
    mock_response = AsyncMock()
    mock_response.status = status_code

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
        with pytest.raises(Exception, match=f"Failed to fetch fact: {status_code}"):
            await get_random_fact()
