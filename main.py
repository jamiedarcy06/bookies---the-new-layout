import asyncio
from scrapers.betfair.race import BetfairRace
from scrapers.sportsbet.race import SportsbetRace
from scrapers.betfair.browser import BrowserManager
from ui.app import launch_ui
from data.odds_store import shared_odds
from utils.match_races import load_or_create_matched_races
from utils.logger import setup_logger


logger = setup_logger("Main")

async def coordinator():
    async with BrowserManager() as context:
        matched = await load_or_create_matched_races(tommorow=True)
        sb = SportsbetRace(matched[0]['sportsbet']['url'], context)
        bf = BetfairRace(matched[0]['betfair']['url'], context)

        async def update_odds():
            while True:
                for horse in set(sb.latest_odds) | set(bf.latest_odds):
                    shared_odds[horse] = {
                        "sportsbet": sb.latest_odds.get(horse, {}),
                        "betfair": bf.latest_odds.get(horse, {})
                    }
                await asyncio.sleep(1)

        await asyncio.gather(
            sb.stream_odds(),
            bf.stream_odds(),
            update_odds()
        )

if __name__ == "__main__":
    launch_ui(coordinator)
