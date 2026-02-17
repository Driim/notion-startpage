"""Weather information fetching and formatting component.

This module fetches current weather data for a specified city and formats it
as Notion blocks with emoji representations of weather conditions.
"""

import logging

import aiohttp

logger = logging.getLogger(__name__)

WMO_WEATHER_SYMBOL = {
    0: "☀️",
    1: "🌤",
    2: "⛅️",
    3: "☁️",
    45: "🌫",
    48: "🌫",
    51: "🌦",
    53: "🌦",
    55: "🌧",
    56: "🌧",
    57: "🌧",
    61: "🌦",
    63: "🌧",
    65: "🌧",
    66: "🌧",
    67: "🌧",
    71: "🌨",
    73: "❄️",
    75: "❄️",
    77: "❄️",
    80: "🌦",
    81: "🌧",
    82: "🌧",
    85: "🌨",
    86: "❄️",
    95: "⛈",
    96: "⛈",
    99: "⛈",
}


def get_wind_arrow(deg: float) -> str:
    """Convert wind direction in degrees to arrow emoji.

    Args:
        deg: Wind direction in degrees (0-360).

    Returns:
        Arrow emoji representing the wind direction.
    """
    directions = [
        "↑",
        "↑",
        "↗",
        "↗",
        "→",
        "↘",
        "↘",
        "↘",
        "↓",
        "↙",
        "↙",
        "↙",
        "←",
        "↖",
        "↖",
        "↖",
    ]
    index = round(deg / 22.5) % 16
    return directions[index]


async def get_coordinates(city: str) -> tuple[float, float]:
    """Convert city name to latitude/longitude coordinates using Open-Meteo Geocoding API.

    Args:
        city: City name to geocode.

    Returns:
        Tuple of (latitude, longitude) coordinates.

    Raises:
        ValueError: If city is not found.
        aiohttp.ClientError: If network request fails.
    """
    geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1, "language": "en", "format": "json"}

    async with aiohttp.ClientSession() as session:
        async with session.get(geocoding_url, params=params) as response:
            response.raise_for_status()
            data = await response.json()

            if not data.get("results"):
                logger.error(f"City not found: {city}")
                raise ValueError(f"City not found: {city}")

            result = data["results"][0]
            latitude = result["latitude"]
            longitude = result["longitude"]
            logger.info(f"Geocoded {city} to coordinates: {latitude}, {longitude}")
            return latitude, longitude


async def get_weather(city: str) -> list:
    """Fetch weather data for a city and format as Notion blocks.

    Args:
        city: City name to fetch weather for.

    Returns:
        List of two Notion block dictionaries: header with weather emoji and
        paragraph with detailed weather information.

    Raises:
        ValueError: If city is not found.
        aiohttp.ClientError: If API request fails.
    """
    try:
        latitude, longitude = await get_coordinates(city)

        weather_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "auto",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(weather_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                current = data["current"]
                daily = data["daily"]

                weather_code = current["weather_code"]
                weather_symbol = WMO_WEATHER_SYMBOL.get(weather_code, "❓")

                wind_direction_deg = current["wind_direction_10m"]
                wind_arrow = get_wind_arrow(wind_direction_deg)

                lowest_temp = int(daily["temperature_2m_min"][0])
                highest_temp = int(daily["temperature_2m_max"][0])
                humidity = int(current["relative_humidity_2m"])
                precipitation = current["precipitation"]
                wind_speed = int(current["wind_speed_10m"])

                weather_info = f"{lowest_temp}°C - {highest_temp}°C "
                weather_info += (
                    f"Humidity: {humidity}% Precipitation: {precipitation}mm "
                )
                weather_info += f"Wind: {wind_speed}km/h {wind_arrow}"

                logger.info(f"Successfully fetched weather for {city}")

                return [
                    {
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": f"{weather_symbol} {city}"},
                                }
                            ]
                        },
                    },
                    {
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"type": "text", "text": {"content": weather_info}}
                            ]
                        },
                    },
                ]
    except ValueError as e:
        logger.error(f"Error fetching weather for {city}: {e}")
        raise
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching weather for {city}: {e}")
        raise
    except KeyError as e:
        logger.error(f"Unexpected API response format for {city}: {e}")
        raise ValueError(f"Invalid API response: missing field {e}")
