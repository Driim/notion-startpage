import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.startpage.components.weather import get_wind_arrow, get_weather


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
async def test_get_weather_success():
    """Test get_weather for a successful API call."""
    # Create mock weather object
    mock_kind = MagicMock()
    mock_kind.name = "SUNNY"

    mock_wind_direction = MagicMock()
    mock_wind_direction.name = "NORTH"

    mock_daily_forecast = MagicMock()
    mock_daily_forecast.lowest_temperature = 15
    mock_daily_forecast.highest_temperature = 25

    mock_weather = MagicMock()
    mock_weather.kind = mock_kind
    mock_weather.wind_direction = mock_wind_direction
    mock_weather.daily_forecasts = [mock_daily_forecast]
    mock_weather.humidity = 60
    mock_weather.precipitation = 5.0
    mock_weather.wind_speed = 10

    # Create mock client
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_weather)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("python_weather.Client", return_value=mock_client):
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

        mock_client.get.assert_called_once_with("Moscow")


@pytest.mark.asyncio
async def test_get_weather_with_cloudy():
    """Test get_weather with cloudy weather."""
    mock_kind = MagicMock()
    mock_kind.name = "CLOUDY"

    mock_wind_direction = MagicMock()
    mock_wind_direction.name = "EAST"

    mock_daily_forecast = MagicMock()
    mock_daily_forecast.lowest_temperature = 10
    mock_daily_forecast.highest_temperature = 18

    mock_weather = MagicMock()
    mock_weather.kind = mock_kind
    mock_weather.wind_direction = mock_wind_direction
    mock_weather.daily_forecasts = [mock_daily_forecast]
    mock_weather.humidity = 75
    mock_weather.precipitation = 0
    mock_weather.wind_speed = 15

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_weather)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("python_weather.Client", return_value=mock_client):
        blocks = await get_weather("London")

        assert "☁️ London" in blocks[0]["heading_2"]["rich_text"][0]["text"]["content"]
        weather_info = blocks[1]["paragraph"]["rich_text"][0]["text"]["content"]
        assert "Wind: 15km/h →" in weather_info


@pytest.mark.asyncio
async def test_get_weather_with_unknown_kind():
    """Test get_weather with unknown weather kind."""
    mock_kind = MagicMock()
    mock_kind.name = "UNKNOWN_WEATHER_TYPE"

    mock_wind_direction = MagicMock()
    mock_wind_direction.name = "SOUTH"

    mock_daily_forecast = MagicMock()
    mock_daily_forecast.lowest_temperature = 5
    mock_daily_forecast.highest_temperature = 12

    mock_weather = MagicMock()
    mock_weather.kind = mock_kind
    mock_weather.wind_direction = mock_wind_direction
    mock_weather.daily_forecasts = [mock_daily_forecast]
    mock_weather.humidity = 50
    mock_weather.precipitation = 0
    mock_weather.wind_speed = 5

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_weather)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("python_weather.Client", return_value=mock_client):
        blocks = await get_weather("Berlin")

        # Should use default symbol for unknown weather
        assert "❓ Berlin" in blocks[0]["heading_2"]["rich_text"][0]["text"]["content"]


@pytest.mark.asyncio
async def test_get_weather_with_unknown_wind_direction():
    """Test get_weather with unknown wind direction."""
    mock_kind = MagicMock()
    mock_kind.name = "SUNNY"

    mock_wind_direction = MagicMock()
    mock_wind_direction.name = "UNKNOWN_DIRECTION"

    mock_daily_forecast = MagicMock()
    mock_daily_forecast.lowest_temperature = 20
    mock_daily_forecast.highest_temperature = 30

    mock_weather = MagicMock()
    mock_weather.kind = mock_kind
    mock_weather.wind_direction = mock_wind_direction
    mock_weather.daily_forecasts = [mock_daily_forecast]
    mock_weather.humidity = 40
    mock_weather.precipitation = 0
    mock_weather.wind_speed = 8

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_weather)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("python_weather.Client", return_value=mock_client):
        blocks = await get_weather("Tokyo")

        weather_info = blocks[1]["paragraph"]["rich_text"][0]["text"]["content"]
        # Should use default arrow for unknown direction
        assert "Wind: 8km/h ?" in weather_info


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "weather_kind,expected_symbol",
    [
        ("SUNNY", "☀️"),
        ("CLOUDY", "☁️"),
        ("HEAVY_RAIN", "🌧"),
        ("LIGHT_SNOW", "🌨"),
        ("PARTLY_CLOUDY", "⛅️"),
        ("FOG", "🌫"),
    ],
)
async def test_get_weather_symbols(weather_kind, expected_symbol):
    """Test get_weather returns correct symbols for different weather types."""
    mock_kind = MagicMock()
    mock_kind.name = weather_kind

    mock_wind_direction = MagicMock()
    mock_wind_direction.name = "NORTH"

    mock_daily_forecast = MagicMock()
    mock_daily_forecast.lowest_temperature = 10
    mock_daily_forecast.highest_temperature = 20

    mock_weather = MagicMock()
    mock_weather.kind = mock_kind
    mock_weather.wind_direction = mock_wind_direction
    mock_weather.daily_forecasts = [mock_daily_forecast]
    mock_weather.humidity = 50
    mock_weather.precipitation = 0
    mock_weather.wind_speed = 5

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_weather)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("python_weather.Client", return_value=mock_client):
        blocks = await get_weather("TestCity")

        assert (
            expected_symbol in blocks[0]["heading_2"]["rich_text"][0]["text"]["content"]
        )
