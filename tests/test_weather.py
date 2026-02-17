from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from src.startpage.components.weather import (
    get_coordinates,
    get_weather,
    get_wind_arrow,
)


@pytest.mark.parametrize(
    "degrees,expected_arrow",
    [
        (0, "↑"),  # North
        (22.5, "↑"),  # North
        (45, "↗"),  # Northeast
        (67.5, "↗"),  # Northeast
        (90, "→"),  # East
        (112.5, "↘"),  # Southeast
        (135, "↘"),  # Southeast
        (157.5, "↘"),  # Southeast
        (180, "↓"),  # South
        (202.5, "↙"),  # Southwest
        (225, "↙"),  # Southwest
        (247.5, "↙"),  # Southwest
        (270, "←"),  # West
        (292.5, "↖"),  # Northwest
        (315, "↖"),  # Northwest
        (337.5, "↖"),  # Northwest
        (360, "↑"),  # Full circle = North
    ],
)
def test_get_wind_arrow(degrees, expected_arrow):
    """Test get_wind_arrow returns correct arrow for various degrees."""
    assert get_wind_arrow(degrees) == expected_arrow


@pytest.mark.asyncio
async def test_get_coordinates_success():
    """Test get_coordinates for a successful API call."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "results": [{"latitude": 55.7558, "longitude": 37.6173, "name": "Moscow"}]
        }
    )
    mock_response.raise_for_status = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        lat, lon = await get_coordinates("Moscow")
        assert lat == 55.7558
        assert lon == 37.6173


@pytest.mark.asyncio
async def test_get_coordinates_city_not_found():
    """Test get_coordinates when city is not found."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"results": []})
    mock_response.raise_for_status = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(ValueError, match="City not found"):
            await get_coordinates("InvalidCity123456")


@pytest.mark.asyncio
async def test_get_weather_success():
    """Test get_weather for a successful API call."""
    geocoding_response = AsyncMock()
    geocoding_response.status = 200
    geocoding_response.json = AsyncMock(
        return_value={
            "results": [{"latitude": 55.7558, "longitude": 37.6173, "name": "Moscow"}]
        }
    )
    geocoding_response.raise_for_status = MagicMock()
    geocoding_response.__aenter__ = AsyncMock(return_value=geocoding_response)
    geocoding_response.__aexit__ = AsyncMock(return_value=None)

    weather_response = AsyncMock()
    weather_response.status = 200
    weather_response.json = AsyncMock(
        return_value={
            "current": {
                "temperature_2m": 20.0,
                "relative_humidity_2m": 60,
                "precipitation": 5.0,
                "weather_code": 0,
                "wind_speed_10m": 10.0,
                "wind_direction_10m": 0.0,
            },
            "daily": {"temperature_2m_max": [25.0], "temperature_2m_min": [15.0]},
        }
    )
    weather_response.raise_for_status = MagicMock()
    weather_response.__aenter__ = AsyncMock(return_value=weather_response)
    weather_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(side_effect=[geocoding_response, weather_response])
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        blocks = await get_weather("Moscow")

        assert len(blocks) == 2
        assert blocks[0]["type"] == "heading_2"
        assert "☀️ Moscow" in blocks[0]["heading_2"]["rich_text"][0]["text"]["content"]

        assert blocks[1]["type"] == "paragraph"
        weather_info = blocks[1]["paragraph"]["rich_text"][0]["text"]["content"]
        assert "15°C - 25°C" in weather_info
        assert "Humidity: 60%" in weather_info
        assert "Precipitation: 5.0mm" in weather_info
        assert "Wind: 10km/h ↑" in weather_info


@pytest.mark.asyncio
async def test_get_weather_with_cloudy():
    """Test get_weather with cloudy weather."""
    geocoding_response = AsyncMock()
    geocoding_response.status = 200
    geocoding_response.json = AsyncMock(
        return_value={
            "results": [{"latitude": 51.5074, "longitude": -0.1278, "name": "London"}]
        }
    )
    geocoding_response.raise_for_status = MagicMock()
    geocoding_response.__aenter__ = AsyncMock(return_value=geocoding_response)
    geocoding_response.__aexit__ = AsyncMock(return_value=None)

    weather_response = AsyncMock()
    weather_response.status = 200
    weather_response.json = AsyncMock(
        return_value={
            "current": {
                "temperature_2m": 14.0,
                "relative_humidity_2m": 75,
                "precipitation": 0.0,
                "weather_code": 3,
                "wind_speed_10m": 15.0,
                "wind_direction_10m": 90.0,
            },
            "daily": {"temperature_2m_max": [18.0], "temperature_2m_min": [10.0]},
        }
    )
    weather_response.raise_for_status = MagicMock()
    weather_response.__aenter__ = AsyncMock(return_value=weather_response)
    weather_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(side_effect=[geocoding_response, weather_response])
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        blocks = await get_weather("London")

        assert "☁️ London" in blocks[0]["heading_2"]["rich_text"][0]["text"]["content"]
        weather_info = blocks[1]["paragraph"]["rich_text"][0]["text"]["content"]
        assert "Wind: 15km/h →" in weather_info


