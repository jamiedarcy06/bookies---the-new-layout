from PyQt6 import QtWidgets, QtCore
import pyqtgraph as pg
from pyqtgraph import PlotWidget, BarGraphItem
import numpy as np

class OddsGraph(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Odds Comparison")
        self.setGeometry(100, 100, 1000, 600)

        self.plot_widget = PlotWidget()
        self.setCentralWidget(self.plot_widget)

        self.plot_widget.setBackground("k")

        self.plot_item = self.plot_widget.getPlotItem()
        self.plot_item.layout.setContentsMargins(10, 10, 10, 50)
        self.plot_widget.setTitle("Live Odds: Sportsbet vs Betfair", color="w", size="16pt")
        self.plot_widget.showGrid(x=True, y=True)

        self.legend = self.plot_item.addLegend(labelTextColor="w")

        self.bottom_axis = self.plot_item.getAxis("bottom")
        self.bottom_axis.setStyle(autoExpandTextSpace=False)
        # self.bottom_axis.setHeight(50) # Keep this commented if needed later

    def update_odds(self, odds_store):
        horses = sorted(odds_store.keys())
        sportsbet_odds = []
        betfair_odds = []
        x = []

        for idx, horse in enumerate(horses):
            sb = float(odds_store[horse].get("sportsbet", {}).get("1st_back", 0) or 0)
            bf = float(odds_store[horse].get("betfair", {}).get("1st_back", 0) or 0)
            sportsbet_odds.append(sb)
            betfair_odds.append(bf)
            x.append(idx)

        self.plot_item.clear()
        self.legend = self.plot_item.addLegend(labelTextColor="w")

        width = 0.3
        sportsbet_bar = BarGraphItem(x=np.array(x) - width / 2, height=sportsbet_odds, width=width, brush='blue', name="Sportsbet")
        betfair_bar = BarGraphItem(x=np.array(x) + width / 2, height=betfair_odds, width=width, brush='green', name="Betfair")

        self.plot_item.addItem(sportsbet_bar)
        self.plot_item.addItem(betfair_bar)

        ticks = [[(i, horses[i]) for i in range(len(horses))]]
        self.bottom_axis.setTicks(ticks)

    def run_updater(self, odds_store):
        if not hasattr(self, 'timer'):
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(lambda: self.update_odds(odds_store))
            self.timer.start(1000)