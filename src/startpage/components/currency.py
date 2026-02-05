"""Currency and cryptocurrency rate fetching component.

This module fetches exchange rates from a currency API and formats them as
Notion blocks for display.
"""

import aiohttp


async def get_currency_rates(
    text: str, base: str, targets: list[str], date: str | None = None
):
    """Fetch currency exchange rates and format as Notion blocks.

    Args:
        text: Section header text for Notion display.
        base: Base currency code (e.g., "rub", "usd").
        targets: List of target currency codes to fetch rates for.
        date: Optional date string for historical rates (YYYY-MM-DD format).

    Returns:
        List of Notion block dictionaries containing header and rate items.

    Raises:
        Exception: If API request fails.
    """
    base = base.lower()
    if date:
        url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies/{base}.json"
    else:
        url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{base}.json"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch currency data: {response.status}")
            data = await response.json()

    rates = data[base]
    # Build Notion blocks: heading_2 and bulleted list items
    blocks = [
        {
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]},
        }
    ]
    for target in targets:
        target = target.lower()
        if target in rates:
            rate = f"{1 / rates[target]:,.2f}"
            text = f"1 {target.upper()} = {rate} {base.upper()}"
        else:
            text = f"Rate for {target.upper()} not available"
        blocks.append(
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                },
            }
        )
    return blocks