@pytest.mark.asyncio
async def test_get_weather_with_unknown_kind():
    """Test get_weather with unknown weather code."""
    geocoding_response = AsyncMock()
    geocoding_response.status = 200
    geocoding_response.json = AsyncMock(
        return_value={
            "results": [{"latitude": 52.5200, "longitude": 13.4050, "name": "Berlin"}]
        }
    )
    geocoding_response.raise_for_status = MagicMock()
    geocoding_response.__aenter__ = AsyncMock(return_value=geocoding_response)
    geocoding_response.__aexit__ = AsyncMock(return_value=None)

    weather_response = AsyncMock()
    weather_response.status = 200
    weather_response.json = AsyncMock(
        return_value={
            "current": {
                "temperature_2m": 8.0,
                "relative_humidity_2m": 50,
                "precipitation": 0.0,
                "weather_code": 999,
                "wind_speed_10m": 5.0,
                "wind_direction_10m": 180.0,
            },
            "daily": {"temperature_2m_max": [12.0], "temperature_2m_min": [5.0]},
        }
    )
    weather_response.raise_for_status = MagicMock()
    weather_response.__aenter__ = AsyncMock(return_value=weather_response)
    weather_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(side_effect=[geocoding_response, weather_response])
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        blocks = await get_weather("Berlin")

        assert "❓ Berlin" in blocks[0]["heading_2"]["rich_text"][0]["text"]["content"]


@pytest.mark.asyncio
async def test_get_weather_network_error():
    """Test get_weather handles network errors."""
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock(
        side_effect=aiohttp.ClientError("Network error")
    )
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(aiohttp.ClientError):
            await get_weather("Tokyo")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "weather_code,expected_symbol",
    [
        (0, "☀️"),
        (3, "☁️"),
        (65, "🌧"),
        (71, "🌨"),
        (2, "⛅️"),
        (45, "🌫"),
        (95, "⛈"),
        (73, "❄️"),
    ],
)
async def test_get_weather_symbols(weather_code, expected_symbol):
    """Test get_weather returns correct symbols for different WMO weather codes."""
    geocoding_response = AsyncMock()
    geocoding_response.status = 200
    geocoding_response.json = AsyncMock(
        return_value={
            "results": [
                {"latitude": 40.7128, "longitude": -74.0060, "name": "TestCity"}
            ]
        }
    )
    geocoding_response.raise_for_status = MagicMock()
    geocoding_response.__aenter__ = AsyncMock(return_value=geocoding_response)
    geocoding_response.__aexit__ = AsyncMock(return_value=None)

    weather_response = AsyncMock()
    weather_response.status = 200
    weather_response.json = AsyncMock(
        return_value={
            "current": {
                "temperature_2m": 15.0,
                "relative_humidity_2m": 50,
                "precipitation": 0.0,
                "weather_code": weather_code,
                "wind_speed_10m": 5.0,
                "wind_direction_10m": 0.0,
            },
            "daily": {"temperature_2m_max": [20.0], "temperature_2m_min": [10.0]},
        }
    )
    weather_response.raise_for_status = MagicMock()
    weather_response.__aenter__ = AsyncMock(return_value=weather_response)
    weather_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(side_effect=[geocoding_response, weather_response])
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        blocks = await get_weather("TestCity")

        assert (
            expected_symbol in blocks[0]["heading_2"]["rich_text"][0]["text"]["content"]
        )


@pytest.mark.asyncio
async def test_get_weather_malformed_response():
    """Test get_weather handles malformed API response."""
    geocoding_response = AsyncMock()
    geocoding_response.status = 200
    geocoding_response.json = AsyncMock(
        return_value={
            "results": [{"latitude": 40.7128, "longitude": -74.0060, "name": "NYC"}]
        }
    )
    geocoding_response.raise_for_status = MagicMock()
    geocoding_response.__aenter__ = AsyncMock(return_value=geocoding_response)
    geocoding_response.__aexit__ = AsyncMock(return_value=None)

    weather_response = AsyncMock()
    weather_response.status = 200
    weather_response.json = AsyncMock(return_value={"current": {}})
    weather_response.raise_for_status = MagicMock()
    weather_response.__aenter__ = AsyncMock(return_value=weather_response)
    weather_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(side_effect=[geocoding_response, weather_response])
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(ValueError, match="Invalid API response"):
            await get_weather("NYC")
