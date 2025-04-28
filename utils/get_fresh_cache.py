import asyncio
import json
import os
import sys
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.betfair.scraper import BetfairScraper
from scrapers.sportsbet.scraper import SportsbetScraper
from scrapers.betfair.browser import BrowserManager
from utils.logger import setup_logger

logger = setup_logger("RaceMatcher")

# Cache file path
MATCHED_RACES_FILE = "matched_races.json"

def standardize(name):
    """Normalize race name for consistent keying."""
    return name.lower().replace(" ", "").replace("-", "").replace("'", "").replace("'", "")

def make_race_key(race):
    """Create a unique key for a race based on its metadata."""
    location = standardize(race["race_name"])
    race_number = race["race_number"]
    race_type = race.get("race_type", "horse")
    return f"{race_type}_{location}_{race_number}"

def get_race_datetime(race):
    try:
        time_str = race["betfair"]["race_time"]
        race_time = datetime.strptime(time_str, "%H:%M").time()
        today = datetime.now().date()
        return datetime.combine(today, race_time)
    except Exception as e:
        logger.info(f"Error getting race datetime: {e}")
        return datetime.max

def sort_races_by_time(matches):
    """Sort races by their start time."""
    return sorted(matches, key=get_race_datetime)

async def get_all_scrapers(context):
    return {
        "betfair": BetfairScraper(context),
        "sportsbet": SportsbetScraper(context),
    }

async def fetch_all_metadata(scrapers):
    data = {}
    for name, scraper in scrapers.items():
        urls = await scraper.get_race_urls(tommorow=False)
        races = await scraper.get_race_metadata_batch(urls)
        data[name] = races
    return data

async def match_races():
    async with BrowserManager() as context:
        scrapers = await get_all_scrapers(context)
        race_data = await fetch_all_metadata(scrapers)

        # Build dicts keyed by race_name and race_number
        race_maps = {
            name: {make_race_key(race): race for race in races}
            for name, races in race_data.items()
        }

        # Get intersection of all race keys
        all_keys = list(race_maps.values())
        common_keys = set(all_keys[0]).intersection(*all_keys[1:])

        logger.info(f"Found {len(common_keys)} matched races across all sources")

        matched_races = []
        for key in common_keys:
            matched = {scraper: race_maps[scraper][key] for scraper in race_maps}
            matched_races.append(matched)

        return matched_races

async def update_cache():
    """Update the race cache with fresh data."""
    logger.info("Updating race cache with fresh data")
    matched_races = await match_races()
    
    # Sort races by time
    sorted_races = sort_races_by_time(matched_races)
    
    # Write to cache file
    with open(MATCHED_RACES_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_races, f, indent=2)
    
    logger.info(f"Cache updated successfully with {len(sorted_races)} races")
    return sorted_races

async def main():
    """Run once to update the cache."""
    try:
        await update_cache()
        logger.info("Race cache updated successfully. You can now run the main application.")
    except Exception as e:
        logger.error(f"Error updating cache: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 