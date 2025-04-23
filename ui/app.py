import sys
from PyQt6 import QtWidgets
from qasync import QEventLoop, asyncSlot
from ui.odds_graph import OddsGraph
from data.odds_store import shared_odds
from utils.logger import setup_logger

logger = setup_logger("UI")

async def initialize_races(graph, matched_races_coro):
    # Load matched races
    matched_races = await matched_races_coro(tommorow=True)
    # Limit to first 5 races
    matched_races = matched_races[:5]
    logger.info(f"Initializing UI with {len(matched_races)} races")
    # Update GUI with matched races
    graph.update_matched_races(matched_races)

def launch_ui(coro, matched_races):
    app = QtWidgets.QApplication(sys.argv)
    loop = QEventLoop(app)
    import asyncio
    asyncio.set_event_loop(loop)

    graph = OddsGraph()
    graph.show()
    graph.run_updater(shared_odds)

    with loop:
        # First initialize races, then start the coordinator
        loop.run_until_complete(initialize_races(graph, matched_races))
        loop.run_until_complete(coro())