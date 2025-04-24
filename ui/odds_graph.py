from PyQt6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
from pyqtgraph import PlotWidget, BarGraphItem
import numpy as np
from data.odds_store import shared_odds

class RaceDashboardCard(QtWidgets.QFrame):
    def __init__(self, race_info, race_index, parent=None):
        super().__init__(parent)
        self.race_index = race_index
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Header
        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel(f"{race_info['location']} - Race {race_info['race_number']}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        time = QtWidgets.QLabel(race_info['race_time'])
        time.setStyleSheet("font-size: 14px;")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(time)
        layout.addLayout(header)
        
        # Sum of Probabilities
        self.probabilities = QtWidgets.QLabel("Calculating probabilities...")
        self.probabilities.setWordWrap(True)
        self.probabilities.setStyleSheet("color: #90caf9; margin-top: 10px;")
        layout.addWidget(self.probabilities)
        
        # EVs
        self.ev = QtWidgets.QLabel("Calculating EVs...")
        self.ev.setStyleSheet("color: #4caf50; margin-top: 10px; font-weight: bold;")
        layout.addWidget(self.ev)
        
        # View Details Button
        self.view_button = QtWidgets.QPushButton("View Detailed Analysis")
        layout.addWidget(self.view_button)

class OddsGraph(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Racing Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        
        # Store matched races
        self.matched_races = []
        self.current_race_index = 0
        
        # Create stacked widget to hold different views
        self.stacked_widget = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create dashboard page
        self.dashboard_page = QtWidgets.QWidget()
        self.dashboard_layout = QtWidgets.QVBoxLayout(self.dashboard_page)
        
        # Dashboard header
        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Live Racing Dashboard")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; margin: 10px;")
        header.addWidget(title)
        header.addStretch()
        self.dashboard_layout.addLayout(header)
        
        # Grid for race cards
        self.race_grid = QtWidgets.QGridLayout()
        self.dashboard_layout.addLayout(self.race_grid)
        
        # Create detailed view page
        self.detail_page = QtWidgets.QWidget()
        detail_layout = QtWidgets.QVBoxLayout(self.detail_page)
        
        # Race selector for detailed view
        selector_layout = QtWidgets.QHBoxLayout()
        selector_label = QtWidgets.QLabel("Select Race:")
        selector_label.setStyleSheet("color: white; font-size: 14px;")
        self.race_selector = QtWidgets.QComboBox()
        self.race_selector.setStyleSheet("color: white; background-color: #333; padding: 5px;")
        self.race_selector.currentIndexChanged.connect(self.on_race_selected)
        selector_layout.addWidget(selector_label)
        selector_layout.addWidget(self.race_selector)
        selector_layout.addStretch()
        detail_layout.addLayout(selector_layout)
        
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
        detail_layout.addWidget(self.plot_widget)
        
        # Table
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Horse/Dog", "Betfair Odds", "Betfair Payout", "Sportsbet Odds",
            "Betfair Prob %", "Sportsbet Prob %"
        ])
        self.table.horizontalHeader().setStretchLastSection(False)
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.setStyleSheet("color: white; background-color: #222; gridline-color: #444;")
        detail_layout.addWidget(self.table)
        
        # Summary label
        self.summary_label = QtWidgets.QLabel()
        self.summary_label.setStyleSheet("color: white; font-size: 14px; margin-top: 10px;")
        detail_layout.addWidget(self.summary_label)
        
        # Back to dashboard button
        back_button = QtWidgets.QPushButton("← Back to Dashboard")
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #424242;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        back_button.clicked.connect(self.show_dashboard)
        detail_layout.addWidget(back_button)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.detail_page)
        
        # Show dashboard by default
        self.show_dashboard()

    def show_dashboard(self):
        self.stacked_widget.setCurrentWidget(self.dashboard_page)

    def show_detail_view(self):
        self.stacked_widget.setCurrentWidget(self.detail_page)

    def update_matched_races(self, races):
        """Update the list of matched races and populate both views."""
        self.matched_races = races
        self.race_selector.clear()
        
        # Clear existing race cards
        while self.race_grid.count():
            item = self.race_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Create race cards for dashboard
        for idx, race in enumerate(races):
            race_info = race['betfair']
            card = RaceDashboardCard(race_info, idx, self)
            card.view_button.clicked.connect(lambda checked, idx=idx: self.show_race_details(idx))
            row = idx // 2  # 2 cards per row
            col = idx % 2
            self.race_grid.addWidget(card, row, col)
            
            # Add to race selector
            race_text = f"{race_info['location']} - Race {race_info['race_number']} - {race_info['race_time']}"
            self.race_selector.addItem(race_text, idx)

    def show_race_details(self, race_index):
        """Show detailed view for the selected race."""
        self.current_race_index = race_index
        self.race_selector.setCurrentIndex(race_index)
        self.show_detail_view()
        self.update_odds(shared_odds)  # Refresh the display

    def get_betfair_commission_rate(self, race_type):
        """Return the Betfair commission rate based on race type."""
        return 0.08 if race_type == "greyhound" else 0.10  # 8% for greyhounds, 10% for horses

    def calculate_betfair_payout(self, odds, race_type):
        """Calculate actual payout for Betfair odds after commission."""
        if not odds or odds <= 0:
            return 0
        commission_rate = self.get_betfair_commission_rate(race_type)
        # The payout formula is: (odds - 1) * (1 - commission_rate) + 1
        return (odds - 1) * (1 - commission_rate) + 1

    def update_dashboard(self, odds_store):
        """Update the dashboard cards with latest odds information."""
        if not odds_store or 'races' not in odds_store:
            return
            
        race_odds = odds_store['races']
        for idx, race in enumerate(self.matched_races):
            card = self.race_grid.itemAt(idx).widget()
            if not card:
                continue
                
            race_key = f"{race['betfair']['location']}_R{race['betfair']['race_number']}"
            if race_key not in race_odds:
                continue
                
            race_data = race_odds[race_key]
            race_type = race['betfair']['race_type']
            
            # Calculate probabilities and best EV
            horses = sorted(race_data.keys())
            total_sb_prob = 0
            total_bf_prob = 0
            best_ev = 0  # Sum of minimum probabilities
            
            for horse in horses:
                # Clean horse names (remove apostrophes)
                clean_horse = horse.replace("'", "")
                if clean_horse != horse:
                    race_data[clean_horse] = race_data.pop(horse)
                    horse = clean_horse
                
                sb_odds = float(race_data[horse].get("sportsbet", {}).get("1st_back", 0) or 0)
                bf_odds = float(race_data[horse].get("betfair", {}).get("1st_back", 0) or 0)
                
                if sb_odds and bf_odds:
                    sb_prob = 1 / sb_odds if sb_odds > 0 else 0
                    # Calculate Betfair probability with commission
                    bf_payout = self.calculate_betfair_payout(bf_odds, race_type)
                    bf_prob = 1 / bf_payout if bf_payout > 0 else 0
                    
                    total_sb_prob += sb_prob
                    total_bf_prob += bf_prob
                    
                    # Take the lower probability (higher odds) for each horse
                    best_ev += min(sb_prob, bf_prob)

            # Calculate alternative EV based on sum of probabilities ratio
            alt_ev_sb = 1 / total_sb_prob if total_sb_prob > 0 else 0
            alt_ev_bf = 1 / total_bf_prob if total_bf_prob > 0 else 0
            alt_ev = max(alt_ev_sb, alt_ev_bf)  # Take the better EV between the two bookmakers
            
            # Update card content
            card.probabilities.setText(
                f"Sum of Probabilities:\n"
                f"Sportsbet: {total_sb_prob:.3f}\n"
                f"Betfair (with {self.get_betfair_commission_rate(race_type)*100:.0f}% commission): {total_bf_prob:.3f}"
            )
            
            # Color coding for EVs
            min_odds_color = "#4caf50" if best_ev <= 1 else "#f44336"
            sum_ratio_color = "#4caf50" if alt_ev >= 1 else "#f44336"
            
            card.ev.setText(
                f"<span style='color: {min_odds_color};'>Market Total: {best_ev:.1%}</span><br>"
                f"<span style='color: {sum_ratio_color};'>EV (Sum Ratio): {alt_ev:.3f}</span>"
            )

    def on_race_selected(self, index):
        """Handle race selection change."""
        if 0 <= index < len(self.matched_races):
            self.current_race_index = index
            # Update title with current race info
            race_info = self.matched_races[index]['betfair']
            self.plot_widget.setTitle(f"Live Odds: {race_info['location']} - Race {race_info['race_number']}", color="w", size="16pt")
            # Clear current display
            self.plot_item.clear()
            self.table.setRowCount(0)
            self.summary_label.clear()
            # Show detail view
            self.show_detail_view()

    def update_odds(self, odds_store):
        """Update both dashboard and detail view with current odds."""
        self.update_dashboard(odds_store)
        
        if not odds_store or 'races' not in odds_store:
            return

        # Get odds for current race
        race = self.matched_races[self.current_race_index]
        race_key = f"{race['betfair']['location']}_R{race['betfair']['race_number']}"
        race_odds = odds_store['races'].get(race_key, {})
        race_type = race['betfair']['race_type']
        
        if not race_odds:
            return

        horses = sorted(race_odds.keys())
        sportsbet_odds = []
        betfair_odds = []
        betfair_payouts = []
        x = []

        # Update table headers
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Horse/Dog", "Betfair Odds", "Betfair Payout", "Sportsbet Odds",
            "Betfair Prob %", "Sportsbet Prob %"
        ])

        # Set all columns to resize to content
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        self.table.setRowCount(len(horses))

        for row, horse in enumerate(horses):
            # Clean horse name
            horse = horse.replace("'", "")
            
            sb = float(race_odds[horse].get("sportsbet", {}).get("1st_back", 0) or 0)
            bf = float(race_odds[horse].get("betfair", {}).get("1st_back", 0) or 0)
            bf_payout = self.calculate_betfair_payout(bf, race_type)
            
            sportsbet_odds.append(sb)
            betfair_odds.append(bf)
            betfair_payouts.append(bf_payout)
            x.append(row)

            # Calculate probabilities
            sb_prob = 1 / sb if sb > 0 else 0
            bf_prob = 1 / bf_payout if bf_payout > 0 else 0

            items = [
                QtWidgets.QTableWidgetItem(horse),
                QtWidgets.QTableWidgetItem(f"{bf:.2f}"),
                QtWidgets.QTableWidgetItem(f"{bf_payout:.2f}"),
                QtWidgets.QTableWidgetItem(f"{sb:.2f}"),
                QtWidgets.QTableWidgetItem(f"{bf_prob*100:.1f}%"),
                QtWidgets.QTableWidgetItem(f"{sb_prob*100:.1f}%")
            ]

            # Set colors for best odds (comparing actual payouts)
            if bf_payout > 0 and sb > 0:
                if bf_payout > sb:
                    items[2].setBackground(QtGui.QColor("#4caf50"))  # Highlight Betfair payout
                    items[4].setBackground(QtGui.QColor("#4caf50"))  # Highlight Betfair prob
                elif sb > bf_payout:
                    items[3].setBackground(QtGui.QColor("#4caf50"))  # Highlight Sportsbet odds
                    items[5].setBackground(QtGui.QColor("#4caf50"))  # Highlight Sportsbet prob

            for col, item in enumerate(items):
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

        # Update plot
        self.plot_item.clear()
        self.legend = self.plot_item.addLegend(labelTextColor="w")

        width = 0.3
        sportsbet_bar = BarGraphItem(x=np.array(x) - width / 2, height=sportsbet_odds, width=width, brush=QtGui.QColor(0, 103, 171), name="Sportsbet")
        betfair_bar = BarGraphItem(x=np.array(x) + width / 2, height=betfair_payouts, width=width, brush=QtGui.QColor(255, 184, 12), name=f"Betfair (after {self.get_betfair_commission_rate(race_type)*100:.0f}% commission)")

        self.plot_item.addItem(sportsbet_bar)
        self.plot_item.addItem(betfair_bar)

        ticks = [[(i, horses[i]) for i in range(len(horses))]]
        self.bottom_axis.setTicks(ticks)

        # Calculate totals and EV using Betfair payouts
        sb_total_prob = sum(1/odds if odds > 0 else 0 for odds in sportsbet_odds)
        bf_total_prob = sum(1/payout if payout > 0 else 0 for payout in betfair_payouts)
        best_ev = sum(min(1/sb if sb > 0 else float('inf'), 
                         1/bf_payout if bf_payout > 0 else float('inf')) 
                     for sb, bf_payout in zip(sportsbet_odds, betfair_payouts))

        # Calculate alternative EV based on sum of probabilities ratio
        alt_ev_sb = 1 / sb_total_prob if sb_total_prob > 0 else 0
        alt_ev_bf = 1 / bf_total_prob if bf_total_prob > 0 else 0
        alt_ev = max(alt_ev_sb, alt_ev_bf)  # Take the better EV between the two bookmakers

        # Show summary with color coding
        summary_parts = []
        
        # Add bookmaker probabilities
        summary_parts.append(f"Sportsbet Total: {sb_total_prob*100:.1f}%")
        summary_parts.append(f"Betfair Total (with {self.get_betfair_commission_rate(race_type)*100:.0f}% commission): {bf_total_prob*100:.1f}%")
        
        # Add both EV calculations with color coding
        ev_color = "#4caf50" if best_ev <= 1 else "#f44336"
        alt_ev_color = "#4caf50" if alt_ev >= 1 else "#f44336"
        
        summary_parts.append(f"<span style='color: {ev_color};'><b>Market Total: {best_ev:.1%}</b></span>")
        summary_parts.append(f"<span style='color: {alt_ev_color};'><b>EV (Sum Ratio): {alt_ev:.3f}</b></span>")
        
        # Add betting strategy explanation
        if best_ev <= 1 or alt_ev >= 1:
            summary_parts.append("<br><br><b>Betting Strategy:</b> Take all highlighted (green) odds")
            if best_ev < 1:
                summary_parts.append(f"Market margin: {(1 - best_ev):.1%}")
            if alt_ev > 1:
                summary_parts.append(f"Expected return: {alt_ev:.3f}")

        self.summary_label.setText(" | ".join(summary_parts))

    def run_updater(self, odds_store):
        """Start the timer to update odds display."""
        if not hasattr(self, 'timer'):
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(lambda: self.update_odds(odds_store))
            self.timer.start(1000)
