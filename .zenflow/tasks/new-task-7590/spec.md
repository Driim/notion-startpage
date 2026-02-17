# Technical Specification: Replace Weather Data Source

## Task Complexity: Medium

**Rationale**: This task requires replacing the weather data provider while maintaining backward compatibility with the existing interface, updating all related tests, and ensuring data mapping is correct. The complexity is moderate because:
- The existing interface is well-defined and should remain unchanged
- Multiple data fields need proper mapping from a new API
- Comprehensive test suite needs updating
- API integration requires error handling and data transformation

---

## Technical Context

### Language & Dependencies
- **Language**: Python 3.10+
- **Current weather library**: `python-weather` (>=2.1.1, <3.0.0) - uses wttr.in backend which is no longer available
- **Replacement**: Open-Meteo API (completely free, no API key required)
- **HTTP client**: `aiohttp` (already in dependencies - version >=3.9.0, <4.0.0)
- **Testing framework**: pytest with pytest-asyncio and pytest-mock
- **Linting**: flake8 with multiple plugins
- **Formatting**: black + isort

---

## Current Implementation Analysis

### File: [./src/startpage/components/weather.py](./src/startpage/components/weather.py)

**Current Data Points Fetched**:
1. Weather condition/kind (e.g., SUNNY, CLOUDY, RAIN)
2. Daily temperature range (lowest and highest)
3. Humidity (percentage)
4. Precipitation (mm)
5. Wind speed (km/h)
6. Wind direction (degrees or cardinal direction)

**Output Format**:
- Returns list of two Notion blocks:
  1. `heading_2` block with weather emoji + city name
  2. `paragraph` block with formatted weather details

**Current Interface**:
```python
async def get_weather(city: str) -> list:
    """Fetch weather data for a city and format as Notion blocks."""
```

This interface **must remain unchanged** to avoid breaking the main orchestrator in [./src/startpage/startpage.py:102](./src/startpage/startpage.py:102).

---

## Implementation Approach

### 1. Open-Meteo API Integration

**API Choice**: Open-Meteo Weather Forecast API
- **Endpoint**: `https://api.open-meteo.com/v1/forecast`
- **Documentation**: https://open-meteo.com/en/docs
- **Cost**: Completely free, no API key required
- **Rate Limits**: No strict limits for reasonable use
- **Features**: Open-source, high-resolution forecasts

**API Request Parameters**:
```
GET https://api.open-meteo.com/v1/forecast
?latitude={lat}
&longitude={lon}
&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m
&daily=temperature_2m_max,temperature_2m_min
&timezone=auto
```

**Note**: Open-Meteo requires latitude/longitude coordinates, not city names. We'll use their Geocoding API to convert city names to coordinates:
- **Geocoding Endpoint**: `https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1`

**API Response Mapping**:
```python
# Open-Meteo Response → Current Implementation
{
  "current": {
    "temperature_2m": 20.5,           # → current temperature
    "relative_humidity_2m": 65,       # → humidity
    "precipitation": 0.5,             # → precipitation (mm)
    "weather_code": 3,                # → weather kind (WMO code)
    "wind_speed_10m": 12.5,           # → wind speed (km/h)
    "wind_direction_10m": 180         # → wind direction (degrees)
  },
  "daily": {
    "temperature_2m_max": [25.0],     # → highest temperature
    "temperature_2m_min": [15.0]      # → lowest temperature
  }
}
```

### 2. WMO Weather Code Mapping

Open-Meteo uses WMO (World Meteorological Organization) weather codes. We need to map these to emojis:

```python
WMO_WEATHER_SYMBOL = {
    0: "☀️",      # Clear sky
    1: "🌤",      # Mainly clear
    2: "⛅️",     # Partly cloudy
    3: "☁️",      # Overcast
    45: "🌫",     # Fog
    48: "🌫",     # Depositing rime fog
    51: "🌦",     # Drizzle: Light
    53: "🌦",     # Drizzle: Moderate
    55: "🌧",     # Drizzle: Dense
    56: "🌧",     # Freezing Drizzle: Light
    57: "🌧",     # Freezing Drizzle: Dense
    61: "🌦",     # Rain: Slight
    63: "🌧",     # Rain: Moderate
    65: "🌧",     # Rain: Heavy
    66: "🌧",     # Freezing Rain: Light
    67: "🌧",     # Freezing Rain: Heavy
    71: "🌨",     # Snow fall: Slight
    73: "❄️",     # Snow fall: Moderate
    75: "❄️",     # Snow fall: Heavy
    77: "❄️",     # Snow grains
    80: "🌦",     # Rain showers: Slight
    81: "🌧",     # Rain showers: Moderate
    82: "🌧",     # Rain showers: Violent
    85: "🌨",     # Snow showers: Slight
    86: "❄️",     # Snow showers: Heavy
    95: "⛈",      # Thunderstorm
    96: "⛈",      # Thunderstorm with hail: Slight
    99: "⛈",      # Thunderstorm with hail: Heavy
}
```

