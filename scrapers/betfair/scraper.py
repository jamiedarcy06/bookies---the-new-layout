import asyncio
import logging
from .race import BetfairRace
from utils.logger import setup_logger
from bs4 import BeautifulSoup

class BetfairScraper:
    def __init__(self, context):
        self.context = context
        self.base_url = "https://www.betfair.com.au/exchange/plus/horse-racing"
        self.logger = setup_logger("BetfairScraper")

    async def get_race_urls(self, tommorow=False):
        self.logger.info("Fetching available Betfair race URLs")

        page = await self.context.new_page()
        await page.goto(self.base_url, timeout=60000)

        if tommorow:
            tomorrow_button = page.locator("button.schedule-filter-button", has_text="Tomorrow")
            await tomorrow_button.wait_for(state="visible", timeout=10000)
            await tomorrow_button.click(force=True)
            self.logger.info("Betfair: we are getting race data for tomorrow.")
            await page.wait_for_timeout(3000)

        await page.wait_for_selector(".race-link", timeout=20000)

        race_links_elements = await page.query_selector_all(".race-link")
        race_links = [
            "https://www.betfair.com.au/exchange/plus/" + await el.get_attribute("href")
            for el in race_links_elements
        ]

        buttons = page.locator(".country-tab")

        count = await buttons.count()

        popup_close_btn = await page.query_selector(
            ".tw-rounded-full.tw-cursor-pointer.tw-bg-black.tw-top-6.tw-right-6"
        )

        if popup_close_btn:
            await popup_close_btn.click()
            await page.wait_for_timeout(500) 
        else:
            self.logger.info("Warning: No popup detected on betfair - we may not get non Australian race urls.")

        '''
        for i in range(count):
            await buttons.nth(i).click(force=True)
            await page.wait_for_timeout(1000)
            await page.wait_for_selector(".race-link", timeout=20000)
            race_links_elements = await page.query_selector_all(".race-link")
            race_links += [
            "https://www.betfair.com.au/exchange/plus/" + await el.get_attribute("href")
            for el in race_links_elements] 
        ''' # this will require some new matching logic - not only for the regex, but also match_races, as we can not get the race number for certain uk races.
        await page.close()
        self.logger.info(f"Found {len(race_links)} races.")
        return race_links

    async def get_race_objects(self, urls):
        return [BetfairRace(url, self.context) for url in urls]

    async def get_race_metadata_batch(self, urls, batch_size=10):
        self.logger.info("Starting batch processing of race metadata")
        races = await self.get_race_objects(urls)
        results = []
        for i in range(0, len(races), batch_size):
            batch = races[i:i + batch_size]
            self.logger.info(f"Processing races {i+1} to {i+len(batch)}")
            infos = await asyncio.gather(*(race.fetch_metadata() for race in batch))
            results.extend(infos)
        return results
