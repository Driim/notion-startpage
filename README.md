# StartPage

A Python application that aggregates data from multiple sources (weather, calendar, currency, RSS feeds, and random facts) and publishes them to a Notion page as a daily summary.

## Features

- 🌤️ **Weather** - Current weather information for any city
- 📅 **Calendar** - Today's events from iCloud calendar
- 💱 **Currency & Crypto** - Exchange rates for currencies and cryptocurrencies
- 📰 **RSS Feeds** - Aggregated tech news from multiple sources
- 🎲 **Random Facts** - Daily interesting fact

## Setup

1. Install dependencies:

   ```bash
   poetry install
   ```

1. Configure environment variables in `.env`:

```bash
NOTION_TOKEN=your_notion_token
PAGE_ID=your_page_id
BLOCK_ID=your_block_id
CITY=your_city
ICLOUD_USERNAME=your_icloud_email
ICLOUD_APP_PASSWORD=your_app_specific_password
TIMEZONE=Europe/London  # Optional, defaults to UTC
```

## Usage

### Run locally

#### Option 1: Using Poetry (recommended)

```bash
poetry run python -m startpage.startpage
```

#### Option 2: Using the convenience script

```bash
poetry run python run.py
```

### Deploy to AWS Lambda

StartPage can run as a scheduled AWS Lambda function. See [AWS Lambda Setup Guide](docs/AWS_LAMBDA_SETUP.md) for detailed instructions.

Quick start:

```bash
# Build the Lambda package
poetry self add poetry-plugin-lambda-build
poetry build-lambda

# Upload to S3 and deploy via CloudFormation
aws s3 cp package.zip s3://YOUR_BUCKET/startpage/package.zip
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name startpage \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    S3Bucket=YOUR_BUCKET \
    NotionToken=... PageId=... BlockId=... \
    City=London ICloudUsername=... ICloudAppPassword=... Timezone=UTC
```

The GitHub Actions workflow automatically deploys to Lambda when PRs are merged to `main`.

## Development

### Run tests

```bash
poetry run pytest
```

### Run tests with coverage

```bash
poetry run pytest --cov=src/startpage
```

### Linting and formatting

```bash
# Format code with black
poetry run black src/ tests/

# Run linting
poetry run flake8 src/ tests/
```

### Pre-commit hooks

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

## Project Structure

```text
startpage/
├── src/
│   └── startpage/
│       ├── components/      # Data fetching components
│       │   ├── calendar.py  # iCloud calendar integration
│       │   ├── currency.py  # Currency/crypto rates
│       │   ├── fact.py      # Random facts
│       │   ├── rss.py       # RSS feed aggregation
│       │   └── weather.py   # Weather information
│       ├── utils/
│       │   └── blocks.py    # Notion block utilities
│       └── startpage.py     # Main orchestration
├── tests/                   # Test suite (82 tests)
├── run.py                   # Convenience run script
└── pyproject.toml          # Project configuration
```

## Testing

The project has comprehensive test coverage (82 tests):

- ✅ RSS component (13 tests)
- ✅ Main orchestration (10 tests)
- ✅ Block utilities (15 tests)
- ✅ Weather (22 tests)
- ✅ Calendar (7 tests)
- ✅ Currency (4 tests)
- ✅ Fact (6 tests)

All tests pass with proper mocking and async support.

## Code Quality

- **Linting**: flake8 with multiple plugins (bandit, bugbear, cognitive-complexity)
- **Formatting**: black + isort
- **Type hints**: Used throughout the codebase
- **Documentation**: Comprehensive docstrings for all modules and functions
- **Logging**: Structured logging instead of print statements

## License

MIT
