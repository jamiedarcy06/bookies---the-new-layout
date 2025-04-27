from PyQt6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
from pyqtgraph import PlotWidget, BarGraphItem
import numpy as np
from data.odds_store import shared_odds

# Define color scheme
COLORS = {
    'background': '#1a1a1a',
    'card_bg': '#2d2d2d',
    'text': '#ffffff',
    'accent1': '#00b8d4',  # Cyan
    'accent2': '#64dd17',  # Light Green
    'warning': '#ff9100',  # Orange
    'error': '#ff1744',    # Red
    'header': '#37474f',   # Blue Grey
}

class MarketDepthWidget(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['card_bg']}; border-radius: 5px;")
        layout = QtWidgets.QVBoxLayout(self)
        
        # Header
        header = QtWidgets.QLabel("Market Depth")
        header.setStyleSheet(f"color: {COLORS['accent1']}; font-size: 14px; font-weight: bold;")
        layout.addWidget(header)
        
        # Depth chart
        self.depth_plot = pg.PlotWidget(background=COLORS['background'])
        self.depth_plot.setTitle("Back Volume by Runner", color=COLORS['text'])
        self.depth_plot.showGrid(x=True, y=True, alpha=0.3)
        self.depth_plot.setLabel('left', 'Volume ($)', color=COLORS['text'])
        self.depth_plot.getAxis('bottom').setStyle(tickTextOffset=10)
        layout.addWidget(self.depth_plot)

    def update_depth(self, horses_data):
        """Update the market depth display for all horses"""
        self.depth_plot.clear()
        
        if not horses_data:
            return
            
        # Use the same sorting as the odds graph
        horses = sorted(horses_data.keys())
        x = []  # For horse indices
        volumes = []  # For volumes
        horse_names = []  # For x-axis labels
        
        for idx, horse in enumerate(horses):
            # Get display name from data
            display_name = horses_data[horse].get("display_name", horse)
            data = horses_data[horse]
            betfair_data = data.get('betfair', {})
            volume = parse_volume(betfair_data.get('1st_back_dom', 0))
            
            # Always add the horse to maintain same order as odds graph
            x.append(idx)
            volumes.append(volume)
            horse_names.append(display_name)
        
        if not x:  # No valid data
            return
            
        # Create bar graph
        bar = pg.BarGraphItem(
            x=x,
            height=volumes,
            width=0.6,
            brush=pg.mkBrush(color=COLORS['accent2']),
            name='Back Volume'
        )
        self.depth_plot.addItem(bar)
        
        # Set x-axis ticks to horse names
        ticks = [[(i, name) for i, name in enumerate(horse_names)]]
        self.depth_plot.getAxis('bottom').setTicks(ticks)
        
        # Update labels
        self.depth_plot.setTitle("Market Depth by Runner", color=COLORS['text'])
        self.depth_plot.setLabel('left', 'Volume ($)', color=COLORS['text'])

def parse_volume(vol_str):
    """Parse volume string to float, handling currency symbols"""
    if not vol_str:
        return 0
    # Remove currency symbols and commas
    clean_str = str(vol_str).replace('$', '').replace(',', '')
    try:
        return float(clean_str)
    except (ValueError, TypeError):
        return 0

class PriceHistoryWidget(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['card_bg']}; border-radius: 5px;")
        layout = QtWidgets.QVBoxLayout(self)
        
        # Header
        header = QtWidgets.QLabel("Price History")
        header.setStyleSheet(f"color: {COLORS['accent1']}; font-size: 14px; font-weight: bold;")
        layout.addWidget(header)
        
        # Price chart
        self.price_plot = pg.PlotWidget(background=COLORS['background'])
        self.price_plot.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.price_plot)

