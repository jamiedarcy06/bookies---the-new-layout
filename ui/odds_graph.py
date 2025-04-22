from PyQt6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
from pyqtgraph import PlotWidget, BarGraphItem
import numpy as np

class OddsGraph(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Odds Comparison")
        self.setGeometry(100, 100, 1000, 850)

        # Plot widget
        self.plot_widget = PlotWidget()
        self.plot_widget.setBackground("k")
        self.plot_item = self.plot_widget.getPlotItem()
        self.plot_item.layout.setContentsMargins(10, 10, 10, 50)
        self.plot_widget.setTitle("Live Odds: Sportsbet vs Betfair", color="w", size="16pt")
        self.plot_widget.showGrid(x=True, y=True)
        self.legend = self.plot_item.addLegend(labelTextColor="w")
        self.bottom_axis = self.plot_item.getAxis("bottom")
        self.bottom_axis.setStyle(autoExpandTextSpace=False)

        # Table
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Horse", "Betfair Odds", "Sportsbet Odds",
            "Betfair Prob", "Sportsbet Prob",
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet("color: white; background-color: #222; gridline-color: #444;")

        # Summary label
        self.summary_label = QtWidgets.QLabel()
        self.summary_label.setStyleSheet("color: white; font-size: 14px; margin-top: 10px;")

        # Layout
        layout = QtWidgets.QVBoxLayout()
        container = QtWidgets.QWidget()
        container.setLayout(layout)
        layout.addWidget(self.plot_widget)
        layout.addWidget(self.table)
        layout.addWidget(self.summary_label)
        self.setCentralWidget(container)

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
        sportsbet_bar = BarGraphItem(x=np.array(x) - width / 2, height=sportsbet_odds, width=width, brush=QtGui.QColor(0, 103, 171), name="Sportsbet")
        betfair_bar = BarGraphItem(x=np.array(x) + width / 2, height=betfair_odds, width=width, brush=QtGui.QColor(255, 184, 12), name="Betfair")

        self.plot_item.addItem(sportsbet_bar)
        self.plot_item.addItem(betfair_bar)

        ticks = [[(i, horses[i]) for i in range(len(horses))]]
        self.bottom_axis.setTicks(ticks)

        # Table and EV Analysis
        self.table.setRowCount(len(horses))

        best_ev = -float("inf")
        best_row = -1
        sb_total_prob = 0
        bf_total_prob = 0
        best_bet_total_prob = 0

        for row, horse in enumerate(horses):
            sb_odds = sportsbet_odds[row]
            bf_odds = betfair_odds[row]

            sb_prob = 1 / sb_odds if sb_odds > 0 else 0
            bf_prob = 1 / bf_odds if bf_odds > 0 else 0

            sb_total_prob += sb_prob
            bf_total_prob += bf_prob

            best_bet_total_prob += min(sb_prob, bf_prob)

            items = [
                QtWidgets.QTableWidgetItem(horse),
                QtWidgets.QTableWidgetItem(f"{bf_odds:.2f}"),
                QtWidgets.QTableWidgetItem(f"{sb_odds:.2f}"),
                QtWidgets.QTableWidgetItem(f"{bf_prob:.2%}"),
                QtWidgets.QTableWidgetItem(f"{sb_prob:.2%}"),
            ]

            for col, item in enumerate(items):
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

        # Show totals and best EV
        summary = (
            f"<b>Sum of Probabilities</b>: "
            f"Sportsbet = {sb_total_prob:.2%}, "
            f"Betfair = {bf_total_prob:.2%} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; "
            f"Best Bet = {best_bet_total_prob:.2%}"
        )
        self.summary_label.setText(summary)

    def run_updater(self, odds_store):
        if not hasattr(self, 'timer'):
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(lambda: self.update_odds(odds_store))
            self.timer.start(1000)


