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

    async def fetch_metadata(self):
        try:
            page = await self.context.new_page()
            await page.goto(self.url, timeout=30000)
            await page.wait_for_selector(".runner-name", timeout=10000)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            title = soup.title.string if soup.title else "Unknown Title"
            au_match = re.match(r"(\d{2}:\d{2})\s+([\w\s]+?)\s+R(\d+)\s+(\d+)m", title)
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

            self.metadata = {
                "race_id": race_id,
                "location": location,
                "race_name": location,
                "race_number": race_number,
                "race_time": race_time,
                "url": self.url
            }

            await page.close()
            return self.metadata

        except Exception as e:
            self.logger.error(f"Error extracting race info: {e}")
            self.metadata = {
                "race_id": "Unknown",
                "location": "Unknown",
                "race_name": "Unknown",
                "race_number": -1,
                "race_time": "Unknown",
                "url": self.url
            }
            return self.metadata

    async def stream_odds(self, interval=5):
        page = await self.context.new_page()
        await page.goto(self.url, timeout=60000)

        while True:
            try:
                # Wait for runners to load
                await page.wait_for_selector("h3.runner-name", timeout=10000)

                # Get page HTML and parse it
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")

                runners = soup.find_all("h3", class_="runner-name")
                odds = soup.find_all("label", class_="Zs3u5 AUP11 Qe-26")  # back odds
                dom = soup.find_all("label", class_="He6+y Qe-26")         # lay odds

                horse_data = {}
                i = 0
                for idx, runner in enumerate(runners, start=1):
                    name = runner.text.strip()
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

                refresh_button = page.locator("button.refresh-btn.marketview-resize")
                await refresh_button.click(force=True)

                await asyncio.sleep(interval)

            except Exception as e:
                print(f"[stream_odds] Error: {e}")
                await asyncio.sleep(interval) 
