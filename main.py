import asyncio
from scrapers.betfair.scraper import BetfairScraper
from scrapers.sportsbet.scraper import SportsbetScraper
from scrapers.betfair.race import BetfairRace
from scrapers.sportsbet.race import SportsbetRace
from scrapers.betfair.browser import BrowserManager
from utils.logger import setup_logger
from match_races import load_or_create_matched_races
from datetime import datetime

logger = setup_logger("Main")

# Hardcode a Betfair race URL here

async def main():
    async with BrowserManager() as context:
        matched_races = await load_or_create_matched_races()
        logger.info(f"Found {len(matched_races)} upcoming matched races.")


        sportsbetrace = SportsbetRace(matched_races[0]["sportsbet"]['url'], context)
        betfairrace = BetfairRace(matched_races[0]["betfair"]['url'], context)

        async def display_odds():
            while True:
                if sportsbetrace.latest_odds and betfairrace.latest_odds:
                    print("\033c", end="")  # Clear terminal
                    print(f"📡 Live Odds\n")
                    print(f"{'Horse':<20} | {'Sportsbet Back':<20} | {'Sportsbet Lay':<20} || {'Betfair Back':<20} | {'Betfair Lay':<20}")
                    print("-" * 110)

                    all_horses = sorted(set(sportsbetrace.latest_odds.keys()) | set(betfairrace.latest_odds.keys()))

                    for horse in all_horses:
                        sb_data = sportsbetrace.latest_odds.get(horse, {})
                        bf_data = betfairrace.latest_odds.get(horse, {})

                        sb_back = f"{sb_data.get('3rd_back', '')} {sb_data.get('2nd_back', '')} {sb_data.get('1st_back', '')}".strip()
                        sb_lay  = f"{sb_data.get('1st_lay', '')} {sb_data.get('2nd_lay', '')} {sb_data.get('3rd_lay', '')}".strip()

                        bf_back = f"{bf_data.get('3rd_back', '')} {bf_data.get('2nd_back', '')} {bf_data.get('1st_back', '')}".strip()
                        bf_lay  = f"{bf_data.get('1st_lay', '')} {bf_data.get('2nd_lay', '')} {bf_data.get('3rd_lay', '')}".strip()

                        print(f"{horse:<20} | {sb_back:<20} | {sb_lay:<20} || {bf_back:<20} | {bf_lay:<20}")
                    print()

                await asyncio.sleep(2)


        await asyncio.gather(
            sportsbetrace.stream_odds(interval=5),
            betfairrace.stream_odds(interval=5),
            display_odds()
        )


if __name__ == "__main__":
    asyncio.run(main())