class RaceDashboardCard(QtWidgets.QFrame):
    def __init__(self, race_info, race_index, parent=None):
        super().__init__(parent)
        self.race_index = race_index
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card_bg']};
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
            }}
            QLabel {{
                color: {COLORS['text']};
            }}
            QPushButton {{
                background-color: {COLORS['accent1']};
                color: {COLORS['text']};
                border-radius: 5px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent2']};
            }}
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Header with status indicator
        header = QtWidgets.QHBoxLayout()
        status_indicator = QtWidgets.QLabel("●")
        status_indicator.setStyleSheet(f"color: {COLORS['accent2']}; font-size: 16px;")
        title = QtWidgets.QLabel(f"{race_info['location']} - Race {race_info['race_number']}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        time = QtWidgets.QLabel(race_info['race_time'])
        time.setStyleSheet("font-size: 14px;")
        header.addWidget(status_indicator)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(time)
        layout.addLayout(header)
        
        # Race type with enhanced styling
        race_type = race_info.get('race_type', 'unknown')
        race_type_label = QtWidgets.QLabel(race_type.title())
        race_type_label.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text']};
            background-color: {COLORS['header']};
            border-radius: 4px;
            padding: 2px 6px;
            margin: 2px;
        """)
        layout.addWidget(race_type_label)
        
        # Probabilities with progress bars
        self.probabilities = QtWidgets.QLabel("Calculating probabilities...")
        self.probabilities.setWordWrap(True)
        self.probabilities.setStyleSheet(f"color: {COLORS['accent1']}; margin-top: 10px;")
        layout.addWidget(self.probabilities)
        
        # EVs with enhanced visibility
        self.ev = QtWidgets.QLabel("Calculating EVs...")
        self.ev.setStyleSheet(f"color: {COLORS['accent2']}; margin-top: 10px; font-weight: bold;")
        layout.addWidget(self.ev)
        
        # Analysis button
        self.view_button = QtWidgets.QPushButton("Analysis")
        layout.addWidget(self.view_button)

class BetfairComparisonWidget(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['card_bg']}; border-radius: 5px;")
        layout = QtWidgets.QVBoxLayout(self)
        
        # Header
        header = QtWidgets.QLabel("Betfair Lay vs Back")
        header.setStyleSheet(f"color: {COLORS['accent1']}; font-size: 14px; font-weight: bold;")
        layout.addWidget(header)
        
        # Comparison chart
        self.comparison_plot = pg.PlotWidget(background=COLORS['background'])
        self.comparison_plot.showGrid(x=True, y=True, alpha=0.3)
        self.comparison_plot.setLabel('left', 'Odds (capped at 100)', color=COLORS['text'])
        self.comparison_plot.getAxis('bottom').setStyle(tickTextOffset=10)
        # Set y-axis range to 0-100
        self.comparison_plot.setYRange(0, 100)
        layout.addWidget(self.comparison_plot)

    def update_comparison(self, horses_data):
        """Update the Betfair lay vs back comparison display"""
        self.comparison_plot.clear()
        
        if not horses_data:
            return
            
        # Sort horses to maintain consistent order
        horses = sorted(horses_data.keys())
        x = []  # For horse indices
        back_odds = []  # For back odds
        lay_odds = []   # For lay odds
        horse_names = []  # For x-axis labels
        capped_indicators = []  # To store which bars are capped
        
        for idx, horse in enumerate(horses):
            # Clean horse name
            horse = horse.replace("'", "")
            data = horses_data[horse].get('betfair', {})
            
            back = float(data.get('1st_back', 0) or 0)
            lay = float(data.get('1st_lay', 0) or 0)
            
            # Cap the displayed values at 100
            back_display = min(back, 100)
            lay_display = min(lay, 100)
            
            x.append(idx)
            back_odds.append(back_display)
            lay_odds.append(lay_display)
            horse_names.append(horse)
            capped_indicators.append((back > 100, lay > 100))
        
        if not x:  # No valid data
            return
            
        width = 0.3
        # Create bars
        back_bar = pg.BarGraphItem(
            x=np.array(x) - width/2,
            height=back_odds,
            width=width,
            brush=pg.mkBrush(color=COLORS['accent2']),  # Green for back
            name='Back'
        )
        lay_bar = pg.BarGraphItem(
            x=np.array(x) + width/2,
            height=lay_odds,
            width=width,
            brush=pg.mkBrush(color=COLORS['error']),  # Red for lay
            name='Lay'
        )
        
        self.comparison_plot.addItem(back_bar)
        self.comparison_plot.addItem(lay_bar)
        
        # Add "+" indicators for capped values
        for idx, (back_capped, lay_capped) in enumerate(capped_indicators):
            if back_capped:
                text = pg.TextItem("+", color=COLORS['text'], anchor=(0.5, 0))
                text.setPos(idx - width/2, 100)
                self.comparison_plot.addItem(text)
            if lay_capped:
                text = pg.TextItem("+", color=COLORS['text'], anchor=(0.5, 0))
                text.setPos(idx + width/2, 100)
                self.comparison_plot.addItem(text)
        
        # Set x-axis ticks to horse names
        ticks = [[(i, name) for i, name in enumerate(horse_names)]]
        self.comparison_plot.getAxis('bottom').setTicks(ticks)
        
        # Add legend
        self.comparison_plot.addLegend(labelTextColor=COLORS['text'])

class OddsGraph(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Racing Analytics Terminal")
        self.setGeometry(100, 100, 1600, 900)
        
        # Set window background
        self.setStyleSheet(f"background-color: {COLORS['background']};")
        
        # Store matched races
        self.matched_races = []
        self.current_race_index = 0
        
        # Helper functions
        def parse_volume(vol_str):
            """Parse volume string to float, handling currency symbols"""
            if not vol_str:
                return 0
            # Remove currency symbols and commas
            clean_str = str(vol_str).replace('$', '').replace(',', '')
            try:
                return float(clean_str)
            except (ValueError, TypeError):
                return 0
        self.parse_volume = parse_volume

        # Create main widget and layout
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QtWidgets.QHBoxLayout(main_widget)
        
        # Left sidebar for race list and filters
        left_sidebar = QtWidgets.QFrame()
        left_sidebar.setStyleSheet(f"background-color: {COLORS['card_bg']}; border-radius: 10px;")
        left_sidebar.setMaximumWidth(300)
        left_layout = QtWidgets.QVBoxLayout(left_sidebar)
        
        # Search and filters
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setPlaceholderText("Search races...")
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['accent1']};
                border-radius: 5px;
                padding: 5px;
            }}
        """)
        self.search_box.textChanged.connect(self.filter_races)
        left_layout.addWidget(self.search_box)
        
        # Race list
        self.race_list = QtWidgets.QListWidget()
        self.race_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                border: none;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent1']};
            }}
        """)
        self.race_list.itemClicked.connect(self.on_race_list_clicked)
        left_layout.addWidget(self.race_list)
        
        main_layout.addWidget(left_sidebar)
        
        # Create stacked widget for main content
        self.stacked_widget = QtWidgets.QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Create dashboard page
        self.dashboard_page = QtWidgets.QWidget()
        self.dashboard_layout = QtWidgets.QVBoxLayout(self.dashboard_page)
        
        # Dashboard header with stats
        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Live Racing Analytics")
        title.setStyleSheet(f"color: {COLORS['text']}; font-size: 24px; font-weight: bold; margin: 10px;")
        header.addWidget(title)
        
        # Add market statistics
        stats_frame = QtWidgets.QFrame()
        stats_frame.setStyleSheet(f"background-color: {COLORS['card_bg']}; border-radius: 5px; padding: 5px;")
        stats_layout = QtWidgets.QHBoxLayout(stats_frame)
        
        total_volume = QtWidgets.QLabel("Total Volume: $0")
        total_volume.setStyleSheet(f"color: {COLORS['accent1']}; font-size: 14px;")
        active_markets = QtWidgets.QLabel("Active Markets: 0")
        active_markets.setStyleSheet(f"color: {COLORS['accent2']}; font-size: 14px;")
        
        stats_layout.addWidget(total_volume)
        stats_layout.addWidget(active_markets)
        header.addWidget(stats_frame)
        header.addStretch()
        
        self.dashboard_layout.addLayout(header)
        
        # Grid for race cards
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        scroll_content = QtWidgets.QWidget()
        self.race_grid = QtWidgets.QGridLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        self.dashboard_layout.addWidget(scroll_area)
        
        # Create detailed view page
        self.detail_page = QtWidgets.QWidget()
        detail_layout = QtWidgets.QVBoxLayout(self.detail_page)
        
        # Top bar with race selector and controls
        top_bar = QtWidgets.QHBoxLayout()
        
        # Race selector
        selector_layout = QtWidgets.QHBoxLayout()
        selector_label = QtWidgets.QLabel("Select Race:")
        selector_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 14px;")
        self.race_selector = QtWidgets.QComboBox()
        self.race_selector.setStyleSheet(f"""
            QComboBox {{
                color: {COLORS['text']};
                background-color: {COLORS['card_bg']};
                padding: 5px;
                border: 1px solid {COLORS['accent1']};
                border-radius: 5px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: url(down_arrow.png);
            }}
        """)
        self.race_selector.currentIndexChanged.connect(self.on_race_selected)
        selector_layout.addWidget(selector_label)
        selector_layout.addWidget(self.race_selector)
        top_bar.addLayout(selector_layout)
        top_bar.addStretch()
        detail_layout.addLayout(top_bar)
        
        # Create split view for detailed analysis
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        
        # Left side - Main chart and Betfair comparison
        left_pane = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_pane)
        
        # Main price chart
        self.plot_widget = PlotWidget()
        self.plot_widget.setBackground(COLORS['background'])
        self.plot_item = self.plot_widget.getPlotItem()
        self.plot_item.layout.setContentsMargins(10, 10, 10, 50)
        self.plot_widget.setTitle("Live Odds Analysis", color=COLORS['text'], size="16pt")
        self.plot_widget.showGrid(x=True, y=True)
        self.legend = self.plot_item.addLegend(labelTextColor=COLORS['text'])
        self.bottom_axis = self.plot_item.getAxis("bottom")
        self.bottom_axis.setStyle(autoExpandTextSpace=False)
        left_layout.addWidget(self.plot_widget)
        
        # Betfair comparison widget
        betfair_comparison = BetfairComparisonWidget()
        left_layout.addWidget(betfair_comparison)
        
        splitter.addWidget(left_pane)
        
        # Right side - Order book and statistics
        right_pane = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_pane)
        
        # Enhanced table with order book
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Runner", "Betfair Back", "Betfair Lay", "Market Depth", "Betfair Payout", "Sportsbet Odds"
        ])
        self.table.horizontalHeader().setStretchLastSection(False)
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                color: {COLORS['text']};
                background-color: {COLORS['background']};
                gridline-color: {COLORS['card_bg']};
                border: none;
            }}
            QHeaderView::section {{
                background-color: {COLORS['header']};
                color: {COLORS['text']};
                padding: 5px;
                border: 1px solid {COLORS['card_bg']};
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
        """)
        right_layout.addWidget(self.table)
        
        # Market statistics
        stats_group = QtWidgets.QGroupBox("Market Statistics")
        stats_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['text']};
                border: 1px solid {COLORS['accent1']};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }}
        """)
        stats_layout = QtWidgets.QVBoxLayout(stats_group)
        self.summary_label = QtWidgets.QLabel()
        self.summary_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 14px;")
        stats_layout.addWidget(self.summary_label)
        right_layout.addWidget(stats_group)
        
        splitter.addWidget(right_pane)
        detail_layout.addWidget(splitter)
        
        # Navigation bar
        nav_bar = QtWidgets.QHBoxLayout()
        back_button = QtWidgets.QPushButton("← Back to Dashboard")
        back_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['card_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['accent1']};
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent1']};
            }}
        """)
        back_button.clicked.connect(self.show_dashboard)
        nav_bar.addWidget(back_button)
        nav_bar.addStretch()
        detail_layout.addLayout(nav_bar)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.detail_page)
        
        # Show dashboard by default
        self.show_dashboard()

    def show_dashboard(self):
        self.stacked_widget.setCurrentWidget(self.dashboard_page)

    def show_detail_view(self):
        self.stacked_widget.setCurrentWidget(self.detail_page)

    def filter_races(self):
        """Filter races based on search text"""
        search_text = self.search_box.text().lower()
        
        # Clear and repopulate race list based on filter
        self.race_list.clear()
        
        for idx, race in enumerate(self.matched_races):
            race_info = race['betfair']
            race_text = f"{race_info['location']} - Race {race_info['race_number']} - {race_info['race_time']}"
            
            # Check if search text appears in any part of the race information
            if (search_text in race_info['location'].lower() or
                search_text in str(race_info['race_number']).lower() or
                search_text in race_info['race_time'].lower() or
                search_text in race_info.get('race_type', '').lower()):
                
                item = QtWidgets.QListWidgetItem(race_text)
                item.setData(QtCore.Qt.ItemDataRole.UserRole, idx)  # Store race index
                self.race_list.addItem(item)

    def on_race_list_clicked(self, item):
        """Handle race selection from the list"""
        race_index = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self.show_race_details(race_index)

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
            
            # Add to race selector and race list
            race_text = f"{race_info['location']} - Race {race_info['race_number']} - {race_info['race_time']}"
            self.race_selector.addItem(race_text, idx)
            
            # Add to race list
            item = QtWidgets.QListWidgetItem(race_text)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, idx)
            self.race_list.addItem(item)

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
                # Get display name from data
                display_name = race_data[horse].get("display_name", horse)
                
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
            race_type = race_info.get('race_type', 'unknown').title()
            self.plot_widget.setTitle(f"Live Odds: {race_info['location']} - Race {race_info['race_number']} ({race_type})", color="w", size="16pt")
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
        if not self.matched_races or self.current_race_index >= len(self.matched_races):
            return
            
        race = self.matched_races[self.current_race_index]
        race_key = f"{race['betfair']['location']}_R{race['betfair']['race_number']}"
        race_odds = odds_store['races'].get(race_key, {})
        race_type = race['betfair']['race_type']
        
        if not race_odds:
            return

        horses = sorted(race_odds.keys())

        # Update market depth with all horses' data
        market_depth = self.findChild(MarketDepthWidget)
        if market_depth:
            market_depth.update_depth(race_odds)

        sportsbet_odds = []
        betfair_odds = []
        betfair_payouts = []
        x = []

        # Update table headers
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Runner", "Betfair Back", "Betfair Lay", "Market Depth", "Betfair Payout", "Sportsbet Odds"
        ])

        # Set all columns to resize to content
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        self.table.setRowCount(len(horses))

        for row, horse in enumerate(horses):
            # Get display name from data
            display_name = race_odds[horse].get("display_name", horse)
            
            sb = float(race_odds[horse].get("sportsbet", {}).get("1st_back", 0) or 0)
            bf_back = float(race_odds[horse].get("betfair", {}).get("1st_back", 0) or 0)
            bf_lay = float(race_odds[horse].get("betfair", {}).get("1st_lay", 0) or 0)
            bf_payout = self.calculate_betfair_payout(bf_back, race_type)
            
            # Get volume from DOM
            volume = self.parse_volume(race_odds[horse].get("betfair", {}).get("1st_back_dom", 0))
            
            sportsbet_odds.append(sb)
            betfair_odds.append(bf_back)
            betfair_payouts.append(bf_payout)
            x.append(row)

            items = [
                QtWidgets.QTableWidgetItem(display_name),
                QtWidgets.QTableWidgetItem(f"{bf_back:.2f}"),
                QtWidgets.QTableWidgetItem(f"{bf_lay:.2f}"),
                QtWidgets.QTableWidgetItem(f"${volume:,.2f}"),
                QtWidgets.QTableWidgetItem(f"{bf_payout:.2f}"),
                QtWidgets.QTableWidgetItem(f"{sb:.2f}")
            ]

            # Set colors for best odds (comparing actual payouts)
            if bf_payout > 0 and sb > 0:
                if bf_payout > sb:
                    items[4].setBackground(QtGui.QColor("#4caf50"))  # Highlight Betfair payout
                elif sb > bf_payout:
                    items[5].setBackground(QtGui.QColor("#4caf50"))  # Highlight Sportsbet odds

            for col, item in enumerate(items):
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            # Update market depth when row is selected
            self.table.itemSelectionChanged.connect(
                lambda: self.update_selected_runner_depth(race_odds)
            )

        # Update plot
        self.plot_item.clear()
        self.legend = self.plot_item.addLegend(labelTextColor="w")

        width = 0.3
        betfair_bar = BarGraphItem(
            x=np.array(x) - width/2,
            height=betfair_payouts,
            width=width,
            brush=QtGui.QColor(255, 184, 12),
            name=f"Betfair (after {self.get_betfair_commission_rate(race_type)*100:.0f}% commission)"
        )
        sportsbet_bar = BarGraphItem(
            x=np.array(x) + width/2,
            height=sportsbet_odds,
            width=width,
            brush=QtGui.QColor(0, 103, 171),
            name="Sportsbet"
        )

        self.plot_item.addItem(betfair_bar)
        self.plot_item.addItem(sportsbet_bar)

        # Use display names for x-axis labels
        ticks = [[(i, race_odds[horses[i]].get("display_name", horses[i])) for i in range(len(horses))]]
        self.bottom_axis.setTicks(ticks)

        # Calculate totals and EV
        sb_total_prob = sum(1/odds if odds > 0 else 0 for odds in sportsbet_odds)
        bf_total_prob = sum(1/payout if payout > 0 else 0 for payout in betfair_payouts)
        
        # Calculate EV based on sum of probabilities ratio
        alt_ev_sb = 1 / sb_total_prob if sb_total_prob > 0 else 0
        alt_ev_bf = 1 / bf_total_prob if bf_total_prob > 0 else 0
        alt_ev = max(alt_ev_sb, alt_ev_bf)  # Take the better EV between the two bookmakers

        # Show summary with color coding
        summary_parts = []
        
        # Add bookmaker probabilities
        summary_parts.append(f"Sportsbet Total: {sb_total_prob*100:.1f}%")
        summary_parts.append(f"Betfair Total (with {self.get_betfair_commission_rate(race_type)*100:.0f}% commission): {bf_total_prob*100:.1f}%")
        
        # Add EV calculation with color coding
        alt_ev_color = "#4caf50" if alt_ev >= 1 else "#f44336"
        
        # Create a styled QLabel for EV
        ev_label = QtWidgets.QLabel()
        ev_label.setStyleSheet(f"color: {alt_ev_color}; font-weight: bold;")
        ev_label.setText(f"EV (Sum Ratio): {alt_ev:.3f}")
        
        # Join the probability summaries
        prob_summary = " | ".join(summary_parts)
        
        # Add betting strategy explanation if profitable
        strategy = ""
        if alt_ev >= 1:
            strategy = f"\n\nBetting Strategy: Take all highlighted (green) odds\nExpected return: {alt_ev:.3f}"
            
        # Set the complete text
        self.summary_label.setText(f"{prob_summary}\n\n{ev_label.text()}{strategy}")

        # Update Betfair comparison widget
        betfair_comparison = self.findChild(BetfairComparisonWidget)
        if betfair_comparison:
            betfair_comparison.update_comparison(race_odds)

    def update_selected_runner_depth(self, race_odds):
        """Update market depth display for the selected runner"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
            
        # Get the runner name from the first column of the selected row
        display_name = self.table.item(selected_items[0].row(), 0).text()
        # Convert to lowercase for dictionary lookup
        runner_key = display_name.lower()
        
        # Update market depth with all race data
        market_depth = self.findChild(MarketDepthWidget)
        if market_depth and runner_key in race_odds:
            market_depth.update_depth(race_odds)

    def run_updater(self, odds_store):
        """Start the timer to update odds display."""
        if not hasattr(self, 'timer'):
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(lambda: self.update_odds(odds_store))
            self.timer.start(1000)

