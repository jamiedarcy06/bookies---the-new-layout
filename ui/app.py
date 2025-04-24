import sys
from PyQt6 import QtWidgets
from qasync import QEventLoop, asyncSlot
from ui.odds_graph import OddsGraph
from data.odds_store import shared_odds
from utils.logger import setup_logger
import asyncio

logger = setup_logger("UI")

async def initialize_races(graph, matched_races_coro):
    # Load matched races (already sorted by time in load_or_create_matched_races)
    matched_races = await matched_races_coro(tommorow=False)
    # Take the first 5 upcoming races
    matched_races = matched_races[:5]
    logger.info(f"Initializing UI with {len(matched_races)} races")
    # Update GUI with matched races
    graph.update_matched_races(matched_races)

def launch_ui(coro, matched_races):
    app = QtWidgets.QApplication(sys.argv)
    
    # Create event loop with error handling
    try:
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)
    except Exception as e:
        logger.error(f"Error setting up event loop: {e}")
        # Fall back to default event loop if QEventLoop fails
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info("Falling back to default event loop")

    graph = OddsGraph()
    graph.show()
    graph.run_updater(shared_odds)

    def exception_handler(loop, context):
        # Log the error
        error = context.get('exception', context['message'])
        logger.error(f"Caught event loop error: {error}")
        
        # Don't quit the app, just log the error
        if isinstance(error, TypeError) and "QMutexLocker" in str(error):
            logger.info("Caught QMutexLocker error, continuing execution")
            return
        
        # For other errors, log them but don't crash
        logger.error(f"Async error in event loop: {context}")

    # Set up error handling
    loop.set_exception_handler(exception_handler)

    try:
        with loop:
            # First initialize races, then start the coordinator
            loop.run_until_complete(initialize_races(graph, matched_races))
            loop.run_until_complete(coro())
    except Exception as e:
        logger.error(f"Error in main event loop: {e}")
        # Keep the UI running even if there's an error
        app.exec()