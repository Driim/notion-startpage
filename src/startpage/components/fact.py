"""Random fact fetching component.

This module fetches a random interesting fact from an external API.
"""

import aiohttp


async def get_random_fact():
    """Fetch a random interesting fact from uselessfacts API.

    Returns:
        String containing a random fact.

    Raises:
        Exception: If API request fails.
    """
    url = "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en"
    headers = {"Accept": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch fact: {response.status}")
            data = await response.json()
            fact = data.get("text", "")

    return fact.strip()
