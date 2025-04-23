from utils.logger import setup_logger
from .race import SportsbetRace
from bs4 import BeautifulSoup
import asyncio

class SportsbetScraper:
    def __init__(self, context):
        self.context = context
        self.base_url = "https://www.sportsbet.com.au/racing-schedule"
        self.logger = setup_logger("SportsbetScraper")

    async def get_race_urls(self, tommorow=False):
        url = f"{self.base_url}/tomorrow" if tommorow else self.base_url
        self.logger.info(f"Navigating to {url}")
        
        page = await self.context.new_page()
        await page.goto(url, timeout=60000)

        await page.wait_for_selector("a.link_fqiekv4", timeout=10000)
        anchors = await page.query_selector_all("a")

        race_links = []
        for a in anchors:
            href = await a.get_attribute("href")
            if href and "/horse-racing/" in href and "race-" in href:
                race_links.append(f"https://www.sportsbet.com.au{href}")

        await page.close()
        self.logger.info(f"Found {len(race_links)} races.")
        return race_links

    async def get_race_objects(self, urls):
        return [SportsbetRace(url, self.context) for url in urls]

    async def get_race_metadata_batch(self, urls, batch_size=10):
        self.logger.info("Starting batch processing of Sportsbet race metadata")
        races = await self.get_race_objects(urls)
        results = []
        for i in range(0, len(races), batch_size):
            batch = races[i:i + batch_size]
            self.logger.info(f"Processing races {i+1} to {i+len(batch)}")
            infos = await asyncio.gather(*(race.fetch_metadata() for race in batch))
            results.extend(infos)
        return results