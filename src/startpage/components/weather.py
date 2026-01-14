import python_weather

# TODO: change symbols to more detailed ones
WEATHER_SYMBOL = {
    "UNKNOWN": "✨",
    "CLOUDY": "☁️",
    "FOG": "🌫",
    "HEAVY_RAIN": "🌧",
    "HEAVY_SHOWERS": "🌧",
    "HEAVY_SNOW": "❄️",
    "HEAVY_SNOW_SHOWERS": "❄️",
    "LIGHT_RAIN": "🌦",
    "LIGHT_SHOWERS": "🌦",
    "LIGHT_SLEET": "🌧",
    "LIGHT_SLEET_SHOWERS": "🌧",
    "LIGHT_SNOW": "🌨",
    "LIGHT_SNOW_SHOWERS": "🌨",
    "PARTLY_CLOUDY": "⛅️",
    "SUNNY": "☀️",
    "THUNDERY_HEAVY_RAIN": "🌩",
    "THUNDERY_SHOWERS": "⛈",
    "THUNDERY_SNOW_SHOWERS": "⛈",
    "VERY_CLOUDY": "☁️",
}

# TODO: change colors based on directions
WIND_ARROWS = {
    "NORTH": "↑",
    "NORTH_NORTHEAST": "↑",
    "NORTHEAST": "↗",
    "EAST_NORTHEAST": "↗",
    "EAST": "→",
    "EAST_SOUTHEAST": "↘",
    "SOUTHEAST": "↘",
    "SOUTH_SOUTHEAST": "↘",
    "SOUTH": "↓",
    "SOUTH_SOUTHWEST": "↙",
    "SOUTHWEST": "↙",
    "WEST_SOUTHWEST": "↙",
    "WEST": "←",
    "WEST_NORTHWEST": "↖",
    "NORTHWEST": "↖",
    "NORTH_NORTHWEST": "↖",
}

OW_WEATHER_SYMBOL = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Rain": "🌧",
    "Drizzle": "🌦",
    "Thunderstorm": "⛈",
    "Snow": "❄️",
    "Mist": "🌫",
    "Fog": "🌫",
    "Haze": "🌫",
    "Dust": "🌫",
    "Sand": "🌫",
    "Ash": "🌫",
    "Squall": "🌬",
    "Tornado": "🌪",
}


def get_wind_arrow(deg: float) -> str:
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


async def get_weather(city: str) -> list:
    async with python_weather.Client(unit=python_weather.METRIC) as client:
        weather = await client.get(city)

        today = weather.daily_forecasts[0]
        weather_symbol = WEATHER_SYMBOL.get(weather.kind.name, "❓")
        wind_arrow = WIND_ARROWS.get(weather.wind_direction.name, "?")
        weather_info = f"{today.lowest_temperature}°C - {today.highest_temperature}°C "
        weather_info += (
            f"Humidity: {weather.humidity}% Precipitation: {weather.precipitation}mm "
        )
        weather_info += f"Wind: {weather.wind_speed}km/h {wind_arrow}"

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
                    "rich_text": [{"type": "text", "text": {"content": weather_info}}]
                },
            },
        ]
