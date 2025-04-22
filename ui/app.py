import sys
from PyQt6 import QtWidgets
from qasync import QEventLoop, asyncSlot
from ui.odds_graph import OddsGraph
from data.odds_store import shared_odds

def launch_ui(coro):
    app = QtWidgets.QApplication(sys.argv)
    loop = QEventLoop(app)
    import asyncio
    asyncio.set_event_loop(loop)

    graph = OddsGraph()
    graph.show()
    graph.run_updater(shared_odds)

    with loop:
        loop.run_until_complete(coro())