### 3. Code Changes Strategy

**Replace Library Import**:
- Remove: `import python_weather`
- Add: Use existing `aiohttp` for HTTP requests

**Preserve Existing Functions**:
- Keep `get_wind_arrow(deg: float) -> str` unchanged - works with degrees
- Remove `WEATHER_SYMBOL` dictionary - was for python_weather library
- Remove `OW_WEATHER_SYMBOL` dictionary - was for OpenWeatherMap
- Add new `WMO_WEATHER_SYMBOL` dictionary for Open-Meteo weather codes
- Remove `WIND_ARROWS` dictionary - not needed with `get_wind_arrow()`

**Add Geocoding Function**:
```python
async def get_coordinates(city: str) -> tuple[float, float]:
    """Convert city name to latitude/longitude coordinates."""
```

**Update `get_weather()` Function**:
1. Call geocoding API to convert city name to coordinates
2. Use `aiohttp.ClientSession` for async HTTP requests
3. Call Open-Meteo API with coordinates
4. Parse JSON response
5. Map weather code from WMO format to emoji using `WMO_WEATHER_SYMBOL`
6. Calculate wind direction arrow using existing `get_wind_arrow(deg)`
7. Format data into same Notion block structure
8. Add error handling for:
   - Network failures
   - City not found (geocoding)
   - Invalid API response
   - Missing data fields

### 4. Configuration Changes

**Environment Variables** (`.env`):
- No API key needed for Open-Meteo
- Can remove `OPENWEATHER_API_KEY` (no longer used)
- Keep existing `CITY` variable

**README Updates**:
- Update weather feature description to mention Open-Meteo
- Remove `OPENWEATHER_API_KEY` from environment variables section
- Add note about Open-Meteo being free and open-source

---

## Source Code Structure Changes

### Files to Modify

1. **[./src/startpage/components/weather.py](./src/startpage/components/weather.py)** (PRIMARY)
   - Replace `python_weather` import with `aiohttp`
   - Add new `WMO_WEATHER_SYMBOL` dictionary for Open-Meteo weather codes
   - Remove `WEATHER_SYMBOL`, `OW_WEATHER_SYMBOL`, and `WIND_ARROWS` dictionaries
   - Add new `get_coordinates()` helper function for geocoding
   - Reimplement `get_weather()` function to use Open-Meteo API
   - Keep `get_wind_arrow()` function unchanged
   - Add error handling and logging

2. **[./tests/test_weather.py](./tests/test_weather.py)** (PRIMARY)
   - Update all 22 tests to mock `aiohttp.ClientSession` instead of `python_weather.Client`
   - Update mock response structures to match Open-Meteo API format
   - Update expected weather symbols to match `WMO_WEATHER_SYMBOL` mappings
   - Add tests for `get_coordinates()` function
   - Add tests for error scenarios:
     - Network timeout
     - City not found (geocoding returns empty)
     - Malformed JSON response
     - Missing data fields
   - Keep existing test for `get_wind_arrow()` unchanged

3. **[./pyproject.toml](./pyproject.toml:10)** (MINOR)
   - Remove dependency: `"python-weather (>=2.1.1,<3.0.0)"`
   - Keep `aiohttp` (already present)

4. **[./README.md](./README.md:22-31)** (DOCUMENTATION)
   - Remove `OPENWEATHER_API_KEY` from environment variables section (no longer needed)
   - Update weather feature description to mention Open-Meteo
   - Add note about Open-Meteo being free and requiring no API key

### Files NOT to Modify

- [./src/startpage/startpage.py](./src/startpage/startpage.py) - Interface remains compatible
- [./src/startpage/lambda_handler.py](./src/startpage/lambda_handler.py) - No changes needed
- Other component files - Independent modules

---

## Data Model / API / Interface Changes

### External API Integration

**New HTTP Client Pattern**:
```python
async with aiohttp.ClientSession() as session:
    async with session.get(url, params=params) as response:
        data = await response.json()
```

