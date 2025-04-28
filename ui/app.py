import sys
from PyQt6 import QtWidgets
from qasync import QEventLoop, asyncSlot
from ui.odds_graph import OddsGraph
from data.odds_store import shared_odds
from utils.logger import setup_logger
import asyncio

logger = setup_logger("UI")

async def initialize_races(graph, matched_races_coro):
    # Load matched races (already sorted by time in load_matched_races)
    matched_races = await matched_races_coro(tommorow=False)
    # Take the first 5 upcoming races
    matched_races = matched_races[:5]
    logger.info(f"Initializing UI with {len(matched_races)} races")
    # Update GUI with matched races
    graph.update_matched_races(matched_races)

def launch_ui(coordinator, matched_races):
    app = QtWidgets.QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    graph = OddsGraph()
    graph.show()

    # Initialize races
    loop.create_task(initialize_races(graph, matched_races))
    
    # Start the coordinator
    loop.create_task(coordinator())

    with loop:
        loop.run_forever()