import re
import asyncio
from bs4 import BeautifulSoup
from utils.logger import setup_logger

class BetfairRace:
    def __init__(self, url: str, context):
        self.url = url
        self.context = context
        self.metadata = {}
        self.latest_odds = {}
        self.logger = setup_logger("BetfairRace")
        self.page = None

    async def initialize(self):
        """Initialize the persistent page."""
        if not self.page:
            self.page = await self.context.new_page()
            await self.page.goto(self.url, timeout=60000)
            await self.page.wait_for_selector(".runner-name", timeout=10000)

    async def cleanup(self):
        """Cleanup resources."""
        if self.page:
            try:
                await self.page.close()
                self.page = None
            except:
                pass

    async def fetch_metadata(self):
        try:
            await self.initialize()
            html = await self.page.content()
            soup = BeautifulSoup(html, "html.parser")

            title = soup.title.string if soup.title else "Unknown Title"
            au_match = re.match(r"(\d{2}:\d{2})\s+([\w\s]+?)\s+R(\d+)\s+(\d+m)", title)
            uk_match = re.match(r"(\d{2}:\d{2})\s+([\w\s]+?)\s+(\d+m\d*f?)", title)

            if au_match:
                race_time, location, race_number, distance = au_match.groups()
            elif uk_match:
                race_time, location, distance = uk_match.groups()
                race_number = -1
            else:
                self.logger.error(f"Unable to extract metadata for race {self.url}")
                race_time, location, race_number, distance = "Unknown", "Unknown", -1, "Unknown"

            race_id_match = re.search(r'market/1\.(\d+)', self.url)
            race_id = race_id_match.group(1) if race_id_match else "Unknown"

            # Determine race type from URL
            race_type = "greyhound" if "greyhound-racing" in self.url else "horse"

            self.metadata = {
                "race_id": race_id,
                "location": location,
                "race_name": location,
                "race_number": race_number,
                "race_time": race_time,
                "race_type": race_type,
                "url": self.url
            }

            return self.metadata

        except Exception as e:
            self.logger.error(f"Error extracting race info: {e}")
            self.metadata = {
                "race_id": "Unknown",
                "location": "Unknown",
                "race_name": "Unknown",
                "race_number": -1, # reserved unknown number for betfair
                "race_time": "Unknown",
                "race_type": "Unknown",
                "url": self.url
            }
            return self.metadata

    async def stream_odds(self, interval=5):
        try:
            await self.initialize()
            
            while True:
                try:
                    # Refresh the page content
                    refresh_button = self.page.locator("button.refresh-btn")
                    await refresh_button.click(force=True)
                    # Reduced wait time after refresh - we'll wait for content instead
                    await self.page.wait_for_selector(".runner-name", timeout=5000)

                    # Get page HTML and parse it
                    html = await self.page.content()
                    soup = BeautifulSoup(html, "html.parser")

                    runners = soup.find_all("h3", class_="runner-name")
                    odds = soup.find_all("label", class_="Zs3u5 AUP11 Qe-26")  # back odds
                    dom = soup.find_all("label", class_="He6+y Qe-26")         # lay odds

                    horse_data = {}
                    i = 0
                    for idx, runner in enumerate(runners, start=1):
                        name = runner.text.strip()
                        name = name.replace("'", "").replace("'", "").replace(".", "").strip()
                        try:
                            oddslist = [odds[i + j].text.strip() for j in range(6)]
                            domlist = [dom[i + j].text.strip() for j in range(6)]

                            horse_data[name] = {
                                "number": idx,
                                "3rd_back": oddslist[0],
                                "2nd_back": oddslist[1],
                                "1st_back": oddslist[2],
                                "1st_lay": oddslist[3],
                                "2nd_lay": oddslist[4],
                                "3rd_lay": oddslist[5],
                                "3rd_back_dom": domlist[0],
                                "2nd_back_dom": domlist[1],
                                "1st_back_dom": domlist[2],
                                "1st_lay_dom": domlist[3],
                                "2nd_lay_dom": domlist[4],
                                "3rd_lay_dom": domlist[5],
                            }
                        except:
                            horse_data[name] = {
                                "number": idx,
                                "3rd_back": None,
                                "2nd_back": None,
                                "1st_back": None,
                                "1st_lay": None,
                                "2nd_lay": None,
                                "3rd_lay": None,
                                "3rd_back_dom": None,
                                "2nd_back_dom": None,
                                "1st_back_dom": None,
                                "1st_lay_dom": None,
                                "2nd_lay_dom": None,
                                "3rd_lay_dom": None,
                            }
                        i += 6

                    self.latest_odds = horse_data

                except Exception as e:
                    self.logger.error(f"Error in stream_odds loop: {e}")
                    # Try to reinitialize the page if there was an error
                    await self.cleanup()
                    await self.initialize()

                await asyncio.sleep(interval)

        except Exception as e:
            self.logger.error(f"Fatal error in stream_odds: {e}")
            await self.cleanup()
            raise 