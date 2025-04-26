import re
from bs4 import BeautifulSoup
from utils.logger import setup_logger
import asyncio

class SportsbetRace:
    def __init__(self, url: str, context):
        self.url = url
        self.context = context
        self.metadata = {}
        self.latest_odds = {}
        self.logger = setup_logger("SportsbetRace")
        self.page = None

    def extract_race_id(self, url):
        match = re.search(r"race-(\d+)-", url)
        return match.group(1) if match else "Unknown"

    async def initialize(self):
        """Initialize the persistent page."""
        if not self.page:
            self.page = await self.context.new_page()
            await self.page.goto(self.url, timeout=60000)
            await self.page.wait_for_selector(".outcomeCard_f7jc198", timeout=10000)

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

            race_title = soup.find("h1", class_=lambda x: x and "title" in x.lower())
            race_name = race_title.text.strip() if race_title else "Unknown Race"

            time_element = soup.select_one(
                "span.size14_f7opyze.defaultTimer_f17adqu9, span.size16_f6irgbz"
            )
            race_time = time_element.text.strip() if time_element else "Unknown Time" # this dosen't work - not tested at all

            # Update location extraction to handle both types
            location_match = re.search(r"/(horse|greyhound)-racing/([^/]+)", self.url)
            location = location_match.group(2).replace("-", " ").title() if location_match else "Unknown Location"

            race_number_match = re.search(r"Race (\d+)", race_name)
            if not race_number_match:
                race_number_match = re.search(r"race-(\d+)-", self.url)
            race_number = race_number_match.group(1) if race_number_match else "Unknown"

            race_type = "greyhound" if "greyhound-racing" in self.url else "horse"

            self.metadata = {
                "race_id": self.extract_race_id(self.url),
                "location": location,
                "race_name": race_name,
                "race_number": race_number,
                "race_time": race_time,
                "race_type": race_type,
                "url": self.url
            }

            return self.metadata

        except Exception as e:
            self.logger.error(f"Error extracting race info: {e}")
            return {
                "race_id": self.extract_race_id(self.url),
                "location": "Unknown Location",
                "race_name": "Unknown Race",
                "race_number": 0, #reserved unknown number for sportsbet
                "race_time": "Unknown Time",
                "race_type": "Unknown",
                "url": self.url
            }

    async def stream_odds(self, interval=5):
        try:
            await self.initialize()
            
            while True:
                try:
                    # Reload the page content
                    await self.page.reload()
                    await self.page.wait_for_selector(".outcomeCard_f7jc198", timeout=10000)

                    # Extract page source for parsing
                    content = await self.page.content()
                    soup = BeautifulSoup(content, "html.parser")

                    horse_data = {}

                    # Loop through each outcome card and extract odds
                    for outcome in soup.find_all("div", class_="outcomeCard_f7jc198"):
                        try:
                            name_tag = outcome.find("div", class_="outcomeName_f18x6kvm")
                            if not name_tag:
                                continue
                            
                            name_parts = name_tag.text.strip().split(". ")
                            number = name_parts[0] if len(name_parts) > 1 else ""
                            name = name_parts[1] if len(name_parts) > 1 else name_parts[0]
                            
                            # Extract odds information
                            odds_tags = outcome.find_all("span", class_="priceFlucsTextDesktop_fiml4cj")
                            open_odds = odds_tags[0].text.strip() if len(odds_tags) > 0 else "N/A"
                            fluc1_odds = odds_tags[1].text.strip() if len(odds_tags) > 1 else "N/A"
                            fluc2_odds = odds_tags[2].text.strip() if len(odds_tags) > 2 else "N/A"
                            price_buttons = outcome.find_all("div", class_="priceText_f71sibe")
                            win_fixed = price_buttons[0].text.strip() if len(price_buttons) > 0 else "N/A"

                            # Clean the name - remove apostrophes, special characters and extra spaces
                            horse_name = name.strip().replace('\xa0', '')
                            horse_name = re.sub(r'\s*\(\d+\)', '', horse_name)
                            horse_name = horse_name.replace("'", "").replace("'", "").replace(".", "").strip()

                            # Store odds in horse_data
                            horse_data[horse_name] = {
                                "number": number.strip(),
                                "3rd_back": None,
                                "2nd_back": None,
                                "1st_back": float(win_fixed) if win_fixed != "N/A" else None,
                                "1st_lay": None,
                                "2nd_lay": None,
                                "3rd_lay": None,
                                "3rd_back_dom": None,
                                "2nd_back_dom": None,
                                "1st_back_dom": None,
                                "1st_lay_dom": None,
                                "2nd_lay_dom": None, 
                                "3rd_lay_dom": None,
                                "fluctuations": {
                                    "open": open_odds,
                                    "open_decimal": float(open_odds) if open_odds != "N/A" else None,
                                    "fluctuation1": fluc1_odds,
                                    "fluctuation2": fluc2_odds,
                                }
                            }

                        except Exception as e:
                            self.logger.error(f"Error processing outcome: {e}")
                            continue

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