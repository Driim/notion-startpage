import aiohttp


async def get_currency_rates(
    text: str, base: str, targets: list[str], date: str | None = None
):
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
