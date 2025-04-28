import asyncio
from scrapers.betfair.race import BetfairRace
from scrapers.sportsbet.race import SportsbetRace
from scrapers.betfair.browser import BrowserManager
from ui.app import launch_ui
from data.odds_store import shared_odds
from utils.match_races import load_matched_races
from utils.logger import setup_logger
from collections import defaultdict

logger = setup_logger("Main")

# Dictionary to store odds for each race
race_odds = defaultdict(dict)

async def coordinator():
    async with BrowserManager() as context:
        matched_races = await load_matched_races(tommorow=False)
        # Limit to first 5 races
        matched_races = matched_races[:5]
        logger.info(f"Processing {len(matched_races)} races")
        
        # Create race objects for each matched race
        race_objects = []
        try:
            # Initialize all race objects concurrently
            init_tasks = []
            for race in matched_races:
                sb = SportsbetRace(race['sportsbet']['url'], context)
                bf = BetfairRace(race['betfair']['url'], context)
                race_objects.append((sb, bf))
                init_tasks.extend([
                    asyncio.create_task(sb.initialize()),
                    asyncio.create_task(bf.initialize())
                ])
            
            # Wait for all initializations to complete
            logger.info("Initializing all race pages concurrently")
            await asyncio.gather(*init_tasks)
            logger.info("All race pages initialized successfully")

            async def update_odds():
                while True:
                    # Update odds for each race
                    for idx, (sb, bf) in enumerate(race_objects):
                        race_key = f"{matched_races[idx]['betfair']['location']}_R{matched_races[idx]['betfair']['race_number']}"
                        
                        # Update odds for this race
                        race_odds[race_key] = {}
                        for horse in set(sb.latest_odds) | set(bf.latest_odds):
                            race_odds[race_key][horse] = {
                                "sportsbet": sb.latest_odds.get(horse, {}),
                                "betfair": bf.latest_odds.get(horse, {})
                            }
                    
                    # Update shared_odds with all race data
                    shared_odds.clear()
                    shared_odds.update({
                        'races': race_odds,
                        'current_race_index': 0  # This will be updated by the UI when user selects a race
                    })
                    
                    await asyncio.sleep(1)

            # Start streaming odds for all races
            stream_tasks = []
            for sb, bf in race_objects:
                stream_tasks.extend([
                    asyncio.create_task(sb.stream_odds()),
                    asyncio.create_task(bf.stream_odds())
                ])
            
            # Start the odds update task
            update_task = asyncio.create_task(update_odds())
            
            # Wait for all tasks to complete
            await asyncio.gather(*stream_tasks, update_task)
            
        except Exception as e:
            logger.error(f"Error in coordinator: {e}")
            # Cleanup race objects
            for sb, bf in race_objects:
                await sb.cleanup()
                await bf.cleanup()

if __name__ == "__main__":
    launch_ui(coordinator, matched_races=load_matched_races)
    