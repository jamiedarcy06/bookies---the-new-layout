import asyncio
from scrapers.betfair.scraper import BetfairScraper
from scrapers.sportsbet.scraper import SportsbetScraper
from scrapers.betfair.browser import BrowserManager
from utils.logger import setup_logger
from datetime import datetime
import json
import os

logger = setup_logger("MatchRaces")

def standardize(name):
    """Normalize race name for consistent keying.
    Removes spaces, hyphens, apostrophes and converts to lowercase for consistent matching."""
    return name.lower().replace(" ", "").replace("-", "").replace("'", "").replace("'", "")

def make_race_key(race):
    """Create a unique key for a race based on its metadata."""
    location = standardize(race["race_name"]) # race['location] only returns the region the race is from!
    race_number = race["race_number"]
    race_type = race.get("race_type")  # Default to "horse" for backward compatibility
    return f"{race_type}_{location}_{race_number}"
 
def is_future_race(race):
    try:
        time_str = race["betfair"]["race_time"]  # or any other scraper
        race_time = datetime.strptime(time_str, "%H:%M").time()
        now = datetime.now().time()
        return race_time > now
    except Exception as e:
        logger.info(f"Error in determining if a race is in the future: {e}")

async def get_all_scrapers(context):
    return {
        "betfair": BetfairScraper(context),
        "sportsbet": SportsbetScraper(context),
        # Add more scrapers here later like: "ladbrokes": LadbrokesScraper(context)
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
        
        # Write all_keys to debug file
        with open('all_keys.json', 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'race_maps': race_maps,
                'all_keys_values': all_keys
            }, f, indent=2)
            
        logger.info(all_keys)
        common_keys = set(all_keys[0]).intersection(*all_keys[1:])

        logger.info(f"Found {len(common_keys)} matched races across all sources")

        matched_races = []
        for key in common_keys:
            matched = {scraper: race_maps[scraper][key] for scraper in race_maps}
            matched_races.append(matched)

        return matched_races

MATCHED_RACES_FILE = "matched_races.json"

def is_file_modified_today(path):
    if not os.path.exists(path):
        return False
    modified_time = datetime.fromtimestamp(os.path.getmtime(path))
    return modified_time.date() == datetime.today().date()

def get_race_datetime(race):
    try:
        time_str = race["betfair"]["race_time"]
        race_time = datetime.strptime(time_str, "%H:%M").time()
        today = datetime.now().date()
        return datetime.combine(today, race_time)
    except Exception as e:
        logger.info(f"Error getting race datetime: {e}")
        return datetime.max  # Put races with invalid times at the end

def sort_races_by_time(matches):
    """Sort races by their start time."""
    return sorted(matches, key=get_race_datetime)

async def load_or_create_matched_races(tommorow=False): # this dosen't change the tommorow above lmao
    if is_file_modified_today(MATCHED_RACES_FILE):
        with open(MATCHED_RACES_FILE, "r", encoding="utf-8") as f:
            logger.info("Reading matched races from cache.")
            all_matches = json.load(f)
    else:
        logger.info("No cache or outdated cache. Running match.")
        all_matches = await match_races()
        with open(MATCHED_RACES_FILE, "w", encoding="utf-8") as f:
            json.dump(all_matches, f, indent=2)

    if tommorow == True:
        logger.info("Matched races are being served with tommorow=True")

    # Filter races that are still upcoming
    upcoming_matches = [match for match in all_matches if (is_future_race(match) or tommorow == True)]
    # Sort races by time
    sorted_matches = sort_races_by_time(upcoming_matches)
    return sorted_matches



# For testing
if __name__ == "__main__":
    logger.info("Testing match_races.py")
    matches = asyncio.run(load_or_create_matched_races())
    for match in matches:
        print(match)