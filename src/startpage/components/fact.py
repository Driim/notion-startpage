import aiohttp


async def get_random_fact():
    url = "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en"
    headers = {"Accept": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch fact: {response.status}")
            data = await response.json()
            fact = data.get("text", "")

    return fact.strip()