### Interface Preservation

**Public Interface** (unchanged):
```python
async def get_weather(city: str) -> list
```

**Return Value** (unchanged):
```python
[
    {
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": f"{emoji} {city}"}}]
        }
    },
    {
        "type": "paragraph", 
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": weather_info}}]
        }
    }
]
```

### Weather Symbol Mapping Updates

Update to use `WMO_WEATHER_SYMBOL` which maps WMO weather codes (integers):
- 0: Clear sky → ☀️
- 1-3: Mainly clear to overcast → 🌤/⛅️/☁️
- 45-48: Fog → 🌫
- 51-57: Drizzle → 🌦/🌧
- 61-67: Rain → 🌦/🌧
- 71-77: Snow → 🌨/❄️
- 80-86: Showers → 🌦/🌧/🌨/❄️
- 95-99: Thunderstorm → ⛈

---

## Verification Approach

### 1. Unit Tests
```bash
poetry run pytest tests/test_weather.py -v
```

**Expected**: All 22+ tests pass (including new error handling tests)

### 2. Full Test Suite
```bash
poetry run pytest
```

**Expected**: All 82+ tests pass

### 3. Code Quality Checks

**Linting**:
```bash
poetry run flake8 src tests
```

**Formatting**:
```bash
poetry run black src tests --check
poetry run isort src tests --check --profile black
```

### 4. Integration Test (Manual)

Run the application locally to verify real API integration:
```bash
poetry run python -m startpage.startpage
```

**Verification checklist**:
- [ ] Weather data fetches successfully
- [ ] Correct emoji appears for current weather
- [ ] Temperature range displays properly
- [ ] Humidity percentage is accurate
- [ ] Wind speed and direction arrow are correct
- [ ] Notion page updates successfully

### 5. Error Handling Verification

Test error scenarios:
- Invalid city name (should fail at geocoding step)
- Network timeout (disconnect internet briefly)
- Malformed API response

---

## Risk Assessment

### Low Risk
- Using existing `aiohttp` dependency (already in project)
- Open-Meteo API is stable, well-documented, and open-source
- No API key required - one less dependency to manage
- No rate limits for reasonable use

### Medium Risk
- Data mapping differences between python_weather and Open-Meteo
  - **Mitigation**: Thorough testing with multiple cities/conditions
- Requires geocoding step (city name → coordinates)
  - **Mitigation**: Cache coordinates or handle geocoding errors gracefully

### Potential Issues
1. **Geocoding accuracy**: City names may be ambiguous or misspelled
   - **Solution**: Use first result from geocoding API, log warnings
2. **Precipitation data**: Open-Meteo returns current precipitation, not daily total
   - **Solution**: Use current precipitation value (acceptable for current weather display)
3. **Weather code mapping**: WMO codes are numeric, different from previous string-based conditions
   - **Solution**: Create comprehensive `WMO_WEATHER_SYMBOL` mapping dictionary

---

## Implementation Tasks Breakdown

Given the moderate complexity, the implementation should be broken down into the following tasks:

### Task 1: Update weather.py to use Open-Meteo API
- Remove `python_weather` import
- Add `WMO_WEATHER_SYMBOL` dictionary
- Implement geocoding function using Open-Meteo Geocoding API
- Implement weather API client using `aiohttp` and Open-Meteo Weather API
- Map API response to existing Notion block format
- Add error handling and logging
- Update weather symbol mapping
- Write/update unit tests for the new implementation (including geocoding tests)
- Run tests: `poetry run pytest tests/test_weather.py -v`

### Task 2: Update dependencies and documentation
- Remove `python-weather` from `pyproject.toml`
- Update README.md to remove `OPENWEATHER_API_KEY` and mention Open-Meteo
- Run full test suite: `poetry run pytest`
- Run linting: `make lint`
- Run formatting check: `poetry run black src tests --check`

### Task 3: Integration testing and verification
- Test with real API calls locally
- Verify Notion page updates correctly
- Test error scenarios (invalid city, network failures)
- Verify Lambda deployment (if needed)

---

## Success Criteria

1. ✅ All existing tests pass with updated mocks
2. ✅ New error handling tests added and passing
3. ✅ Linting passes with no warnings
4. ✅ Code formatting complies with black + isort
5. ✅ Weather data displays correctly in Notion
6. ✅ Same user experience (emoji, formatting, data points)
7. ✅ No breaking changes to public interface
8. ✅ Documentation updated
