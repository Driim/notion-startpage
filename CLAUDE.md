# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

StartPage is a Python application that aggregates data from multiple sources (weather, calendar, currency, RSS feeds, random facts) and publishes them to a Notion page as a daily summary. It can run locally or as a scheduled AWS Lambda function.

## Development Commands

### Setup
```bash
poetry install
```

### Run Application
```bash
# Recommended method
poetry run python -m startpage.startpage

# Alternative: using convenience script
poetry run python run.py
```

### Testing
```bash
# Run all tests
poetry run pytest

# With coverage report
poetry run pytest --cov=src/startpage

# Run a single test file
poetry run pytest tests/test_weather.py

# Run a specific test
poetry run pytest tests/test_weather.py::test_function_name
```

### Code Quality
```bash
# Format code (runs isort + black)
make format

# Run linting
make lint

# Pre-commit hooks
poetry run pre-commit install
poetry run pre-commit run --all-files
```

### AWS Lambda Deployment
```bash
# Build Lambda package
make build-lambda

# Deploy to AWS (requires .env configuration)
make deploy
```

## Architecture

### Component Pattern
All data-fetching components follow a consistent pattern:
- Located in `src/startpage/components/`
- Async functions that fetch data from external sources
- Return lists of Notion block dictionaries
- Handle errors gracefully with structured logging
- Example: `async def get_weather(city: str) -> list`

### Main Orchestration Flow
1. `startpage.py` loads environment variables from `.env`
2. Creates async tasks for all components (weather, calendar, currency, RSS, fact)
3. Executes tasks concurrently using `asyncio.gather()`
4. Combines results into nested Notion blocks
5. Appends blocks to Notion page and updates fact block

### Notion Block Structure
- `utils/blocks.py` provides helpers for creating Notion blocks
- `create_header_1_block()`: Creates toggleable heading with children
- `append_block_to_page()`: Recursively appends blocks with hierarchies
- Components return block dictionaries with `type` and type-specific properties

### AWS Lambda Integration
- `lambda_handler.py` wraps the main function for AWS Lambda
- Environment variables configured in CloudFormation template
- Uses Python 3.12 runtime on ARM64 architecture
- Scheduled via EventBridge (default: daily at 6 AM UTC)

## Testing Strategy

The project has 82 tests across all components:
- Uses `pytest` with `pytest-mock` for mocking external API calls
- Uses `pytest-asyncio` for testing async functions
- Each component has comprehensive test coverage
- Tests mock external services (weather APIs, iCloud, Notion API, RSS feeds)
- Follow the existing test patterns when adding new components

## Code Quality Standards

- **Type Hints**: Use type hints throughout the codebase
- **Docstrings**: All modules and functions have comprehensive docstrings
- **Logging**: Use structured logging via `logging` module (not print statements)
- **Formatting**: Code formatted with black and isort (enforced by pre-commit)
- **Linting**: Multiple flake8 plugins (bandit, bugbear, cognitive-complexity, etc.)
- **Async/Await**: All I/O operations use async patterns

## Environment Variables

Required variables in `.env`:
- `NOTION_TOKEN`: Notion API integration token
- `PAGE_ID`: Target Notion page ID
- `BLOCK_ID`: Notion block ID for fact updates
- `CITY`: City name for weather information
- `ICLOUD_USERNAME`: iCloud email address
- `ICLOUD_APP_PASSWORD`: iCloud app-specific password
- `TIMEZONE`: Timezone for calendar events (optional, defaults to UTC)

## Common Patterns

### Adding a New Component
1. Create async function in `src/startpage/components/your_component.py`
2. Function should return list of Notion block dictionaries
3. Add comprehensive docstrings and type hints
4. Import and add to tasks list in `startpage.py`
5. Create corresponding test file `tests/test_your_component.py`
6. Mock external API calls in tests

### Notion Block Format
```python
{
    "type": "heading_2",
    "heading_2": {
        "rich_text": [{"type": "text", "text": {"content": "Your text"}}]
    }
}
```

### Error Handling
Use structured logging for errors:
```python
logger.error("Error message", exc_info=True)
```
