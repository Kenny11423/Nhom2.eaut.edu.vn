from __future__ import annotations

import sys
from datetime import datetime, timedelta
from typing import Any, cast

from PySide6.QtCore import QDate, QTime, Qt
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QRadioButton,
    QScrollArea,
    QStackedWidget,
    QStatusBar,
    QSpinBox,
    QButtonGroup,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from src.train_ticket_app.backend.database import DatabaseManager
from src.train_ticket_app.backend.service import TicketService

try:
    from PySide6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QValueAxis
except ImportError:
    QBarCategoryAxis = QBarSeries = QBarSet = QChart = QChartView = QValueAxis = None


APP_STYLESHEET = """
QWidget {
    background: #f4f7fb;
    color: #17324d;
    font-size: 14px;
}
QMainWindow, QDialog {
    background: #f4f7fb;
}
QGroupBox, QTabWidget::pane, QTableWidget, QLineEdit, QComboBox, QDateEdit, QPlainTextEdit {
    background: #ffffff;
}
QGroupBox {
    border: 1px solid #cbd5e1;
    border-radius: 14px;
    margin-top: 10px;
    padding-top: 14px;
    font-weight: 700;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QLineEdit, QComboBox, QDateEdit, QPlainTextEdit {
    border: 1px solid #b9c8dd;
    border-radius: 8px;
    padding: 8px 10px;
}
QPushButton {
    background: #0d6e8a;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    font-weight: 700;
}
QPushButton:hover {
    background: #0b6179;
}
QPushButton#successButton { background: #2f855a; }
QPushButton#dangerButton { background: #b54747; }
QPushButton#seatAvailable {
    background: #ffffff;
    color: #1f3b5b;
    border: 3px solid #3b82f6;
    border-radius: 18px;
    min-width: 108px;
    min-height: 84px;
    padding: 12px 10px;
}
QPushButton#seatBooked {
    background: #edf1f5;
    color: #9aa8b8;
    border: 3px solid #d8e1ea;
    border-radius: 18px;
    min-width: 108px;
    min-height: 84px;
    padding: 12px 10px;
}
QPushButton#seatSelected {
    background: #ec4899;
    color: #ffffff;
    border: 3px solid #db2777;
    border-radius: 18px;
    min-width: 108px;
    min-height: 84px;
    padding: 12px 10px;
}
QTableWidget {
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    gridline-color: #d8e1ee;
}
QHeaderView::section {
    background: #12344d;
    color: #ffffff;
    padding: 8px;
    border: none;
    font-weight: 700;
}
QTabBar::tab {
    background: #dcecff;
    color: #244b72;
    padding: 10px 16px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 6px;
    font-weight: 700;
}
QTabBar::tab:selected {
    background: #12344d;
    color: #ffffff;
}
QListWidget {
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    background: #ffffff;
}
QStatusBar {
    background: #ffffff;
}
"""

# Master Route Data (Code, Cumulative Distance in Km)
MASTER_ROUTE_DATA = [
    ("HN", 0), ("PL", 56), ("ND", 87), ("NB", 115), ("TH", 176), 
    ("V", 319), ("DH", 522), ("DHA", 622), ("HU", 688), ("DN", 791), 
    ("TK", 865), ("QN", 928), ("DT", 1096), ("THO", 1198), ("NT", 1315), 
    ("TC", 1408), ("BT", 1551), ("BH", 1697), ("DA", 1707), ("SG", 1726)
]
ROUTE_TEMPLATE_ORDER = [item[0] for item in MASTER_ROUTE_DATA]
ROUTE_TEMPLATE_DISTANCES = {item[0]: item[1] for item in MASTER_ROUTE_DATA}


class LoginDialog(QDialog):
    def __init__(self, service: TicketService) -> None:
        super().__init__()
        self.service = service
        self.user: dict[str, Any] | None = None
        self.setWindowTitle("Hệ thống vé tàu - Đăng nhập")
        self.resize(400, 280)
        self.setStyleSheet(APP_STYLESHEET)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        title = QLabel("HỆ THỐNG QUẢN LÝ BÁN VÉ TÀU")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #0d6e8a; margin-bottom: 5px;")
        layout.addWidget(title)

        hint = QLabel("Vui lòng đăng nhập để tiếp tục")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #64748b; font-size: 13px;")
        layout.addWidget(hint)

        demo_hint = QLabel("Demo: admin/admin123, staff/staff123, user/user")
        demo_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        demo_hint.setStyleSheet("color: #94a3b8; font-style: italic;")
        layout.addWidget(demo_hint)

        form = QFormLayout()
        self.username_input = QLineEdit("user")
        self.password_input = QLineEdit("user")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Tên đăng nhập", self.username_input)
        form.addRow("Mật khẩu", self.password_input)
        layout.addLayout(form)

        self.message_label = QLabel("")
        self.message_label.setStyleSheet("color: #b91c1c;")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)

        login_button = QPushButton("Đăng nhập")
        login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        login_button.clicked.connect(self._attempt_login)
        layout.addWidget(login_button)

    def _attempt_login(self) -> None:
        user = self.service.login(self.username_input.text(), self.password_input.text())
        if not user:
            self.message_label.setText("Sai tài khoản hoặc mật khẩu")
            return
        self.user = user
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, service: TicketService, current_user: dict[str, Any]) -> None:
        super().__init__()
        self.service = service
        self.current_user = current_user
        self.catalog: dict[str, list[dict[str, Any]]] = {"stations": [], "trains": [], "carriages": [], "routes": [], "users": []}
        self.trip_rows: list[dict[str, Any]] = []
        self.ticket_rows: list[dict[str, Any]] = []
        self.schedule_rows: list[dict[str, Any]] = []
        self.current_trip_carriages: list[dict[str, Any]] = []
        self.current_seat_rows: list[dict[str, Any]] = []
        self.schedule_detail_rows: list[dict[str, Any]] = []
        self.template_rows: list[dict[str, Any]] = []
        self.audit_rows: list[dict[str, Any]] = []
        self.planned_stops: list[dict[str, Any]] = []
        self.my_ticket_rows: list[dict[str, Any]] = []
        self.current_planner_route_stations: list[dict[str, Any]] = []
        self.planned_carriage_ids: list[int] = []
        self.template_carriage_ids: list[int] = []
        self.selected_trip: dict[str, Any] | None = None
        self.selected_carriage: dict[str, Any] | None = None
        self.selected_seat: dict[str, Any] | None = None
        self.selected_schedule_trip: dict[str, Any] | None = None
        self.selected_schedule_stop: dict[str, Any] | None = None
        
        # UI attributes for Trip Planner (Wizard and Legacy)
        self.plan_trip_code: QLineEdit | None = None
        self.plan_trip_code_input: QLineEdit | None = None
        self.plan_train_type: QComboBox | None = None
        self.plan_train_combo: QComboBox | None = None
        self.plan_base_price_input: QLineEdit | None = None
        self.plan_captain_combo: QComboBox | None = None
        self.plan_crew_code: QComboBox | None = None
        self.plan_departure_date: QDateEdit | None = None
        self.plan_departure_input: QTimeEdit | None = None
        self.plan_route_base: QComboBox | None = None
        self.plan_origin_combo: QComboBox | None = None
        self.plan_destination_combo: QComboBox | None = None
        self.plan_template_combo: QComboBox | None = None
        self.plan_carriage_combo: QComboBox | None = None
        self.plan_timetable_table: QTableWidget | None = None
        self.plan_avail_carriages: QListWidget | None = None
        self.plan_train_composition: QListWidget | None = None
        self.plan_summary: QPlainTextEdit | None = None
        self.plan_stop_list: QListWidget | None = None
        self.plan_carriage_list: QListWidget | None = None
        
        # Other dynamic UI attributes
        self.station_completer: QCompleter | None = None
        self.planner_stack: QStackedWidget | None = None
        self.planner_progress: QProgressBar | None = None
        self.audit_table: QTableWidget | None = None
        self.staff_table: QTableWidget | None = None
        self.selected_staff_id: int | None = None
        self.audit_query_input: QLineEdit | None = None
        self.audit_category_filter: QComboBox | None = None

        self.stat_labels: dict[str, QLabel] = {}
        self.revenue_chart_placeholder: QWidget | None = None
        self.occupancy_chart_placeholder: QWidget | None = None
        self.schedule_table: QTableWidget | None = None
        self.schedule_station_combo: QComboBox | None = None
        self.schedule_stop_order_input: QSpinBox | None = None
        self.schedule_arrival_enabled: QCheckBox | None = None
        self.schedule_arrival_time: QTimeEdit | None = None
        self.schedule_departure_enabled: QCheckBox | None = None
        self.schedule_departure_time: QTimeEdit | None = None
        self.schedule_trip_label: QLabel | None = None
        self.schedule_stop_table: QTableWidget | None = None
        self.schedule_date_filter: QDateEdit | None = None

        self.template_name_input: QLineEdit | None = None
        self.template_description_input: QPlainTextEdit | None = None
        self.template_carriage_combo: QComboBox | None = None
        self.template_carriage_list: QListWidget | None = None
        self.template_list: QListWidget | None = None

        self.station_table: QTableWidget | None = None
        self.train_table: QTableWidget | None = None
        self.carriage_table_catalog: QTableWidget | None = None
        self.station_code_input: QLineEdit | None = None
        self.station_name_input: QLineEdit | None = None
        self.station_city_input: QLineEdit | None = None
        self.train_code_input: QLineEdit | None = None
        self.train_name_input: QLineEdit | None = None
        self.new_carriage_code_input: QLineEdit | None = None
        self.new_carriage_type_input: QLineEdit | None = None
        self.new_carriage_count_input: QLineEdit | None = None

        self.my_ticket_table: QTableWidget | None = None
        self.profile_name: QLineEdit | None = None
        self.profile_user: QLineEdit | None = None
        self.profile_role: QLineEdit | None = None

        self.origin_input: QLineEdit | None = None
        self.destination_input: QLineEdit | None = None
        self.travel_date_input: QDateEdit | None = None
        self.trip_table: QTableWidget | None = None
        self.selected_trip_label: QLabel | None = None
        self.itinerary_list: QListWidget | None = None
        self.carriage_list: QListWidget | None = None
        self.carriage_panel_title: QLabel | None = None
        self.selected_seat_label: QLabel | None = None
        self.full_name_input: QLineEdit | None = None
        self.id_number_input: QLineEdit | None = None
        self.phone_input: QLineEdit | None = None
        self.booking_summary_label: QLabel | None = None
        self.booking_total_label: QLabel | None = None
        
        self.radio_forward: QRadioButton | None = None
        self.radio_backward: QRadioButton | None = None

        role_label = "Khách hàng"
        if self.current_user["role"] == "admin":
            role_label = "Quản trị viên"
        elif self.current_user["role"] == "staff":
            role_label = "Nhân viên"

        self.setWindowTitle(f"Hệ thống vé tàu - [{role_label}]")
        self.resize(1480, 920)
        self.setStyleSheet(APP_STYLESHEET)

        central = QWidget()
        root_layout = QVBoxLayout(central)
        self.setCentralWidget(central)

        header_text = f"Xin chào, {self.current_user['full_name']} ({role_label})"
        header = QLabel(header_text)
        header.setStyleSheet("font-size: 22px; font-weight: 800; color: #12344d; padding: 5px;")
        root_layout.addWidget(header)

        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs)

        role = self.current_user["role"]
        
        # Role-based Tab logic
        if role == "admin":
            self.tabs.addTab(self._build_dashboard_tab(), "Thống kê (Reports)")
            self.tabs.addTab(self._build_booking_tab(), "Nghiệp vụ Bán vé")
            self.tabs.addTab(self._build_ticket_tab(), "Quản lý vé & Hoàn tiền")
            self.tabs.addTab(self._build_schedule_tab(), "Điều hành Lịch trình")
            self.tabs.addTab(self._build_trip_planner_tab(), "Lập hành trình")
            self.tabs.addTab(self._build_catalog_tab(), "Quản trị Tàu & Ga")
            self.tabs.addTab(self._build_staff_tab(), "Quản trị Nhân viên")
            self.tabs.addTab(self._build_audit_tab(), "Nhật ký hệ thống")
        elif role == "staff":
            self.tabs.addTab(self._build_dashboard_tab(), "Tổng quan")
            self.tabs.addTab(self._build_booking_tab(), "Bán vé tại quầy")
            self.tabs.addTab(self._build_ticket_tab(), "Xử lý Vé & Soát vé")
            self.tabs.addTab(self._build_schedule_tab(), "Xem lịch trình")
        else: # customer
            self.tabs.addTab(self._build_booking_tab(), "Đặt vé trực tuyến")
            self.tabs.addTab(self._build_my_tickets_tab(), "Vé của tôi")
            self.tabs.addTab(self._build_profile_tab(), "Hồ sơ cá nhân")
            header.setText("HỆ THỐNG ĐẶT VÉ TRỰC TUYẾN")
            header.setStyleSheet("font-size: 26px; font-weight: 900; color: #0d6e8a; padding: 10px;")

        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Initialize data and inputs BEFORE showing
        self.catalog = self.service.get_catalog()
        self.template_rows = self.service.get_train_templates()
        self.populate_catalog_inputs()
        self.refresh_all()

    def _get_role_label(self, role: str) -> str:
        mapping = {
            "admin": "Quản trị viên",
            "staff": "Nhân viên",
            "captain": "Trưởng tàu",
            "customer": "Khách hàng"
        }
        return mapping.get(role, role)

    def _get_role_internal(self, label: str) -> str:
        mapping = {
            "Quản trị viên": "admin",
            "Nhân viên": "staff",
            "Trưởng tàu": "captain",
            "Khách hàng": "customer"
        }
        return mapping.get(label, "customer")

    def _build_dashboard_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        stats_layout = QGridLayout()
        self.stat_labels = {}
        cards = [
            ("tickets_sold", "Vé đã bán"),
            ("revenue", "Doanh thu"),
            ("active_trips", "Chuyến đang bán"),
            ("occupancy_rate", "Tỉ lệ lấp đầy"),
        ]
        for index, (key, title) in enumerate(cards):
            box = QGroupBox(title)
            box_layout = QVBoxLayout(box)
            value_label = QLabel("0")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value_label.setStyleSheet("font-size: 28px; font-weight: 800;")
            box_layout.addWidget(value_label)
            self.stat_labels[key] = value_label
            stats_layout.addWidget(box, index // 2, index % 2)
        layout.addLayout(stats_layout)

        charts_layout = QGridLayout()
        revenue_group = QGroupBox("Doanh thu theo tháng")
        revenue_layout = QVBoxLayout(revenue_group)
        self.revenue_chart_placeholder = QLabel("Chưa có dữ liệu biểu đồ doanh thu")
        self.revenue_chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        revenue_layout.addWidget(self.revenue_chart_placeholder)
        occupancy_group = QGroupBox("Tỷ lệ lấp đầy theo chuyến")
        occupancy_layout = QVBoxLayout(occupancy_group)
        self.occupancy_chart_placeholder = QLabel("Chưa có dữ liệu biểu đồ lấp đầy")
        self.occupancy_chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        occupancy_layout.addWidget(self.occupancy_chart_placeholder)
        charts_layout.addWidget(revenue_group, 0, 0)
        charts_layout.addWidget(occupancy_group, 0, 1)
        layout.addLayout(charts_layout)
        layout.addStretch()
        return tab

    def _build_booking_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # 1. Top Search Bar
        search_group = QGroupBox("1. Tìm kiếm chuyến tàu")
        search_group.setStyleSheet("QGroupBox { font-weight: 800; color: #0d6e8a; }")
        search_main_layout = QVBoxLayout(search_group)
        
        search_inputs_h = QHBoxLayout()
        self.origin_input = QLineEdit()
        self.origin_input.setPlaceholderText("Nhập ga đi (VD: Hà Nội)...")
        self.destination_input = QLineEdit()
        self.destination_input.setPlaceholderText("Nhập ga đến (VD: Sài Gòn)...")
        
        # Setup Completers
        self.station_completer = QCompleter([])
        self.station_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.station_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.station_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        
        # Style the popup list
        completer_popup = self.station_completer.popup()
        if completer_popup:
            completer_popup.setStyleSheet(
                "QAbstractItemView { background-color: #ffffff; border: 1px solid #0d6e8a; "
                "selection-background-color: #0d6e8a; selection-color: #ffffff; outline: none; padding: 5px; }"
                "QAbstractItemView::item { padding: 8px; color: #1e293b; }"
            )
        
        self.origin_input.setCompleter(self.station_completer)
        self.destination_input.setCompleter(self.station_completer)

        self.travel_date_input = QDateEdit(QDate.currentDate())
        self.travel_date_input.setCalendarPopup(True)
        self.travel_date_input.setFixedWidth(150)
        
        search_button = QPushButton("TÌM CHUYẾN")
        search_button.setFixedWidth(140)
        search_button.setObjectName("successButton")
        search_button.clicked.connect(self.search_trips)
        
        search_inputs_h.addWidget(QLabel("Từ:"))
        search_inputs_h.addWidget(self.origin_input)
        search_inputs_h.addWidget(QLabel("Đến:"))
        search_inputs_h.addWidget(self.destination_input)
        search_inputs_h.addWidget(QLabel("Ngày đi:"))
        search_inputs_h.addWidget(self.travel_date_input)
        search_inputs_h.addWidget(search_button)
        search_main_layout.addLayout(search_inputs_h)

        # Quick Select Row
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QLabel("Chọn nhanh ga phổ biến:"))
        major_stations = ["Hà Nội", "Sài Gòn", "Đà Nẵng", "Vinh", "Huế", "Nha Trang", "Hải Phòng"]
        for city in major_stations:
            btn = QPushButton(city)
            btn.setFlat(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { color: #0d6e8a; font-weight: bold; border: 1px solid #bae6fd; "
                "border-radius: 4px; padding: 2px 10px; background: #f0f9ff; }"
                "QPushButton:hover { background: #e0f2fe; border-color: #0d6e8a; }"
            )
            # Connect to helper
            btn.clicked.connect(lambda checked=False, c=city: self._on_quick_station_select(c))
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        search_main_layout.addLayout(quick_layout)

        layout.addWidget(search_group)

        # 2. Main Content Area (Split Left/Right)
        main_content = QHBoxLayout()
        main_content.setSpacing(15)

        # Left Column: Trip Results
        left_panel = QVBoxLayout()
        results_group = QGroupBox("2. Danh sách chuyến")
        results_group.setStyleSheet("QGroupBox { font-weight: 800; color: #0d6e8a; }")
        results_layout = QVBoxLayout(results_group)
        
        self.trip_table = self._create_table(
            ["Mã", "Tàu", "Ga đi", "Ga đến", "Giờ đi", "Giờ đến", "Giá vé"]
        )
        self.trip_table.itemSelectionChanged.connect(self._on_trip_selected)
        results_layout.addWidget(self.trip_table)
        
        itinerary_box = QGroupBox("Hành trình")
        itinerary_box_layout = QVBoxLayout(itinerary_box)
        self.itinerary_list = QListWidget()
        self.itinerary_list.setMaximumHeight(120)
        itinerary_box_layout.addWidget(self.itinerary_list)
        results_layout.addWidget(itinerary_box)
        
        left_panel.addWidget(results_group)
        main_content.addLayout(left_panel, 2) # Width weight 2

        # Right Column: Seat Selection (The big focus)
        right_panel = QVBoxLayout()
        
        self.selected_trip_label = QLabel("Vui lòng chọn chuyến tàu")
        self.selected_trip_label.setStyleSheet(
            "padding: 12px; background: #e0f2fe; border: 1px solid #7dd3fc; border-radius: 12px;"
            "font-size: 16px; font-weight: 700; color: #0369a1;"
        )
        right_panel.addWidget(self.selected_trip_label)

        seat_selection_group = QGroupBox("3. Sơ đồ chỗ ngồi")
        seat_selection_group.setStyleSheet("QGroupBox { font-weight: 800; color: #0d6e8a; }")
        seat_selection_layout = QVBoxLayout(seat_selection_group)

        # Legend and Selection Hint
        top_info = QHBoxLayout()
        booking_legend = QLabel(
            "<span style='color:#22c55e;'>●</span> Trống &nbsp;&nbsp; "
            "<span style='color:#94a3b8;'>●</span> Đã đặt &nbsp;&nbsp; "
            "<span style='color:#ec4899;'>●</span> Đang chọn"
        )
        self.selected_seat_label = QLabel("Chưa chọn ghế")
        self.selected_seat_label.setStyleSheet("font-weight: 700; color: #ec4899;")
        top_info.addWidget(booking_legend)
        top_info.addStretch()
        top_info.addWidget(self.selected_seat_label)
        seat_selection_layout.addLayout(top_info)

        # Carriage and Seats split
        carriage_seats_h = QHBoxLayout()
        
        # Carriage List (Horizontal or narrow vertical)
        carriage_box = QVBoxLayout()
        carriage_box.addWidget(QLabel("Toa tàu:"))
        self.carriage_list = QListWidget()
        self.carriage_list.setFixedWidth(160)
        self.carriage_list.setStyleSheet(
            "QListWidget { border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fafc; }"
            "QListWidget::item { padding: 12px; border-bottom: 1px solid #f1f5f9; }"
            "QListWidget::item:selected { background: #0d6e8a; color: white; border-radius: 4px; }"
        )
        self.carriage_list.currentRowChanged.connect(self._on_carriage_selected)
        carriage_box.addWidget(self.carriage_list)
        carriage_seats_h.addLayout(carriage_box)

        # Seat Grid Scroll Area
        seat_area_v = QVBoxLayout()
        self.carriage_panel_title = QLabel("Toa chưa chọn")
        self.carriage_panel_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #1e293b;")
        seat_area_v.addWidget(self.carriage_panel_title)
        
        seat_scroll = QScrollArea()
        seat_scroll.setWidgetResizable(True)
        seat_scroll.setStyleSheet("QScrollArea { border: 1px solid #e2e8f0; border-radius: 10px; background: #ffffff; }")
        seat_canvas = QWidget()
        self.seat_grid = QGridLayout()
        self.seat_grid.setSpacing(10)
        seat_canvas.setLayout(self.seat_grid)
        seat_scroll.setWidget(seat_canvas)
        seat_area_v.addWidget(seat_scroll)
        
        carriage_seats_h.addLayout(seat_area_v, 1)
        seat_selection_layout.addLayout(carriage_seats_h)
        
        right_panel.addWidget(seat_selection_group)
        main_content.addLayout(right_panel, 5) # Much wider for seats

        layout.addLayout(main_content)

        # 3. Bottom Passenger Info & Summary
        bottom_area = QHBoxLayout()
        bottom_area.setSpacing(15)

        passenger_group = QGroupBox("4. Thông tin hành khách")
        passenger_group.setStyleSheet("QGroupBox { font-weight: 800; color: #0d6e8a; }")
        passenger_form = QFormLayout(passenger_group)
        self.full_name_input = QLineEdit()
        self.id_number_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.full_name_input.textChanged.connect(self._refresh_booking_summary)
        passenger_form.addRow("Họ tên:", self.full_name_input)
        passenger_form.addRow("CCCD:", self.id_number_input)
        passenger_form.addRow("SĐT:", self.phone_input)
        bottom_area.addWidget(passenger_group, 3)

        summary_group = QGroupBox("5. Thanh toán")
        summary_group.setStyleSheet("QGroupBox { font-weight: 800; color: #0d6e8a; }")
        summary_layout = QVBoxLayout(summary_group)
        
        summary_h = QHBoxLayout()
        self.booking_summary_label = QLabel("Vui lòng chọn ghế")
        self.booking_summary_label.setStyleSheet("color: #64748b; font-size: 14px;")
        self.booking_total_label = QLabel("0 VND")
        self.booking_total_label.setStyleSheet("font-size: 24px; font-weight: 900; color: #f97316;")
        summary_h.addWidget(self.booking_summary_label)
        summary_h.addStretch()
        summary_h.addWidget(QLabel("Tổng tiền:"))
        summary_h.addWidget(self.booking_total_label)
        summary_layout.addLayout(summary_h)

        book_button = QPushButton("XÁC NHẬN ĐẶV VÉ")
        book_button.setCursor(Qt.CursorShape.PointingHandCursor)
        book_button.setStyleSheet(
            "QPushButton { background: #0d6e8a; color: white; border-radius: 8px; padding: 12px; font-size: 16px; font-weight: 800; }"
            "QPushButton:hover { background: #0a566e; }"
        )
        book_button.clicked.connect(self.create_booking)
        summary_layout.addWidget(book_button)
        
        bottom_area.addWidget(summary_group, 2)
        layout.addLayout(bottom_area)

        return tab

    def _build_my_tickets_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        label = QLabel("Danh sách vé bạn đã mua. Bạn có thể xem chi tiết hoặc yêu cầu hủy vé.")
        label.setStyleSheet("color: #64748b; margin-bottom: 10px;")
        layout.addWidget(label)

        self.my_ticket_table = self._create_table(
            ["Mã vé", "Chuyến", "Ga đi", "Ga đến", "Chỗ", "Giá", "Trạng thái", "Ngày đặt"]
        )
        layout.addWidget(self.my_ticket_table)
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Yêu cầu hủy vé")
        cancel_btn.setObjectName("dangerButton")
        cancel_btn.clicked.connect(self.cancel_selected_ticket)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        return tab

    def _build_profile_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        group = QGroupBox("Thông tin cá nhân")
        form = QFormLayout(group)
        self.profile_name = QLineEdit(self.current_user["full_name"])
        self.profile_user = QLineEdit(self.current_user["username"])
        self.profile_user.setEnabled(False)
        self.profile_role = QLineEdit(self._get_role_label(self.current_user["role"]))
        self.profile_role.setEnabled(False)
        
        save_btn = QPushButton("Cập nhật thông tin")
        save_btn.setFixedWidth(200)
        
        form.addRow("Họ và tên:", self.profile_name)
        form.addRow("Tên đăng nhập:", self.profile_user)
        form.addRow("Vai trò:", self.profile_role)
        form.addRow("", save_btn)
        
        layout.addWidget(group)
        layout.addStretch()
        return tab

    def _build_ticket_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        toolbar = QHBoxLayout()
        self.ticket_query_input = QLineEdit()
        self.ticket_query_input.setPlaceholderText("Nhập mã vé, CCCD, SĐT hoặc tên hành khách")
        search_button = QPushButton("Tìm kiếm")
        search_button.clicked.connect(self.refresh_tickets)
        
        print_button = QPushButton("In vé (Print)")
        print_button.setStyleSheet("background: #6366f1;")
        print_button.clicked.connect(self.print_selected_ticket)
        
        validate_button = QPushButton("Soát vé (Validate)")
        validate_button.setStyleSheet("background: #059669;")
        validate_button.clicked.connect(self.validate_selected_ticket)
        
        cancel_button = QPushButton("Hoàn tiền / Hủy vé")
        cancel_button.setObjectName("dangerButton")
        cancel_button.clicked.connect(self.cancel_selected_ticket)
        
        toolbar.addWidget(self.ticket_query_input)
        toolbar.addWidget(search_button)
        toolbar.addWidget(print_button)
        toolbar.addWidget(validate_button)
        toolbar.addWidget(cancel_button)
        layout.addLayout(toolbar)

        self.ticket_table = self._create_table(
            ["Mã vé", "Hành khách", "Người đặt", "CCCD", "SĐT", "Ga lên", "Ga xuống", "Chỗ", "Giá", "Trạng thái", "Đặt lúc"]
        )
        layout.addWidget(self.ticket_table)
        return tab

    def _build_schedule_tab(self) -> QWidget:
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # BÊN TRÁI: DANH SÁCH CHUYẾN TÀU (Card-like container)
        left_card = QFrame()
        left_card.setStyleSheet("QFrame { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; }")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(12)
        
        # Tiêu đề bảng trái
        title_left = QLabel("DANH SÁCH LỊCH TRÌNH")
        title_left.setStyleSheet("font-size: 16px; font-weight: 800; color: #0d6e8a; border: none;")
        left_layout.addWidget(title_left)

        # Toolbar bảng trái
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Lọc theo ngày:"))
        self.schedule_date_filter = QDateEdit(QDate.currentDate())
        self.schedule_date_filter.setCalendarPopup(True)
        self.schedule_date_filter.setFixedWidth(120)
        self.schedule_date_filter.dateChanged.connect(self.refresh_schedules)
        toolbar.addWidget(self.schedule_date_filter)
        
        refresh_btn = QPushButton("🔄 Làm mới")
        refresh_btn.setFixedWidth(100)
        refresh_btn.setStyleSheet("background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1;")
        refresh_btn.clicked.connect(self.refresh_schedules)
        toolbar.addWidget(refresh_btn)
        
        cancel_trip_button = QPushButton("🚫 Hủy chuyến")
        cancel_trip_button.setObjectName("dangerButton")
        cancel_trip_button.clicked.connect(self.cancel_selected_trip_manual)
        
        toolbar.addStretch()
        toolbar.addWidget(cancel_trip_button)
        left_layout.addLayout(toolbar)

        self.schedule_table = self._create_table(
            ["Mã chuyến", "Tàu", "Điểm đầu", "Điểm cuối", "Ngày", "Giờ đi", "Giờ đến", "Trạng thái", "Toa", "Ghế trống"]
        )
        self.schedule_table.itemSelectionChanged.connect(self._on_schedule_trip_selected)
        left_layout.addWidget(self.schedule_table)
        
        layout.addWidget(left_card, 3)

        # BÊN PHẢI: CHI TIẾT HÀNH TRÌNH
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)

        # 1. Info Card (Trip Header)
        self.info_header_card = QFrame()
        self.info_header_card.setStyleSheet("QFrame { background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #12344d, stop:1 #0d6e8a); border-radius: 12px; }")
        self.info_header_card.setMinimumHeight(150)
        info_header_layout = QVBoxLayout(self.info_header_card)
        
        self.schedule_trip_label = QLabel("Vui lòng chọn một hành trình từ danh sách bên trái để xem chi tiết chi tiết.")
        self.schedule_trip_label.setWordWrap(True)
        self.schedule_trip_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.schedule_trip_label.setStyleSheet("color: #ffffff; border: none; font-size: 15px;")
        info_header_layout.addWidget(self.schedule_trip_label)
        right_panel.addWidget(self.info_header_card)

        # 2. Itinerary Table Card
        stops_card = QFrame()
        stops_card.setStyleSheet("QFrame { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; }")
        stops_layout = QVBoxLayout(stops_card)
        stops_layout.setContentsMargins(15, 15, 15, 15)
        
        title_right = QLabel("CHI TIẾT LỘ TRÌNH GA DỪNG")
        title_right.setStyleSheet("font-size: 14px; font-weight: 800; color: #12344d; border: none;")
        stops_layout.addWidget(title_right)

        self.schedule_stop_table = self._create_table(
            ["STT", "Vai trò", "Ga", "Mã", "Đến", "Đi", "Dừng"]
        )
        self.schedule_stop_table.itemSelectionChanged.connect(self._on_schedule_stop_selected)
        stops_layout.addWidget(self.schedule_stop_table)
        
        hint_label = QLabel("💡 <i>Thông tin này được cập nhật theo thời gian thực từ hệ thống vận hành.</i>")
        hint_label.setStyleSheet("color: #94a3b8; font-size: 12px; border: none;")
        stops_layout.addWidget(hint_label)

        right_panel.addWidget(stops_card)
        layout.addLayout(right_panel, 2)
        
        return tab

    def _build_catalog_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        sub_tabs = QTabWidget()
        sub_tabs.addTab(self._build_catalog_station_tab(), "Quản lý Ga")
        sub_tabs.addTab(self._build_catalog_train_tab(), "Quản lý Tàu")
        sub_tabs.addTab(self._build_catalog_carriage_tab(), "Quản lý Toa")
        sub_tabs.addTab(self._build_catalog_template_tab(), "Mẫu đoàn tàu")
        
        layout.addWidget(sub_tabs)
        return tab

    def _build_catalog_station_tab(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        
        # Form bên trái
        left_panel = QVBoxLayout()
        station_group = QGroupBox("Thêm ga mới")
        station_layout = QVBoxLayout(station_group)
        station_form = QFormLayout()
        self.station_code_input = QLineEdit()
        self.station_name_input = QLineEdit()
        self.station_city_input = QLineEdit()
        station_form.addRow("Mã ga:", self.station_code_input)
        station_form.addRow("Tên ga:", self.station_name_input)
        station_form.addRow("Thành phố:", self.station_city_input)
        
        btn_layout = QVBoxLayout()
        save_btn = QPushButton("Lưu ga")
        save_btn.setObjectName("successButton")
        save_btn.clicked.connect(self.add_station)
        delete_btn = QPushButton("Xóa ga chọn")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self.delete_station)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(delete_btn)
        
        station_layout.addLayout(station_form)
        station_layout.addLayout(btn_layout)
        left_panel.addWidget(station_group)
        left_panel.addStretch()
        
        # Bảng bên phải
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Danh sách các ga trên hệ thống"))
        self.station_table = self._create_table(["Mã ga", "Tên ga", "Thành phố"])
        right_panel.addWidget(self.station_table)
        
        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 2)
        return page

    def _build_catalog_train_tab(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        
        # Form bên trái
        left_panel = QVBoxLayout()
        train_group = QGroupBox("Thêm tàu mới")
        train_layout = QVBoxLayout(train_group)
        train_form = QFormLayout()
        self.train_code_input = QLineEdit()
        self.train_name_input = QLineEdit()
        train_form.addRow("Mã tàu:", self.train_code_input)
        train_form.addRow("Tên tàu:", self.train_name_input)
        
        btn_layout = QVBoxLayout()
        save_btn = QPushButton("Lưu tàu")
        save_btn.setObjectName("successButton")
        save_btn.clicked.connect(self.add_train)
        delete_btn = QPushButton("Xóa tàu chọn")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self.delete_train)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(delete_btn)
        
        train_layout.addLayout(train_form)
        train_layout.addLayout(btn_layout)
        left_panel.addWidget(train_group)
        left_panel.addStretch()
        
        # Bảng bên phải
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Danh sách các đầu máy/đoàn tàu"))
        self.train_table = self._create_table(["Mã tàu", "Tên tàu"])
        right_panel.addWidget(self.train_table)
        
        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 2)
        return page

    def _build_catalog_carriage_tab(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        
        # Form bên trái
        left_panel = QVBoxLayout()
        carriage_group = QGroupBox("Thêm toa mới")
        carriage_layout = QVBoxLayout(carriage_group)
        carriage_form = QFormLayout()
        self.new_carriage_code_input = QLineEdit()
        self.new_carriage_type_input = QLineEdit("Ghế mềm")
        self.new_carriage_count_input = QLineEdit("12")
        carriage_form.addRow("Mã toa:", self.new_carriage_code_input)
        carriage_form.addRow("Loại ghế:", self.new_carriage_type_input)
        carriage_form.addRow("Số ghế:", self.new_carriage_count_input)
        
        btn_layout = QVBoxLayout()
        save_btn = QPushButton("Lưu toa")
        save_btn.setObjectName("successButton")
        save_btn.clicked.connect(self.add_carriage)
        delete_btn = QPushButton("Xóa toa chọn")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self.delete_carriage)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(delete_btn)
        
        carriage_layout.addLayout(carriage_form)
        carriage_layout.addLayout(btn_layout)
        left_panel.addWidget(carriage_group)
        left_panel.addStretch()
        
        # Bảng bên phải
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Danh sách các toa tàu mẫu"))
        self.carriage_table_catalog = self._create_table(["Mã toa", "Loại ghế", "Số ghế"])
        right_panel.addWidget(self.carriage_table_catalog)
        
        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 2)
        return page

    def _build_catalog_template_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        
        template_group = QGroupBox("Ghép mẫu đoàn tàu")
        template_layout = QGridLayout(template_group)
        self.template_name_input = QLineEdit()
        self.template_description_input = QPlainTextEdit()
        self.template_description_input.setMaximumHeight(80)
        self.template_carriage_combo = QComboBox()
        self.template_carriage_list = QListWidget()
        self.template_carriage_list.setMinimumHeight(150)
        self.template_list = QListWidget()
        self.template_list.setMinimumHeight(200)
        self.template_list.currentRowChanged.connect(self._on_template_selected)
        
        add_template_carriage_button = QPushButton("Thêm toa vào mẫu")
        add_template_carriage_button.clicked.connect(self.add_template_carriage)
        remove_template_carriage_button = QPushButton("Bỏ toa đã chọn")
        remove_template_carriage_button.setObjectName("dangerButton")
        remove_template_carriage_button.clicked.connect(self.remove_template_carriage)
        save_template_button = QPushButton("Lưu mẫu đoàn tàu")
        save_template_button.setObjectName("successButton")
        save_template_button.clicked.connect(self.create_template)
        delete_template_button = QPushButton("Xóa mẫu đã chọn")
        delete_template_button.setObjectName("dangerButton")
        delete_template_button.clicked.connect(self.delete_template)
        
        template_layout.addWidget(QLabel("Tên mẫu:"), 0, 0)
        template_layout.addWidget(self.template_name_input, 0, 1)
        template_layout.addWidget(QLabel("Mô tả:"), 0, 2)
        template_layout.addWidget(self.template_description_input, 0, 3)
        
        template_layout.addWidget(QLabel("Chọn toa:"), 1, 0)
        template_layout.addWidget(self.template_carriage_combo, 1, 1)
        template_layout.addWidget(add_template_carriage_button, 1, 2)
        template_layout.addWidget(remove_template_carriage_button, 1, 3)
        
        template_layout.addWidget(QLabel("Cấu tạo toa trong mẫu:"), 2, 0)
        template_layout.addWidget(self.template_carriage_list, 2, 1, 1, 3)
        
        btn_box = QHBoxLayout()
        btn_box.addWidget(save_template_button)
        btn_box.addWidget(delete_template_button)
        template_layout.addLayout(btn_box, 3, 1, 1, 3)
        
        template_layout.addWidget(QLabel("Danh sách các mẫu đã lưu:"), 4, 0)
        template_layout.addWidget(self.template_list, 4, 1, 1, 3)
        
        layout.addWidget(template_group)
        return page

    def _build_staff_tab(self) -> QWidget:
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Danh sách nhân viên (Bên trái)
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Danh sách người dùng & Nhân viên"))
        self.staff_table = self._create_table(["ID", "Tên đăng nhập", "Họ tên", "Vai trò"])
        left_panel.addWidget(self.staff_table)
        layout.addLayout(left_panel, 3)
        
        # Form chỉnh sửa (Bên phải)
        right_panel = QVBoxLayout()
        form_group = QGroupBox("Thông tin người dùng")
        form = QFormLayout(form_group)
        
        self.staff_username_input = QLineEdit()
        self.staff_fullname_input = QLineEdit()
        self.staff_password_input = QLineEdit()
        self.staff_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.staff_role_combo = QComboBox()
        self.staff_role_combo.addItems([
            "Quản trị viên", "Nhân viên", "Trưởng tàu", "Khách hàng"
        ])
        
        form.addRow("Tên đăng nhập:", self.staff_username_input)
        form.addRow("Họ và tên:", self.staff_fullname_input)
        form.addRow("Mật khẩu mới:", self.staff_password_input)
        form.addRow("Vai trò:", self.staff_role_combo)
        
        btn_layout = QVBoxLayout()
        add_btn = QPushButton("Thêm người dùng mới")
        add_btn.clicked.connect(self.add_user)
        save_btn = QPushButton("Lưu thay đổi")
        save_btn.setObjectName("successButton")
        save_btn.clicked.connect(self.update_user)
        delete_btn = QPushButton("Xóa người dùng")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self.delete_user)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(delete_btn)
        
        right_panel.addWidget(form_group)
        right_panel.addLayout(btn_layout)
        right_panel.addStretch()
        layout.addLayout(right_panel, 2)
        
        self.staff_table.itemSelectionChanged.connect(self._on_staff_selected)

        return tab

    def _build_audit_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Thanh công cụ lọc hiện đại
        filter_group = QGroupBox("Bộ lọc nhật ký")
        toolbar = QHBoxLayout(filter_group)
        toolbar.setSpacing(15)

        v_layout_1 = QVBoxLayout()
        v_layout_1.addWidget(QLabel("Phân loại nghiệp vụ:"))
        self.audit_category_filter = QComboBox()
        self.audit_category_filter.addItems([
            "--- Tất cả nghiệp vụ ---",
            "Nghiệp vụ Bán vé",
            "Điều hành Lịch trình",
            "Lập hành trình mới",
            "Quản trị Danh mục",
            "Quản trị Người dùng"
        ])
        self.audit_category_filter.currentIndexChanged.connect(self.refresh_audit_logs)
        v_layout_1.addWidget(self.audit_category_filter)
        
        v_layout_2 = QVBoxLayout()
        v_layout_2.addWidget(QLabel("Tìm kiếm từ khóa:"))
        self.audit_query_input = QLineEdit()
        self.audit_query_input.setPlaceholderText("Mã vé, tên người dùng, thao tác...")
        self.audit_query_input.textChanged.connect(self.refresh_audit_logs)
        v_layout_2.addWidget(self.audit_query_input)

        toolbar.addLayout(v_layout_1, 1)
        toolbar.addLayout(v_layout_2, 2)
        
        btn_refresh = QPushButton("🔄 Làm mới")
        btn_refresh.setFixedWidth(120)
        btn_refresh.clicked.connect(self.refresh_audit_logs)
        toolbar.addWidget(btn_refresh, 0, Qt.AlignmentFlag.AlignBottom)
        
        layout.addWidget(filter_group)

        # Bảng nhật ký
        self.audit_table = self._create_table(
            ["Thời gian", "Người dùng", "Thao tác", "Đối tượng", "Mã", "Nội dung chi tiết"]
        )
        # Tùy chỉnh độ rộng cột cho nhật ký
        header = self.audit_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.audit_table)
        
        hint = QLabel("💡 <i>Nhật ký hệ thống ghi lại mọi thay đổi quan trọng liên quan đến dữ liệu và vận hành.</i>")
        hint.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(hint)
        
        return tab

    def _build_trip_planner_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Thanh tiến trình Wizard
        self.planner_progress = QProgressBar()
        self.planner_progress.setRange(1, 4)
        self.planner_progress.setValue(1)
        self.planner_progress.setFormat("Bước %v/4: %p")
        self.planner_progress.setStyleSheet("QProgressBar { height: 25px; text-align: center; font-weight: bold; }")
        layout.addWidget(self.planner_progress)

        # Container StackedWidget cho 4 bước
        self.planner_stack = QStackedWidget()
        
        # BƯỚC 1: ĐỊNH HÌNH KHUNG XƯƠNG
        self.step1_widget = self._build_planner_step1()
        self.planner_stack.addWidget(self.step1_widget)
        
        # BƯỚC 2: LỊCH TRÌNH & GA ĐỖ
        self.step2_widget = self._build_planner_step2()
        self.planner_stack.addWidget(self.step2_widget)
        
        # BƯỚC 3: LẮP RÁP TOA XE
        self.step3_widget = self._build_planner_step3()
        self.planner_stack.addWidget(self.step3_widget)
        
        # BƯỚC 4: TỔNG DUYỆT
        self.step4_widget = self._build_planner_step4()
        self.planner_stack.addWidget(self.step4_widget)
        
        layout.addWidget(self.planner_stack)
        return tab

    def auto_generate_trip_code(self) -> None:
        import random
        import string
        from datetime import datetime
        
        prefix = "TRP"
        date_str = datetime.now().strftime("%y%m%d")
        
        while True:
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            code = f"{prefix}-{date_str}-{suffix}"
            
            # Kiểm tra xem mã đã tồn tại trong database chưa
            if not any(t["trip_code"] == code for t in self.schedule_rows):
                if self.plan_trip_code is not None:
                    self.plan_trip_code.setText(code)
                break

    def _build_planner_step1(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 1. Khối Thông tin Chuyến tàu
        info_group = QGroupBox("1. Thông tin Chuyến tàu")
        info_layout = QGridLayout(info_group)
        
        self.plan_trip_code = QLineEdit()
        self.plan_trip_code.setPlaceholderText("VD: SE1, NA1...")
        auto_gen_btn = QPushButton("Tự động tạo")
        auto_gen_btn.clicked.connect(self.auto_generate_trip_code)
        
        self.plan_train_type = QComboBox()
        self.plan_train_type.addItems(["Tàu nhanh SE", "Tàu địa phương", "Tàu du lịch"])
        
        self.plan_departure_date = QDateEdit(QDate.currentDate())
        self.plan_departure_date.setCalendarPopup(True)
        
        self.plan_end_date = QDateEdit(QDate.currentDate())
        self.plan_end_date.setCalendarPopup(True)
        self.plan_end_date.setEnabled(False)
        
        self.is_recurring_check = QCheckBox("Lập lịch định kỳ (nhiều ngày)")
        self.is_recurring_check.toggled.connect(lambda checked: self.plan_end_date.setEnabled(checked) if self.plan_end_date else None)

        self.plan_train_combo = QComboBox()
        
        self.plan_base_price_input = QLineEdit("400000")
        self.plan_base_price_input.setPlaceholderText("VD: 400000")
        
        info_layout.addWidget(QLabel("Mã chuyến đi:"), 0, 0)
        info_layout.addWidget(self.plan_trip_code, 0, 1)
        info_layout.addWidget(auto_gen_btn, 0, 2)
        info_layout.addWidget(QLabel("Phân loại tàu:"), 1, 0)
        info_layout.addWidget(self.plan_train_type, 1, 1, 1, 2)
        info_layout.addWidget(QLabel("Ngày xuất phát:"), 2, 0)
        info_layout.addWidget(self.plan_departure_date, 2, 1, 1, 2)
        info_layout.addWidget(QLabel("Đầu máy (Train):"), 3, 0)
        info_layout.addWidget(self.plan_train_combo, 3, 1, 1, 2)
        info_layout.addWidget(QLabel("Giá vé cơ sở (VNĐ):"), 4, 0)
        info_layout.addWidget(self.plan_base_price_input, 4, 1, 1, 2)
        
        # 2. Khối Chặng đường
        route_group = QGroupBox("2. Tuyến đường sắt & Hướng tuyến")
        route_layout = QGridLayout(route_group)
        
        self.plan_route_base = QComboBox()
        # Sẽ được load từ catalog.routes
        self.plan_route_base.currentIndexChanged.connect(self._on_planner_route_changed)
        
        dir_layout = QHBoxLayout()
        self.radio_forward = QRadioButton("Lượt đi (Bắc -> Nam)")
        self.radio_backward = QRadioButton("Lượt về (Nam -> Bắc)")
        self.radio_forward.setChecked(True)
        dir_group = QButtonGroup(page)
        dir_group.addButton(self.radio_forward)
        dir_group.addButton(self.radio_backward)
        dir_layout.addWidget(self.radio_forward)
        dir_layout.addWidget(self.radio_backward)
        
        self.plan_origin_combo = QComboBox()
        self.plan_destination_combo = QComboBox()
        self.plan_departure_input = QTimeEdit(QTime(22, 0))
        self.plan_departure_input.setDisplayFormat("HH:mm")
        
        # Connect logic lọc ga
        self.radio_forward.toggled.connect(self._on_planner_route_changed)
        self.radio_backward.toggled.connect(self._on_planner_route_changed)
        self.plan_origin_combo.currentIndexChanged.connect(self._on_planner_origin_changed)

        route_layout.addWidget(QLabel("Tuyến đường gốc:"), 0, 0)
        route_layout.addWidget(self.plan_route_base, 0, 1)
        route_layout.addWidget(QLabel("Hướng tuyến:"), 1, 0)
        route_layout.addLayout(dir_layout, 1, 1)
        route_layout.addWidget(QLabel("Ga khởi hành:"), 2, 0)
        route_layout.addWidget(self.plan_origin_combo, 2, 1)
        route_layout.addWidget(QLabel("Ga kết thúc:"), 3, 0)
        route_layout.addWidget(self.plan_destination_combo, 3, 1)
        route_layout.addWidget(QLabel("Giờ xuất phát (Ga đầu):"), 4, 0)
        route_layout.addWidget(self.plan_departure_input, 4, 1)

        # 3. Khối Nhân sự & Mẫu
        staff_group = QGroupBox("3. Thiết lập khác")
        staff_layout = QFormLayout(staff_group)
        
        self.plan_template_combo = QComboBox()
        apply_tpl_btn = QPushButton("Áp dụng Mẫu")
        apply_tpl_btn.clicked.connect(self.apply_trip_template)
        
        tpl_layout = QHBoxLayout()
        tpl_layout.addWidget(self.plan_template_combo)
        tpl_layout.addWidget(apply_tpl_btn)
        
        self.plan_captain_combo = QComboBox()
        self.plan_crew_code = QComboBox()
        self.plan_crew_code.addItems(["Đội 1 (HN)", "Đội 2 (Vinh)", "Đội 3 (SG)"])
        
        staff_layout.addRow("Mẫu đoàn tàu:", tpl_layout)
        staff_layout.addRow("Trưởng tàu:", self.plan_captain_combo)
        staff_layout.addRow("Đội tiếp viên:", self.plan_crew_code)
        
        layout.addWidget(info_group)
        layout.addWidget(route_group)
        layout.addWidget(staff_group)
        
        next_btn = QPushButton("Tiếp theo: Lịch trình & Ga đỗ →")
        next_btn.setMinimumHeight(45)
        next_btn.setObjectName("successButton")
        next_btn.clicked.connect(lambda: self._switch_planner_step(1))
        layout.addWidget(next_btn)
        layout.addStretch()
        return page

    def _build_planner_step2(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Thiết lập chi tiết giờ tàu đến/đi và sân ga tại từng điểm dừng."))
        
        self.plan_timetable_table = QTableWidget(0, 8)
        self.plan_timetable_table.setHorizontalHeaderLabels([
            "Ga dừng", "Đón khách", "Sân ga", "Giờ đến", "Đỗ (phút)", "Giờ đi", "Ngày (+)", "Hành động"
        ])
        layout.addWidget(self.plan_timetable_table)
        
        btn_layout = QHBoxLayout()
        back_btn = QPushButton("← Quay lại")
        back_btn.clicked.connect(lambda: self._switch_planner_step(0))
        next_btn = QPushButton("Tiếp theo: Lắp ráp Toa xe →")
        next_btn.setObjectName("successButton")
        next_btn.clicked.connect(lambda: self._switch_planner_step(2))
        
        btn_layout.addWidget(back_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(next_btn)
        layout.addLayout(btn_layout)
        return page

    def _build_planner_step3(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        
        content = QHBoxLayout()
        # Kho toa xe
        left = QVBoxLayout()
        left.addWidget(QLabel("Kho Toa xe Sẵn sàng"))
        self.plan_avail_carriages = QListWidget()
        left.addWidget(self.plan_avail_carriages)
        add_btn = QPushButton(">> Thêm vào đoàn tàu")
        add_btn.clicked.connect(self._add_carriage_to_comp)
        left.addWidget(add_btn)
        
        # Đoàn tàu
        right = QVBoxLayout()
        right.addWidget(QLabel("Sơ đồ Đoàn tàu thực tế"))
        self.plan_train_composition = QListWidget()
        right.addWidget(self.plan_train_composition)
        remove_btn = QPushButton("<< Loại bỏ khỏi đoàn")
        remove_btn.clicked.connect(self._remove_carriage_from_comp)
        right.addWidget(remove_btn)
        
        content.addLayout(left, 1)
        content.addLayout(right, 1)
        layout.addLayout(content)
        
        btn_layout = QHBoxLayout()
        back_btn = QPushButton("← Quay lại")
        back_btn.clicked.connect(lambda: self._switch_planner_step(1))
        next_btn = QPushButton("Tiếp theo: Tổng duyệt →")
        next_btn.setObjectName("successButton")
        next_btn.clicked.connect(lambda: self._switch_planner_step(3))
        
        btn_layout.addWidget(back_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(next_btn)
        layout.addLayout(btn_layout)
        return page

    def _build_planner_step4(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        
        self.plan_summary = QPlainTextEdit()
        self.plan_summary.setReadOnly(True)
        layout.addWidget(QLabel("Tóm tắt hành trình:"))
        layout.addWidget(self.plan_summary)
        
        btn_layout = QHBoxLayout()
        back_btn = QPushButton("← Quay lại")
        back_btn.clicked.connect(lambda: self._switch_planner_step(2))
        
        draft_btn = QPushButton("Lưu Bản Nháp")
        draft_btn.clicked.connect(self.save_trip_draft)
        
        publish_btn = QPushButton("XUẤT BẢN - PUBLISH")
        publish_btn.setMinimumHeight(50)
        publish_btn.setObjectName("successButton")
        publish_btn.clicked.connect(self.create_trip)
        
        btn_layout.addWidget(back_btn)
        btn_layout.addWidget(draft_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(publish_btn)
        layout.addLayout(btn_layout)
        return page

    def _switch_planner_step(self, index: int) -> None:
        planner_stack = self.planner_stack
        if planner_stack is None:
            return
            
        # Kiểm tra điều kiện trước khi chuyển bước
        current_idx = planner_stack.currentIndex()
        
        # LOGIC CHUYỂN TIẾP
        if index > current_idx:
            if current_idx == 0: # Từ Bước 1 đi tiếp
                if self.plan_trip_code is None or not self.plan_trip_code.text().strip():
                    self._show_warning("Vui lòng nhập mã chuyến đi.")
                    return
                
                origin_id = self.plan_origin_combo.currentData() if self.plan_origin_combo is not None else None
                dest_id = self.plan_destination_combo.currentData() if self.plan_destination_combo is not None else None
                
                if origin_id is None or dest_id is None:
                    self._show_warning("Vui lòng chọn đầy đủ Ga khởi hành và Ga kết thúc ở Bước 1.")
                    return
                    
                # Sinh bảng ga dừng
                if not self._generate_timetable_rows():
                    return 
            
            elif current_idx == 1: # Từ Bước 2 đi tiếp
                if self.plan_timetable_table is None or self.plan_timetable_table.rowCount() < 2:
                    self._show_warning("Lịch trình phải có ít nhất 2 ga.")
                    return
            
            elif current_idx == 2: # Từ Bước 3 đi tiếp
                if self.plan_train_composition is None or self.plan_train_composition.count() == 0:
                    self._show_warning("Vui lòng ghép ít nhất 1 toa xe.")
                    return

        # Thực hiện chuyển bước
        planner_stack.setCurrentIndex(index)
        if self.planner_progress is not None:
            self.planner_progress.setValue(index + 1)
        if index == 3: self._update_planner_summary()

    def _on_planner_route_changed(self) -> None:
        plan_route_base = self.plan_route_base
        if plan_route_base is None:
            return
        route_id = plan_route_base.currentData()
        if route_id is None: return
        
        # Lấy danh sách ga thực tế của tuyến này từ DB
        route_stations = self.service.get_route_stations(route_id)
        if not route_stations:
            if self.plan_origin_combo is not None: self.plan_origin_combo.clear()
            if self.plan_destination_combo is not None: self.plan_destination_combo.clear()
            return

        # Đảo ngược nếu là Lượt về
        if self.radio_backward is not None and self.radio_backward.isChecked():
            route_stations = list(reversed(route_stations))
        
        self.current_planner_route_stations = route_stations # Lưu để dùng cho logic filter ga đến
        
        plan_origin_combo = self.plan_origin_combo
        if plan_origin_combo is not None:
            plan_origin_combo.blockSignals(True)
            plan_origin_combo.clear()
            for rs in route_stations:
                plan_origin_combo.addItem(f"{rs['code']} - {rs['name']}", rs["id"])
            plan_origin_combo.blockSignals(False)
        self._on_planner_origin_changed()

    def _on_planner_origin_changed(self) -> None:
        plan_origin_combo = self.plan_origin_combo
        if plan_origin_combo is None:
            return
        origin_id = plan_origin_combo.currentData()
        if origin_id is None or not self.current_planner_route_stations:
            return
        
        # Tìm vị trí ga khởi hành trong danh sách ga của tuyến
        start_idx = -1
        for i, rs in enumerate(self.current_planner_route_stations):
            if rs["id"] == origin_id:
                start_idx = i
                break
        
        # Ga kết thúc phải nằm SAU ga khởi hành
        plan_destination_combo = self.plan_destination_combo
        if plan_destination_combo is not None:
            plan_destination_combo.clear()
            if start_idx != -1:
                targets = self.current_planner_route_stations[start_idx + 1:]
                for rs in targets:
                    plan_destination_combo.addItem(f"{rs['code']} - {rs['name']}", rs["id"])

    def _generate_timetable_rows(self) -> bool:
        plan_timetable_table = self.plan_timetable_table
        if plan_timetable_table is None:
            return False
        try:
            route_id = self.plan_route_base.currentData() if self.plan_route_base is not None else None
            origin_id = self.plan_origin_combo.currentData() if self.plan_origin_combo is not None else None
            destination_id = self.plan_destination_combo.currentData() if self.plan_destination_combo is not None else None
            
            if route_id is None or origin_id is None or destination_id is None:
                self._show_warning("Thông tin Tuyến đường hoặc Ga chưa đầy đủ.")
                return False

            # 1. Xác định phân đoạn ga thực tế từ danh sách ga của tuyến đã nạp
            if not self.current_planner_route_stations:
                self._on_planner_route_changed()
                if not self.current_planner_route_stations:
                    self._show_warning("Dữ liệu ga chưa được nạp. Vui lòng chọn lại Tuyến đường.")
                    return False
            
            stations = self.current_planner_route_stations
            
            start_idx = -1
            end_idx = -1
            for i, s in enumerate(stations):
                if s["id"] == origin_id: start_idx = i
                if s["id"] == destination_id: end_idx = i
            
            if start_idx == -1 or end_idx == -1 or end_idx <= start_idx: 
                self._show_warning("Lỗi logic lộ trình: Ga kết thúc phải nằm sau Ga khởi hành trên tuyến đường đã chọn.")
                return False
                
            segment = stations[start_idx : end_idx + 1]

            # 2. Render bảng
            plan_timetable_table.blockSignals(True)
            plan_timetable_table.setRowCount(0)
            plan_timetable_table.setRowCount(len(segment))
            
            # Safely get start time string from UI; fallback to current time if widget is missing
            if self.plan_departure_input is not None:
                try:
                    start_time_obj = self.plan_departure_input.time()
                    start_time_str = start_time_obj.toString("HH:mm")
                except Exception:
                    start_time_str = datetime.now().strftime("%H:%M")
            else:
                start_time_str = datetime.now().strftime("%H:%M")

            curr_dt = datetime.combine(datetime.today(), datetime.strptime(start_time_str, "%H:%M").time())
            
            # Vận tốc trung bình thực tế (km/phút)
            AVG_MIN_PER_KM = 1.2 

            import random
            for i, rs in enumerate(segment):
                is_first = (i == 0)
                is_last = (i == len(segment) - 1)
                
                # Ga dừng
                plan_timetable_table.setItem(i, 0, QTableWidgetItem(f"{rs['code']} - {rs['name']}"))
                
                # Đón khách
                cb = QCheckBox()
                cb.setChecked(True)
                plan_timetable_table.setCellWidget(i, 1, cb)
                
                # Sân ga
                plan_timetable_table.setItem(i, 2, QTableWidgetItem(f"Số {random.randint(1,2)}"))
                
                # Tính Giờ Đến
                if not is_first:
                    dist_prev = segment[i-1]["distance_km"]
                    dist_curr = rs["distance_km"]
                    km_diff = abs(dist_curr - dist_prev)
                    curr_dt += timedelta(minutes=km_diff * AVG_MIN_PER_KM)
                
                arr_edit = QTimeEdit(QTime.fromString(curr_dt.strftime("%H:%M"), "HH:mm"))
                arr_edit.setDisplayFormat("HH:mm")
                if is_first: arr_edit.setEnabled(False)
                plan_timetable_table.setCellWidget(i, 3, arr_edit)
                
                # Thời gian Đỗ
                dwell = QSpinBox()
                dwell.setRange(0, 120)
                if is_first or is_last: dwell.setEnabled(False)
                else: dwell.setValue(10)
                plan_timetable_table.setCellWidget(i, 4, dwell)
                
                # Giờ đi = Đến + Đỗ
                if not is_first and not is_last:
                    curr_dt += timedelta(minutes=dwell.value())
                
                dep_edit = QTimeEdit(QTime.fromString(curr_dt.strftime("%H:%M"), "HH:mm"))
                dep_edit.setDisplayFormat("HH:mm")
                if is_last: dep_edit.setEnabled(False)
                plan_timetable_table.setCellWidget(i, 5, dep_edit)
                
                # Ngày lệch
                day_offset = (curr_dt.date() - datetime.today().date()).days
                plan_timetable_table.setItem(i, 6, QTableWidgetItem(str(day_offset)))
                
                # Cột 7: Hành động (Xóa ga)
                if not is_first and not is_last:
                    del_btn = QPushButton("Xóa")
                    del_btn.setStyleSheet("background: #ef4444; color: white; padding: 2px;")
                    del_btn.clicked.connect(lambda checked=False, r=i: self._remove_timetable_row(r))
                    plan_timetable_table.setCellWidget(i, 7, del_btn)
                else:
                    plan_timetable_table.setItem(i, 7, QTableWidgetItem(""))
                
                # Connect logic tự động cập nhật
                arr_edit.timeChanged.connect(lambda t, r=i: self._on_timetable_time_changed(r))
                dwell.valueChanged.connect(lambda v, r=i: self._on_timetable_time_changed(r))

            plan_timetable_table.blockSignals(False)
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._show_warning(f"Lỗi hệ thống khi sinh lịch trình: {str(e)}")
            return False

    def _remove_timetable_row(self, row_index: int) -> None:
        # Xóa hàng khỏi bảng
        plan_timetable_table = self.plan_timetable_table
        if plan_timetable_table is None:
            return
        item = plan_timetable_table.item(row_index, 0)
        ga_name = item.text() if item else "Không xác định"
        plan_timetable_table.removeRow(row_index)
        
        # Quan trọng: Sau khi xóa hàng, row_index của các hàng phía sau bị thay đổi
        # Chúng ta cần gán lại lambda cho tất cả các nút Xóa và bộ chỉnh giờ
        self._rebind_timetable_signals()
        
        # Tính toán lại giờ cho toàn bộ các ga từ vị trí vừa xóa
        self._cascade_timetable_updates(max(0, row_index - 1))
        self.statusBar().showMessage(f"Đã loại bỏ ga {ga_name} khỏi lộ trình", 3000)

    def _rebind_timetable_signals(self) -> None:
        plan_timetable_table = self.plan_timetable_table
        if plan_timetable_table is None:
            return
        plan_timetable_table.blockSignals(True)
        for i in range(plan_timetable_table.rowCount()):
            # Re-bind Xóa button (nếu có)
            btn = plan_timetable_table.cellWidget(i, 7)
            if isinstance(btn, QPushButton):
                try: btn.clicked.disconnect()
                except: pass
                btn.clicked.connect(lambda checked=False, r=i: self._remove_timetable_row(r))
            
            # Re-bind Time/Dwell changes
            arr = plan_timetable_table.cellWidget(i, 3)
            dwell = plan_timetable_table.cellWidget(i, 4)
            if isinstance(arr, QTimeEdit):
                try: arr.timeChanged.disconnect()
                except: pass
                arr.timeChanged.connect(lambda t, r=i: self._on_timetable_time_changed(r))
            if isinstance(dwell, QSpinBox):
                try: dwell.valueChanged.disconnect()
                except: pass
                dwell.valueChanged.connect(lambda v, r=i: self._on_timetable_time_changed(r))
        plan_timetable_table.blockSignals(False)

    def _on_timetable_time_changed(self, row: int) -> None:
        plan_timetable_table = self.plan_timetable_table
        if plan_timetable_table is None:
            return
        # Khi Giờ đến hoặc Đỗ thay đổi -> Tính lại Giờ đi của dòng đó
        arr_widget = plan_timetable_table.cellWidget(row, 3)
        dwell_widget = plan_timetable_table.cellWidget(row, 4)
        dep_widget = plan_timetable_table.cellWidget(row, 5)
        
        if not (isinstance(arr_widget, QTimeEdit) and isinstance(dwell_widget, QSpinBox) and isinstance(dep_widget, QTimeEdit)):
            return

        # Tính Giờ đi = Giờ đến + Đỗ
        new_dep_time = arr_widget.time().addSecs(dwell_widget.value() * 60)
        dep_widget.blockSignals(True)
        dep_widget.setTime(new_dep_time)
        dep_widget.blockSignals(False)

        # Lan truyền: Cập nhật Giờ đến của ga TIẾP THEO
        self._cascade_timetable_updates(row)

    def _cascade_timetable_updates(self, start_row: int) -> None:
        plan_timetable_table = self.plan_timetable_table
        if plan_timetable_table is None:
            return
        # Tự động tính toán lại toàn bộ các ga phía sau dựa trên sự thay đổi ở start_row
        row_count = plan_timetable_table.rowCount()
        AVG_MIN_PER_KM = 1.2 # Vận tốc giả định

        for i in range(start_row + 1, row_count):
            # 1. Lấy giờ đi của ga trước
            prev_dep_widget = plan_timetable_table.cellWidget(i-1, 5)
            if not isinstance(prev_dep_widget, QTimeEdit): break
            prev_dep_time = prev_dep_widget.time()

            # 2. Tính khoảng cách giữa 2 ga
            item_curr = plan_timetable_table.item(i, 0)
            item_prev = plan_timetable_table.item(i-1, 0)
            if not (item_curr and item_prev): break
            
            curr_ga_text = item_curr.text().split(" - ")[0]
            prev_ga_text = item_prev.text().split(" - ")[0]
            
            # Tìm trong MASTER data KM
            dist_curr = next((s["distance_km"] for s in self.current_planner_route_stations if s["code"] == curr_ga_text), 0)
            dist_prev = next((s["distance_km"] for s in self.current_planner_route_stations if s["code"] == prev_ga_text), 0)
            km_diff = abs(dist_curr - dist_prev)

            # 3. Cập nhật Giờ đến của ga hiện tại
            travel_secs = int(km_diff * AVG_MIN_PER_KM * 60)
            new_arr_time = prev_dep_time.addSecs(travel_secs)
            
            arr_widget = plan_timetable_table.cellWidget(i, 3)
            if isinstance(arr_widget, QTimeEdit):
                arr_widget.blockSignals(True)
                arr_widget.setTime(new_arr_time)
                arr_widget.blockSignals(False)

            # 4. Tính lại Giờ đi của ga hiện tại (Giờ đến + Đỗ)
            dwell_widget = plan_timetable_table.cellWidget(i, 4)
            dep_widget = plan_timetable_table.cellWidget(i, 5)
            if isinstance(dwell_widget, QSpinBox) and isinstance(dep_widget, QTimeEdit):
                new_dep_time = new_arr_time.addSecs(dwell_widget.value() * 60)
                dep_widget.blockSignals(True)
                dep_widget.setTime(new_dep_time)
                dep_widget.blockSignals(False)
            
    def _add_carriage_to_comp(self) -> None:
        plan_avail_carriages = self.plan_avail_carriages
        plan_train_composition = self.plan_train_composition
        if plan_avail_carriages is None or plan_train_composition is None:
            return
        
        item = plan_avail_carriages.currentItem()
        if not item: return
        cid = item.data(Qt.ItemDataRole.UserRole)
        new_item = QListWidgetItem(item.text())
        new_item.setData(Qt.ItemDataRole.UserRole, cid)
        plan_train_composition.addItem(new_item)

    def _remove_carriage_from_comp(self) -> None:
        plan_train_composition = self.plan_train_composition
        if plan_train_composition is None:
            return
        row = plan_train_composition.currentRow()
        if row >= 0:
            plan_train_composition.takeItem(row)

    def _update_planner_summary(self) -> None:
        # Đảm bảo UI tồn tại bằng biến cục bộ
        trip_code_widget = self.plan_trip_code
        train_type_widget = self.plan_train_type
        origin_combo = self.plan_origin_combo
        dest_combo = self.plan_destination_combo
        date_widget = self.plan_departure_date
        timetable_table = self.plan_timetable_table
        composition_list = self.plan_train_composition
        captain_combo = self.plan_captain_combo
        crew_combo = self.plan_crew_code
        summary_edit = self.plan_summary

        if (trip_code_widget is None or train_type_widget is None or origin_combo is None or 
            dest_combo is None or date_widget is None or timetable_table is None or 
            composition_list is None or captain_combo is None or crew_combo is None or 
            summary_edit is None):
            return

        trip_code = trip_code_widget.text()
        train_type = train_type_widget.currentText()
        origin = origin_combo.currentText()
        dest = dest_combo.currentText()
        date = date_widget.date().toString("dd/MM/yyyy")
        
        stops_count = timetable_table.rowCount()
        carriages_count = composition_list.count()
        
        summary = f"""
CHUYẾN TÀU: {trip_code} ({train_type})
HÀNH TRÌNH: {origin} ➔ {dest}
KHỞI HÀNH: {date}
------------------------------------------
THÔNG SỐ KỸ THUẬT:
- Số ga dừng: {stops_count} ga
- Số toa xe ghép nối: {carriages_count} toa
- Trưởng tàu: {captain_combo.currentText()}
- Đội tiếp viên: {crew_combo.currentText()}
------------------------------------------
DANH SÁCH GA DỰNG VÀ GIỜ TÀU:
"""
        for i in range(stops_count):
            item = timetable_table.item(i, 0)
            ga = item.text() if item else "N/A"
            arr_widget = timetable_table.cellWidget(i, 3)
            dep_widget = timetable_table.cellWidget(i, 5)
            arr = cast(QTimeEdit, arr_widget).time().toString("HH:mm") if isinstance(arr_widget, QTimeEdit) else "--:--"
            dep = cast(QTimeEdit, dep_widget).time().toString("HH:mm") if isinstance(dep_widget, QTimeEdit) else "--:--"
            if i == 0: summary += f"[GA ĐẦU] {ga} | Giờ đi: {dep}\n"
            elif i == stops_count - 1: summary += f"[GA CUỐI] {ga} | Giờ đến: {arr}\n"
            else: summary += f"  - {ga} | Đến: {arr} | Đi: {dep}\n"

        summary_edit.setPlainText(summary)

    def _create_table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        return table

    def refresh_all(self) -> None:
        role = self.current_user["role"]
        self.catalog = self.service.get_catalog()
        self.template_rows = self.service.get_train_templates()

        # Only refresh components that exist for the current role
        if role in ("admin", "staff"):
            self.refresh_dashboard()
            self.refresh_tickets()
            self.refresh_schedules()

        if role == "admin":
            self.refresh_catalog_tables()
            self.refresh_template_views()
            self.refresh_audit_logs()
            self.refresh_staff_table()

        if role == "customer":
            self.refresh_my_tickets()

        if role in ("admin", "staff"):
            self.populate_catalog_inputs()

        self.search_trips()

    def refresh_staff_table(self) -> None:
        staff_table = self.staff_table
        if staff_table is None:
            return
        users = self.catalog.get("users", [])
        staff_table.setRowCount(len(users))
        for i, u in enumerate(users):
            self._set_row(staff_table, i, [
                str(u["id"]), u["username"], u["full_name"], self._get_role_label(u["role"])
            ])

    def refresh_my_tickets(self) -> None:
        my_ticket_table = self.my_ticket_table
        if my_ticket_table is None:
            return
        # Lọc vé theo user hiện tại
        all_tickets = self.service.search_tickets("")
        self.my_ticket_rows = [t for t in all_tickets if t.get("booked_by_id") == self.current_user["id"] or t["id_number"] == self.current_user.get("id_number")]

        my_ticket_table.setRowCount(len(self.my_ticket_rows))
        for i, t in enumerate(self.my_ticket_rows):
            self._set_row(my_ticket_table, i, [
                t["ticket_code"], t["trip_code"], t["boarding_name"], t["alighting_name"],
                f"{t['carriage_code']}-{t['seat_code']}", self._currency(t["price"]),
                t["status"], t["booked_at"]
            ])
            
    def refresh_dashboard(self) -> None:
        dashboard = self.service.get_dashboard()
        
        # Đảm bảo các thành phần UI tồn tại
        if not self.stat_labels or self.revenue_chart_placeholder is None or self.occupancy_chart_placeholder is None:
            return

        self.stat_labels["tickets_sold"].setText(str(dashboard["tickets_sold"]))
        self.stat_labels["revenue"].setText(self._currency(float(dashboard["revenue"])))
        self.stat_labels["active_trips"].setText(str(dashboard["active_trips"]))
        self.stat_labels["occupancy_rate"].setText(f"{dashboard['occupancy_rate']}%")
        
        self._render_dashboard_chart(
            self.revenue_chart_placeholder,
            "Doanh thu theo tháng",
            cast(list[dict[str, Any]], dashboard.get("revenue_by_month", [])),
            value_suffix=" VND",
        )
        self._render_dashboard_chart(
            self.occupancy_chart_placeholder,
            "Tỷ lệ lấp đầy theo chuyến",
            cast(list[dict[str, Any]], dashboard.get("occupancy_by_trip", [])),
            value_suffix="%",
        )

    def refresh_tickets(self) -> None:
        ticket_table = self.ticket_table
        ticket_query_input = self.ticket_query_input
        if ticket_table is None or ticket_query_input is None:
            return
        self.ticket_rows = self.service.search_tickets(ticket_query_input.text())
        ticket_table.setRowCount(len(self.ticket_rows))
        for row_index, ticket in enumerate(self.ticket_rows):
            booker_info = "--"
            if ticket.get("booked_by_name"):
                booker_info = f"{ticket['booked_by_name']} ({ticket['booked_by_username']})"
            elif ticket.get("booked_by_username"):
                booker_info = ticket["booked_by_username"]

            values = [
                ticket["ticket_code"],
                ticket["full_name"],
                booker_info,
                ticket["id_number"],
                ticket["phone"],
                ticket["boarding_name"],
                ticket["alighting_name"],
                f"{ticket['carriage_code']}-{ticket['seat_code']}",
                self._currency(float(ticket["price"])),
                "Đã hủy" if ticket["status"] == "cancelled" else "Đã đặt",
                ticket["booked_at"],
            ]
            self._set_row(ticket_table, row_index, values)

    def refresh_schedules(self) -> None:
        schedule_table = self.schedule_table
        schedule_date_filter = self.schedule_date_filter
        if schedule_table is None or schedule_date_filter is None:
            return
        date_str = schedule_date_filter.date().toString("yyyy-MM-dd")
        self.schedule_rows = self.service.get_schedules(date_str)
        schedule_table.setRowCount(len(self.schedule_rows))
        for row_index, item in enumerate(self.schedule_rows):
            values = [
                item["trip_code"],
                item["train_code"],
                item["origin_name"],
                item["destination_name"],
                item["departure_date"],
                item["departure_time"],
                item["arrival_time"],
                item["status_label"],
                item["stop_count"],
                item["carriage_count"],
                f"{item['available_seats']}/{item['total_seats']}",
            ]
            self._set_row(schedule_table, row_index, values)
        self.selected_schedule_trip = None
        self.selected_schedule_stop = None
        self.schedule_detail_rows = []
        if self.schedule_trip_label is not None:
            self.schedule_trip_label.setText("Chọn một hành trình để xem chi tiết")
        if self.schedule_stop_table is not None:
            self.schedule_stop_table.setRowCount(0)
        self._reset_schedule_stop_form()

    def refresh_catalog_tables(self) -> None:
        if self.station_table is not None:
            self._fill_table(self.station_table, self.catalog["stations"], ["code", "name", "city"])
        if self.train_table is not None:
            self._fill_table(self.train_table, self.catalog["trains"], ["code", "name"])
        if self.carriage_table_catalog is not None:
            self._fill_table(self.carriage_table_catalog, self.catalog["carriages"], ["carriage_code", "seat_type", "seat_count"])

    def refresh_template_views(self) -> None:
        template_list = self.template_list
        if template_list is None:
            return
        template_list.clear()
        for template in self.template_rows:
            template_list.addItem(
                f"{template['name']} ({len(template['carriages'])} toa)\n{template['description'] or 'Không có mô tả'}"
            )
        self._refresh_template_carriage_list()

    def refresh_audit_logs(self) -> None:
        audit_table = self.audit_table
        audit_query_input = self.audit_query_input
        category_filter = self.audit_category_filter
        if audit_table is None or audit_query_input is None or category_filter is None:
            return

        query = audit_query_input.text()
        category_idx = category_filter.currentIndex()
        
        # Lấy dữ liệu từ service
        self.audit_rows = self.service.get_audit_logs(query)
        
        # Thực hiện lọc theo phân loại nghiệp vụ (trang)
        display_rows = self.audit_rows
        
        if category_idx > 0:
            if category_idx == 1: # Nghiệp vụ Bán vé
                display_rows = [r for r in self.audit_rows if r["target_type"] == "ticket"]
            elif category_idx == 2: # Điều hành Lịch trình
                display_rows = [r for r in self.audit_rows if r["target_type"] in ("trip", "station_trip") and r["action"] != "CREATE_TRIP"]
            elif category_idx == 3: # Lập hành trình mới
                display_rows = [r for r in self.audit_rows if r["target_type"] == "trip" and r["action"] == "CREATE_TRIP"]
            elif category_idx == 4: # Quản trị Danh mục
                display_rows = [r for r in self.audit_rows if r["target_type"] in ("station", "train", "carriage", "train_template")]
            elif category_idx == 5: # Quản trị Người dùng
                display_rows = [r for r in self.audit_rows if r["target_type"] == "user"]

        audit_table.setRowCount(len(display_rows))
        for row_index, item in enumerate(display_rows):
            values = [
                item["created_at"],
                item["full_name"] or item["username"] or "--",
                item["action"],
                item["target_type"],
                item["target_label"],
                item["details"],
            ]
            self._set_row(audit_table, row_index, values)
            
            # Tinh chỉnh màu sắc cho trực quan
            action = str(item["action"]).upper()
            color = "#1e293b" # Mặc định
            if "DELETE" in action or "CANCEL" in action: color = "#dc2626" # Đỏ cho xóa/hủy
            elif "CREATE" in action or "ADD" in action: color = "#16a34a"  # Xanh cho thêm mới
            elif "UPDATE" in action: color = "#2563eb"                     # Xanh dương cho cập nhật
            
            for col in range(audit_table.columnCount()):
                cell = audit_table.item(row_index, col)
                if cell: cell.setForeground(Qt.GlobalColor.black if color == "#1e293b" else Qt.GlobalColor.darkGray) # Tạm thời để đen/xám để dễ đọc
                # Hoặc thiết lập style cụ thể cho ô
                if cell:
                    font = cell.font()
                    if color != "#1e293b": font.setBold(True)
                    cell.setFont(font)

    def _on_schedule_trip_selected(self) -> None:
        schedule_table = self.schedule_table
        if schedule_table is None:
            return
        row = schedule_table.currentRow()
        if row < 0 or row >= len(self.schedule_rows):
            return
        self.selected_schedule_trip = self.schedule_rows[row]
        self.selected_schedule_stop = None
        detail = self.service.get_schedule_detail(int(self.selected_schedule_trip["id"]))
        trip = detail["trip"]
        self.schedule_detail_rows = detail["stops"]
        if self.schedule_trip_label is not None:
            self.schedule_trip_label.setText(
                f"<div style='line-height: 1.4;'>"
                f"<b style='font-size: 18px;'>Hành trình {trip['trip_code']}</b><br>"
                f"<span style='color: #cbd5e1; font-size: 14px;'>Tàu: {trip['train_code']} - {trip['train_name']}</span><br>"
                f"<span style='color: #ffffff; font-weight: bold;'>{self.selected_schedule_trip['origin_name']} ➔ {self.selected_schedule_trip['destination_name']}</span><br>"
                f"<span style='color: #bae6fd; font-size: 13px;'>Khởi hành: {trip['departure_date']} • {trip['departure_time']} - {trip['arrival_time']}</span><br>"
                f"<span style='color: #fbbf24; font-weight: bold; font-size: 16px;'>Giá vé cơ sở: {self._currency(float(trip['base_price']))}</span>"
                f"</div>"
            )
        if self.schedule_stop_table is not None:
            self.schedule_stop_table.setRowCount(len(self.schedule_detail_rows))
            for row_index, stop in enumerate(self.schedule_detail_rows):
                dwell_text = f"{stop['dwell_minutes']} phút" if stop["dwell_minutes"] else "--"
                values = [
                    stop["stop_order"],
                    stop["role_name"],
                    stop["station_code"],
                    stop["station_name"],
                    stop["arrival_time"] or "--",
                    stop["departure_time"] or "--",
                    dwell_text,
                ]
                self._set_row(self.schedule_stop_table, row_index, values)
        if self.schedule_stop_order_input is not None:
            self.schedule_stop_order_input.setMaximum(len(self.schedule_detail_rows) + 1)
        self._reset_schedule_stop_form()

    def _on_schedule_stop_selected(self) -> None:
        schedule_stop_table = self.schedule_stop_table
        if schedule_stop_table is None:
            return
        row = schedule_stop_table.currentRow()
        if row < 0 or row >= len(self.schedule_detail_rows):
            self.selected_schedule_stop = None
            return
        stop = self.schedule_detail_rows[row]
        self.selected_schedule_stop = stop
        if self.schedule_stop_order_input is not None:
            self.schedule_stop_order_input.setValue(int(stop["stop_order"]))
        if self.schedule_station_combo is not None:
            combo_index = self.schedule_station_combo.findData(int(stop["station_id"]))
            if combo_index >= 0:
                self.schedule_station_combo.setCurrentIndex(combo_index)
        if self.schedule_arrival_enabled is not None:
            self.schedule_arrival_enabled.setChecked(bool(stop["arrival_time"]))
        if self.schedule_departure_enabled is not None:
            self.schedule_departure_enabled.setChecked(bool(stop["departure_time"]))
        if stop["arrival_time"] and self.schedule_arrival_time is not None:
            self.schedule_arrival_time.setTime(self._parse_time(stop["arrival_time"]))
        if stop["departure_time"] and self.schedule_departure_time is not None:
            self.schedule_departure_time.setTime(self._parse_time(stop["departure_time"]))

    def _reset_schedule_stop_form(self) -> None:
        self.selected_schedule_stop = None
        if self.schedule_stop_order_input is not None:
            self.schedule_stop_order_input.setValue(1)
            self.schedule_stop_order_input.setMaximum(max(2, len(self.schedule_detail_rows) + 1))
        if self.schedule_arrival_enabled is not None:
            self.schedule_arrival_enabled.setChecked(False)
        if self.schedule_departure_enabled is not None:
            self.schedule_departure_enabled.setChecked(True)
        if self.schedule_arrival_time is not None:
            self.schedule_arrival_time.setTime(self.schedule_arrival_time.minimumTime())
        if self.schedule_departure_time is not None:
            self.schedule_departure_time.setTime(self.schedule_departure_time.minimumTime())

    def _schedule_form_times(self) -> tuple[str | None, str | None]:
        arrival_time = None
        if self.schedule_arrival_enabled is not None and self.schedule_arrival_time is not None:
            arrival_time = (
                self.schedule_arrival_time.time().toString("HH:mm")
                if self.schedule_arrival_enabled.isChecked()
                else None
            )
        departure_time = None
        if self.schedule_departure_enabled is not None and self.schedule_departure_time is not None:
            departure_time = (
                self.schedule_departure_time.time().toString("HH:mm")
                if self.schedule_departure_enabled.isChecked()
                else None
            )
        return arrival_time, departure_time

    def add_schedule_stop(self) -> None:
        if not self.selected_schedule_trip:
            self._show_warning("Vui lòng chọn lịch trình trước")
            return
        
        combo = self.schedule_station_combo
        order_input = self.schedule_stop_order_input
        if combo is None or order_input is None:
            return
            
        station_id = combo.currentData()
        if station_id is None:
            self._show_warning("Vui lòng chọn ga")
            return
        arrival_time, departure_time = self._schedule_form_times()
        try:
            self.service.add_trip_stop(
                trip_id=int(self.selected_schedule_trip["id"]),
                station_id=int(station_id),
                stop_order=int(order_input.value()),
                arrival_time=arrival_time,
                departure_time=departure_time,
                actor_user_id=int(self.current_user["id"]),
            )
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        self.refresh_schedules()
        self._restore_schedule_selection(int(self.selected_schedule_trip["id"]))
        self.statusBar().showMessage("Đã thêm điểm dừng", 4000)

    def update_schedule_stop(self) -> None:
        if not self.selected_schedule_stop:
            self._show_warning("Vui lòng chọn điểm dừng cần sửa")
            return
            
        combo = self.schedule_station_combo
        order_input = self.schedule_stop_order_input
        if combo is None or order_input is None:
            return
            
        station_id = combo.currentData()
        if station_id is None:
            self._show_warning("Vui lòng chọn ga")
            return
        arrival_time, departure_time = self._schedule_form_times()
        try:
            self.service.update_trip_stop(
                stop_id=int(self.selected_schedule_stop["id"]),
                station_id=int(station_id),
                stop_order=int(order_input.value()),
                arrival_time=arrival_time,
                departure_time=departure_time,
                actor_user_id=int(self.current_user["id"]),
            )
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        trip_id = int(self.selected_schedule_trip["id"]) if self.selected_schedule_trip else 0
        self.refresh_schedules()
        self._restore_schedule_selection(trip_id)
        self.statusBar().showMessage("Đã cập nhật điểm dừng", 4000)

    def delete_schedule_stop(self) -> None:
        if not self.selected_schedule_stop:
            self._show_warning("Vui lòng chọn điểm dừng cần xóa")
            return
        stop_order = int(self.selected_schedule_stop["stop_order"])
        if stop_order == 1 or stop_order == len(self.schedule_detail_rows):
            self._show_warning("Không được phép xóa ga đầu hoặc ga cuối")
            return
        confirm = QMessageBox.question(
            self,
            "Xác nhận",
            f"Xóa điểm dừng {self.selected_schedule_stop['station_name']}?",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            self.service.delete_trip_stop(int(self.selected_schedule_stop["id"]), int(self.current_user["id"]))
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        trip_id = int(self.selected_schedule_trip["id"]) if self.selected_schedule_trip else 0
        self.refresh_schedules()
        self._restore_schedule_selection(trip_id)
        self.statusBar().showMessage("Đã xóa điểm dừng", 4000)

    def _restore_schedule_selection(self, trip_id: int) -> None:
        schedule_table = self.schedule_table
        if schedule_table is None:
            return
        for row_index, trip in enumerate(self.schedule_rows):
            if int(trip["id"]) == trip_id:
                schedule_table.selectRow(row_index)
                self._on_schedule_trip_selected()
                return

    def _on_template_selected(self, row: int) -> None:
        if row < 0 or row >= len(self.template_rows):
            return
        template = self.template_rows[row]
        if self.template_name_input is not None:
            self.template_name_input.setText(str(template["name"]))
        if self.template_description_input is not None:
            self.template_description_input.setPlainText(str(template["description"] or ""))
        self.template_carriage_ids = [int(item["id"]) for item in template["carriages"]]
        self._refresh_template_carriage_list()

    def add_template_carriage(self) -> None:
        combo = self.template_carriage_combo
        if combo is None:
            return
        carriage_id_raw = combo.currentData()
        if carriage_id_raw is None:
            self._show_warning("Không có toa để chọn")
            return
        carriage_id = int(carriage_id_raw)
        if carriage_id in self.template_carriage_ids:
            self._show_warning("Toa này đã có trong mẫu")
            return
        self.template_carriage_ids.append(carriage_id)
        self._refresh_template_carriage_list()

    def remove_template_carriage(self) -> None:
        list_widget = self.template_carriage_list
        if list_widget is None:
            return
        row = list_widget.currentRow()
        if row < 0 or row >= len(self.template_carriage_ids):
            self._show_warning("Vui lòng chọn toa cần bỏ khỏi mẫu")
            return
        del self.template_carriage_ids[row]
        self._refresh_template_carriage_list()

    def _refresh_template_carriage_list(self) -> None:
        list_widget = self.template_carriage_list
        if list_widget is None:
            return
        carriage_map = {item["id"]: item for item in self.catalog["carriages"]}
        list_widget.clear()
        for carriage_id in self.template_carriage_ids:
            carriage = carriage_map.get(carriage_id, {})
            list_widget.addItem(
                f"{carriage.get('carriage_code', '?')} - {carriage.get('seat_type', '?')} ({carriage.get('seat_count', '?')} ghế)"
            )

    def create_template(self) -> None:
        name_input = self.template_name_input
        desc_input = self.template_description_input
        if name_input is None or desc_input is None:
            return
        try:
            self.service.create_train_template(
                name_input.text(),
                desc_input.toPlainText(),
                self.template_carriage_ids,
                int(self.current_user["id"]),
            )
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        name_input.clear()
        desc_input.clear()
        self.template_carriage_ids = []
        self.catalog = self.service.get_catalog()
        self.template_rows = self.service.get_train_templates()
        self.refresh_catalog_tables()
        self.refresh_template_views()
        self.populate_catalog_inputs()
        if self.current_user["role"] == "admin":
            self.refresh_audit_logs()
        self.statusBar().showMessage("Đã lưu mẫu đoàn tàu", 4000)

    def delete_template(self) -> None:
        list_widget = self.template_list
        if list_widget is None:
            return
        row = list_widget.currentRow()
        if row < 0 or row >= len(self.template_rows):
            self._show_warning("Vui lòng chọn mẫu đoàn tàu cần xóa")
            return
        template = self.template_rows[row]
        try:
            self.service.delete_train_template(int(template["id"]), int(self.current_user["id"]))
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        if self.template_name_input is not None: self.template_name_input.clear()
        if self.template_description_input is not None: self.template_description_input.clear()
        self.template_carriage_ids = []
        self.catalog = self.service.get_catalog()
        self.template_rows = self.service.get_train_templates()
        self.refresh_template_views()
        self.populate_catalog_inputs()
        if self.current_user["role"] == "admin":
            self.refresh_audit_logs()
        self.statusBar().showMessage(f"Đã xóa mẫu {template['name']}", 4000)

    def apply_trip_template(self) -> None:
        combo = self.plan_template_combo
        if combo is None:
            return
        template_id_raw = combo.currentData()
        if template_id_raw is None:
            self._show_warning("Vui lòng chọn mẫu đoàn tàu")
            return
        template_id = int(template_id_raw)
        template = next((item for item in self.template_rows if int(item["id"]) == template_id), None)
        if not template:
            self._show_warning("Không tìm thấy mẫu đoàn tàu đã chọn")
            return
        self.planned_carriage_ids = [int(item["id"]) for item in template["carriages"]]
        self._refresh_planned_carriage_list()
        self.statusBar().showMessage(f"Đã áp dụng mẫu {template['name']}", 4000)

    def populate_catalog_inputs(self) -> None:
        # 1. Sắp xếp Ga theo thứ tự địa lý (Bắc -> Nam)
        sorted_stations = sorted(
            self.catalog.get("stations", []),
            key=lambda x: ROUTE_TEMPLATE_ORDER.index(x["code"]) if x["code"] in ROUTE_TEMPLATE_ORDER else 999
        )

        station_names = []
        for s in sorted_stations:
            if s["name"] not in station_names:
                station_names.append(s["name"])
            if s["city"] not in station_names:
                station_names.append(s["city"])
        
        station_completer = self.station_completer
        if station_completer is not None:
            from PySide6.QtCore import QStringListModel
            station_completer.setModel(QStringListModel(station_names))
            if popup := station_completer.popup():
                popup.repaint()

        # Update other role-specific combos with safety checks
        plan_train_combo = self.plan_train_combo
        if plan_train_combo is not None:
            plan_train_combo.clear()
            for train in self.catalog.get("trains", []):
                plan_train_combo.addItem(f"{train['code']} - {train['name']}", train["id"])
        
        plan_template_combo = self.plan_template_combo
        if plan_template_combo is not None:
            plan_template_combo.clear()
            for tpl in self.template_rows:
                plan_template_combo.addItem(tpl["name"], tpl["id"])
        
        schedule_station_combo = self.schedule_station_combo
        if schedule_station_combo is not None:
            schedule_station_combo.clear()
            for station in sorted_stations:
                schedule_station_combo.addItem(
                    f"{station['code']} - {station['name']} ({station['city']})",
                    station["id"],
                )
        
        plan_origin_combo = self.plan_origin_combo
        plan_destination_combo = self.plan_destination_combo
        if plan_origin_combo is not None:
            plan_origin_combo.clear()
            if plan_destination_combo is not None:
                plan_destination_combo.clear()
            for station in sorted_stations:
                label = f"{station['code']} - {station['name']} ({station['city']})"
                plan_origin_combo.addItem(label, station["id"])
                if plan_destination_combo is not None:
                    plan_destination_combo.addItem(label, station["id"])

        # Safely populate carriage-related combos
        plan_carriage_combo = self.plan_carriage_combo
        template_carriage_combo = self.template_carriage_combo
        plan_avail_carriages = self.plan_avail_carriages
        
        if plan_carriage_combo is not None: plan_carriage_combo.clear()
        if template_carriage_combo is not None: template_carriage_combo.clear()
        if plan_avail_carriages is not None: plan_avail_carriages.clear()
        
        for carriage in self.catalog.get("carriages", []):
            carriage_label = f"{carriage['carriage_code']} - {carriage['seat_type']} ({carriage['seat_count']} ghế)"
            if plan_carriage_combo is not None:
                plan_carriage_combo.addItem(carriage_label, carriage["id"])
            if template_carriage_combo is not None:
                template_carriage_combo.addItem(carriage_label, carriage["id"])
            if plan_avail_carriages is not None:
                item = QListWidgetItem(carriage_label)
                item.setData(Qt.ItemDataRole.UserRole, carriage["id"])
                plan_avail_carriages.addItem(item)

        # Cập nhật danh sách Trưởng tàu
        plan_captain_combo = self.plan_captain_combo
        if plan_captain_combo is not None:
            plan_captain_combo.clear()
            for user in self.catalog.get("users", []):
                if user["role"] == "captain":
                    plan_captain_combo.addItem(f"{user['full_name']} ({user['username']})", user["id"])

        # Cập nhật danh sách Tuyến đường sắt
        plan_route_base = self.plan_route_base
        if plan_route_base is not None:
            plan_route_base.blockSignals(True)
            plan_route_base.clear()
            for route in self.catalog.get("routes", []):
                plan_route_base.addItem(route["route_name"], route["id"])
            plan_route_base.blockSignals(False)
            # Kích hoạt cập nhật ga lần đầu
            self._on_planner_route_changed()

    def search_trips(self) -> None:
        origin_input = self.origin_input
        destination_input = self.destination_input
        travel_date_input = self.travel_date_input
        trip_table = self.trip_table
        if origin_input is None or destination_input is None or travel_date_input is None or trip_table is None:
            return
        self.trip_rows = self.service.search_trips(
            origin_input.text(),
            destination_input.text(),
            travel_date_input.date().toString("yyyy-MM-dd"),
        )
        trip_table.setRowCount(len(self.trip_rows))
        for row_index, trip in enumerate(self.trip_rows):
            # Must match headers: ["Mã", "Tàu", "Ga đi", "Ga đến", "Giờ đi", "Giờ đến", "Giá vé"]
            values = [
                trip["trip_code"],
                trip["train_code"],
                trip["origin_name"],
                trip["destination_name"],
                trip["departure_time"],
                trip["arrival_time"],
                f"{int(trip['segment_base_price']):,} VND",
            ]
            self._set_row(trip_table, row_index, values)
        self.selected_trip = None
        self.selected_carriage = None
        self.selected_seat = None
        if self.selected_trip_label is not None:
            self.selected_trip_label.setText("Chưa chọn chuyến")
        if self.itinerary_list is not None:
            self.itinerary_list.clear()
        if self.carriage_panel_title is not None:
            self.carriage_panel_title.setText("Chưa chọn toa")
        if self.carriage_list is not None:
            self.carriage_list.clear()
        if self.selected_seat_label is not None:
            self.selected_seat_label.setText("Chưa chọn toa và ghế")
        self._refresh_booking_summary()
        self._render_seats([])

    def _on_quick_station_select(self, station_name: str) -> None:
        origin_input = self.origin_input
        destination_input = self.destination_input
        if origin_input is None or destination_input is None:
            return
        if not origin_input.text():
            origin_input.setText(station_name)
            destination_input.setFocus()
        else:
            destination_input.setText(station_name)
            self.search_trips()

    def _on_trip_selected(self) -> None:
        trip_table = self.trip_table
        if trip_table is None:
            return
        row = trip_table.currentRow()
        if row < 0 or row >= len(self.trip_rows):
            return
        self.selected_trip = self.trip_rows[row]
        self.selected_carriage = None
        self.selected_seat = None
        trip_data = self.service.get_trip_carriages(
            int(self.selected_trip["id"]),
            int(self.selected_trip["boarding_station_trip_id"]),
            int(self.selected_trip["alighting_station_trip_id"]),
        )
        self.current_trip_carriages = trip_data["carriages"]

        trip = trip_data["trip"]
        if self.selected_trip_label is not None:
            self.selected_trip_label.setText(
                f"{trip['origin_name']} -> {trip['destination_name']}<br>"
                f"<span style='font-size:16px; color:#475569;'>Ngày {trip['departure_date']} • "
                f"{trip['departure_time']} - {trip['arrival_time']} • Mã {trip['trip_code']} / Tàu {trip['train_code']}</span>"
            )
        if self.itinerary_list is not None:
            self.itinerary_list.clear()
            for stop in trip_data["itinerary"]:
                arrival = stop["arrival_time"] or "--"
                departure = stop["departure_time"] or "--"
                item = QListWidgetItem(
                    f"{stop['stop_order']}. {stop['station_name']} ({stop['station_code']}) | đến {arrival} | đi {departure}"
                )
                self.itinerary_list.addItem(item)

        if self.carriage_list is not None:
            self.carriage_list.clear()
            for index, carriage in enumerate(self.current_trip_carriages, start=1):
                self.carriage_list.addItem(
                    f"Toa {index}\n{carriage['carriage_code']} • {carriage['seat_type']}\n"
                    f"{carriage['available_seats']}/{carriage['total_seats']} chỗ trống"
                )
        if self.carriage_panel_title is not None:
            self.carriage_panel_title.setText("Chưa chọn toa")
        if self.selected_seat_label is not None:
            self.selected_seat_label.setText("Bước 1: chọn toa, sau đó chọn ghế")
        self._refresh_booking_summary()
        self._render_seats([])

    def _on_carriage_selected(self, _row: int | None = None) -> None:
        carriage_list = self.carriage_list
        if carriage_list is None:
            return
        row = carriage_list.currentRow()
        if row < 0 or row >= len(self.current_trip_carriages):
            return
        self.selected_carriage = self.current_trip_carriages[row]
        self.selected_seat = None
        self.current_seat_rows = self.service.get_carriage_seats(
            int(self.selected_carriage["id"]),
            int(self.selected_trip["boarding_station_trip_id"]) if self.selected_trip else None,
            int(self.selected_trip["alighting_station_trip_id"]) if self.selected_trip else None,
        )
        if self.carriage_panel_title is not None:
            self.carriage_panel_title.setText(
                f"Toa {row + 1}: {self.selected_carriage['seat_type']}"
            )
        if self.selected_seat_label is not None:
            self.selected_seat_label.setText(
                f"Đang xem {self.selected_carriage['carriage_code']} | "
                f"{self.selected_carriage['available_seats']}/{self.selected_carriage['total_seats']} chỗ trống"
            )
        self._refresh_booking_summary()
        self._render_seats(self.current_seat_rows)

    def _on_seat_selected(self, seat: dict[str, Any]) -> None:
        if seat["status"] != "available":
            self._show_warning("Ghế này đã được đặt")
            return
        self.selected_seat = seat
        if self.selected_seat_label is not None:
            self.selected_seat_label.setText(
                f"Đã chọn {seat['carriage_code']}-{seat['seat_code']} | {seat['seat_type']} | {self._currency(float(seat['seat_price']))}"
            )
        self._refresh_booking_summary()
        self._render_seats(self.current_seat_rows)

    def _render_seats(self, seats: list[dict[str, Any]]) -> None:
        while self.seat_grid.count():
            item = self.seat_grid.takeAt(0)
            if item and (widget := item.widget()):
                widget.deleteLater()
        if not seats:
            note = QLabel("Chọn toa để xem ghế.")
            note.setStyleSheet("color: #64748b; font-size: 18px; padding: 24px;")
            self.seat_grid.addWidget(note, 0, 0)
            return
        for index, seat in enumerate(seats):
            seat_price = self._currency(float(seat["seat_price"]))
            button = QPushButton(f"{seat['seat_code']}\n{seat_price}")
            if self.selected_seat and self.selected_seat["id"] == seat["id"]:
                button.setObjectName("seatSelected")
            elif seat["status"] == "booked":
                button.setObjectName("seatBooked")
            else:
                button.setObjectName("seatAvailable")
            button.clicked.connect(lambda _checked=False, current=seat: self._on_seat_selected(current))
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.seat_grid.addWidget(button, index // 4, index % 4)

    def _refresh_booking_summary(self) -> None:
        if not self.selected_trip:
            if self.booking_summary_label is not None:
                self.booking_summary_label.setText("Chưa chọn chuyến, toa và ghế")
            if self.booking_total_label is not None:
                self.booking_total_label.setText("Tổng tiền: 0 VND")
            return

        route_text = f"{self.selected_trip['origin_name']} -> {self.selected_trip['destination_name']}"
        carriage_text = self.selected_carriage["carriage_code"] if self.selected_carriage else "Chưa chọn toa"
        seat_text = self.selected_seat["seat_code"] if self.selected_seat else "Chưa chọn ghế"
        
        passenger_input = self.full_name_input
        passenger_text = passenger_input.text().strip() if passenger_input is not None else "Người lớn"
        if not passenger_text: passenger_text = "Người lớn"
        
        if self.booking_summary_label is not None:
            self.booking_summary_label.setText(
                f"{passenger_text}<br>{route_text}<br>{carriage_text} - Chỗ {seat_text}"
            )
        if self.booking_total_label is not None:
            if self.selected_seat:
                self.booking_total_label.setText(
                    f"Tổng tiền: {self._currency(float(self.selected_seat['seat_price']))}"
                )
            else:
                self.booking_total_label.setText("Tổng tiền: 0 VND")

    def create_booking(self) -> None:
        if not self.selected_trip or not self.selected_seat:
            self._show_warning("Vui lòng chọn chuyến, toa và ghế trước khi đặt vé")
            return
        
        full_name = self.full_name_input.text() if self.full_name_input else ""
        id_number = self.id_number_input.text() if self.id_number_input else ""
        phone = self.phone_input.text() if self.phone_input else ""
        
        try:
            ticket = self.service.create_booking(
                int(self.current_user["id"]),
                int(self.selected_trip["id"]),
                int(self.selected_seat["id"]),
                int(self.selected_trip["boarding_station_trip_id"]),
                int(self.selected_trip["alighting_station_trip_id"]),
                full_name,
                id_number,
                phone,
            )
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        except Exception as exc:
            import traceback
            traceback.print_exc()
            self._show_warning(f"Lỗi hệ thống khi đặt vé: {str(exc)}")
            return

        QMessageBox.information(self, "Đặt vé thành công", f"Đã tạo vé {ticket['ticket_code']}")
        if self.full_name_input: self.full_name_input.clear()
        if self.id_number_input: self.id_number_input.clear()
        if self.phone_input: self.phone_input.clear()
        self.refresh_all()
        self.statusBar().showMessage(f"Đã đặt vé {ticket['ticket_code']}", 5000)

    def print_selected_ticket(self) -> None:
        ticket_table = self.ticket_table
        if ticket_table is None:
            return
        row = ticket_table.currentRow()
        if row < 0 or row >= len(self.ticket_rows):
            self._show_warning("Vui lòng chọn vé cần in")
            return
        ticket_code = self.ticket_rows[row]["ticket_code"]
        detail = self.service.get_ticket_detail(ticket_code)
        if not detail:
            self._show_warning("Không tìm thấy thông tin chi tiết vé")
            return

        # Tạo nội dung vé (giả lập in)
        ticket_content = f"""
==========================================
        VÉ TÀU HỎA ĐIỆN TỬ
==========================================
Mã vé: {detail['ticket_code']}
Hành khách: {detail['full_name']}
CCCD: {detail['id_number']}
------------------------------------------
Chuyến: {detail['trip_code']} | Tàu: {detail['train_code']}
Ngày đi: {detail['departure_date']}
Khởi hành: {detail['departure_time']} tại {detail['boarding_name']}
Đến (dự kiến): {detail['arrival_time']} tại {detail['alighting_name']}
------------------------------------------
Vị trí: Toa {detail['carriage_code']} - Ghế {detail['seat_code']}
Loại chỗ: {detail['seat_type']}
Giá vé: {self._currency(detail['price'])}
Trạng thái: {detail['status'].upper()}
------------------------------------------
Ngày in: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Chúc quý khách có một chuyến đi an toàn!
==========================================
"""
        # Lưu ra file tạm hoặc hiển thị
        file_path, _ = QFileDialog.getSaveFileName(self, "In vé", f"Ve_{ticket_code}.txt", "Text Files (*.txt)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(ticket_content)
            QMessageBox.information(self, "Thành công", f"Đã in vé ra tệp:\n{file_path}")

    def validate_selected_ticket(self) -> None:
        ticket_table = self.ticket_table
        if ticket_table is None:
            return
        row = ticket_table.currentRow()
        if row < 0 or row >= len(self.ticket_rows):
            self._show_warning("Vui lòng chọn vé cần soát")
            return
        ticket = self.ticket_rows[row]
        if ticket["status"] == "cancelled":
            self._show_warning("Vé này không hợp lệ (Đã bị hủy)")
        else:
            QMessageBox.information(self, "Soát vé", f"VÉ HỢP LỆ\n\nKhách hàng: {ticket['full_name']}\nChỗ: {ticket['carriage_code']}-{ticket['seat_code']}\nTrạng thái: {ticket['status']}")

    def cancel_selected_ticket(self) -> None:
        if self.ticket_table is not None and self.ticket_table.isVisible():
            table = self.ticket_table
            rows = self.ticket_rows
        else:
            table = self.my_ticket_table
            rows = self.my_ticket_rows
            
        if table is None:
            return
            
        row = table.currentRow()
        if row < 0 or row >= len(rows):
            self._show_warning("Vui lòng chọn vé cần hủy")
            return
            
        ticket = rows[row]
        ticket_code = ticket["ticket_code"]

        confirm = QMessageBox.question(self, "Xác nhận", f"Hủy vé {ticket_code}?")
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            self.service.cancel_ticket(str(ticket_code), int(self.current_user["id"]))
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        self.refresh_all()
        self.statusBar().showMessage(f"Đã hủy vé {ticket_code}", 5000)

    def _on_staff_selected(self) -> None:
        table = self.staff_table
        if table is None:
            return
        rows = table.selectionModel().selectedRows()
        if not rows:
            self.selected_staff_id = None
            return
        
        row = rows[0].row()
        item = table.item(row, 0)
        if item is None:
            return
        user_id = int(item.text())
        self.selected_staff_id = user_id
        
        # Tìm user trong catalog
        users = self.catalog.get("users", [])
        user = next((u for u in users if u["id"] == user_id), None)
        if user:
            self.staff_username_input.setText(user["username"])
            self.staff_fullname_input.setText(user["full_name"])
            self.staff_password_input.clear() # Không hiển thị mật khẩu cũ
            
            index = self.staff_role_combo.findText(self._get_role_label(user["role"]))
            if index >= 0:
                self.staff_role_combo.setCurrentIndex(index)

    def add_user(self) -> None:
        try:
            username = self.staff_username_input.text()
            password = self.staff_password_input.text()
            fullname = self.staff_fullname_input.text()
            role = self._get_role_internal(self.staff_role_combo.currentText())
            
            self.service.add_user(username, password, fullname, role, int(self.current_user["id"]))
            self.refresh_all()
            
            self.staff_username_input.clear()
            self.staff_password_input.clear()
            self.staff_fullname_input.clear()
            self.statusBar().showMessage(f"Đã thêm người dùng {username}", 5000)
        except Exception as e:
            self._show_warning(str(e))

    def update_user(self) -> None:
        if self.selected_staff_id is None:
            self._show_warning("Vui lòng chọn người dùng từ danh sách trước")
            return
            
        try:
            username = self.staff_username_input.text()
            password = self.staff_password_input.text()
            fullname = self.staff_fullname_input.text()
            role = self._get_role_internal(self.staff_role_combo.currentText())
            
            self.service.update_user(
                self.selected_staff_id, username, password, fullname, role, int(self.current_user["id"])
            )
            self.refresh_all()
            self.statusBar().showMessage(f"Đã cập nhật thông tin cho {username}", 5000)
        except Exception as e:
            self._show_warning(str(e))

    def delete_user(self) -> None:
        if self.selected_staff_id is None:
            self._show_warning("Vui lòng chọn người dùng từ danh sách trước")
            return
            
        username = self.staff_username_input.text()
        confirm = QMessageBox.question(
            self, "Xác nhận xóa", f"Bạn có chắc chắn muốn xóa người dùng {username} không?"
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
            
        try:
            self.service.delete_user(self.selected_staff_id, int(self.current_user["id"]))
            self.refresh_all()
            
            self.selected_staff_id = None
            self.staff_username_input.clear()
            self.staff_fullname_input.clear()
            self.staff_password_input.clear()
            
            self.statusBar().showMessage(f"Đã xóa người dùng {username}", 5000)
        except Exception as e:
            self._show_warning(str(e))

    def add_station(self) -> None:
        code_input = self.station_code_input
        name_input = self.station_name_input
        city_input = self.station_city_input
        if code_input is None or name_input is None or city_input is None:
            return
        try:
            self.service.add_station(
                code_input.text(),
                name_input.text(),
                city_input.text(),
                int(self.current_user["id"]),
            )
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        code_input.clear()
        name_input.clear()
        city_input.clear()
        self.catalog = self.service.get_catalog()
        self.refresh_catalog_tables()
        self.populate_catalog_inputs()
        self.statusBar().showMessage("Đã thêm ga", 4000)

    def delete_station(self) -> None:
        station_table = self.station_table
        if station_table is None:
            return
        row = station_table.currentRow()
        if row < 0 or row >= len(self.catalog["stations"]):
            self._show_warning("Vui lòng chọn ga cần xóa")
            return
        station = self.catalog["stations"][row]
        try:
            self.service.delete_station(int(station["id"]), int(self.current_user["id"]))
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        self.catalog = self.service.get_catalog()
        self.refresh_catalog_tables()
        self.populate_catalog_inputs()
        self.statusBar().showMessage(f"Đã xóa ga {station['code']}", 4000)

    def add_train(self) -> None:
        code_input = self.train_code_input
        name_input = self.train_name_input
        if code_input is None or name_input is None:
            return
        try:
            self.service.add_train(code_input.text(), name_input.text(), int(self.current_user["id"]))
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        code_input.clear()
        name_input.clear()
        self.catalog = self.service.get_catalog()
        self.refresh_catalog_tables()
        self.populate_catalog_inputs()
        self.statusBar().showMessage("Đã thêm tàu", 4000)

    def delete_train(self) -> None:
        train_table = self.train_table
        if train_table is None:
            return
        row = train_table.currentRow()
        if row < 0 or row >= len(self.catalog["trains"]):
            self._show_warning("Vui lòng chọn tàu cần xóa")
            return
        train = self.catalog["trains"][row]
        try:
            self.service.delete_train(int(train["id"]), int(self.current_user["id"]))
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        self.catalog = self.service.get_catalog()
        self.refresh_catalog_tables()
        self.populate_catalog_inputs()
        self.statusBar().showMessage(f"Đã xóa tàu {train['code']}", 4000)

    def add_carriage(self) -> None:
        code_input = self.new_carriage_code_input
        type_input = self.new_carriage_type_input
        count_input = self.new_carriage_count_input
        if code_input is None or type_input is None or count_input is None:
            return
        try:
            self.service.add_carriage(
                code_input.text(),
                type_input.text(),
                int(count_input.text() or "0"),
                int(self.current_user["id"]),
            )
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        code_input.clear()
        if type_input: type_input.setText("Ghế mềm")
        if count_input: count_input.setText("12")
        self.catalog = self.service.get_catalog()
        self.refresh_catalog_tables()
        self.populate_catalog_inputs()
        self.statusBar().showMessage("Đã thêm toa", 4000)

    def delete_carriage(self) -> None:
        carriage_table = self.carriage_table_catalog
        if carriage_table is None:
            return
        row = carriage_table.currentRow()
        if row < 0 or row >= len(self.catalog["carriages"]):
            self._show_warning("Vui lòng chọn toa cần xóa")
            return
        carriage = self.catalog["carriages"][row]
        try:
            self.service.delete_carriage(int(carriage["id"]), int(self.current_user["id"]))
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        self.catalog = self.service.get_catalog()
        self.refresh_catalog_tables()
        self.populate_catalog_inputs()
        self.statusBar().showMessage(f"Đã xóa toa {carriage['carriage_code']}", 4000)

    def save_trip_draft(self) -> None:
        # Đảm bảo UI tồn tại
        plan_trip_code = self.plan_trip_code
        plan_timetable_table = self.plan_timetable_table
        plan_train_composition = self.plan_train_composition
        plan_train_combo = self.plan_train_combo
        plan_train_type = self.plan_train_type
        plan_captain_combo = self.plan_captain_combo
        plan_crew_code = self.plan_crew_code
        plan_departure_date = self.plan_departure_date
        plan_base_price_input = self.plan_base_price_input
        planner_stack = self.planner_stack
        planner_progress = self.planner_progress

        if (plan_trip_code is None or plan_timetable_table is None or plan_train_composition is None or 
            plan_train_combo is None or plan_train_type is None or plan_captain_combo is None or 
            plan_crew_code is None or plan_departure_date is None or plan_base_price_input is None or 
            planner_stack is None or planner_progress is None):
            return

        # Tương tự create_trip nhưng status là 'draft'
        trip_code = plan_trip_code.text().strip()
        if not trip_code:
            self._show_warning("Vui lòng nhập mã chuyến đi để lưu nháp")
            return
            
        stops_count = plan_timetable_table.rowCount()
        if stops_count < 2:
            self._show_warning("Bản nháp cần ít nhất 2 ga")
            return

        stops = []
        stations = self.catalog.get("stations", [])
        for i in range(stops_count):
            ga_item = plan_timetable_table.item(i, 0)
            ga_text = ga_item.text() if ga_item else ""
            code = ga_text.split(" - ")[0]
            sid = next((s["id"] for s in stations if s["code"] == code), None)
            if sid is None: continue
            
            check_widget = plan_timetable_table.cellWidget(i, 1)
            is_pick_up = 1 if isinstance(check_widget, QCheckBox) and check_widget.isChecked() else 0
            
            plat_item = plan_timetable_table.item(i, 2)
            platform = plat_item.text() if plat_item else ""
            
            arr_widget = plan_timetable_table.cellWidget(i, 3)
            arr = cast(QTimeEdit, arr_widget).time().toString("HH:mm") if isinstance(arr_widget, QTimeEdit) else "00:00"
            
            dwell_widget = plan_timetable_table.cellWidget(i, 4)
            dwell = cast(QSpinBox, dwell_widget).value() if isinstance(dwell_widget, QSpinBox) else 0
            
            dep_widget = plan_timetable_table.cellWidget(i, 5)
            dep = cast(QTimeEdit, dep_widget).time().toString("HH:mm") if isinstance(dep_widget, QTimeEdit) else "00:00"
            
            offset_item = plan_timetable_table.item(i, 6)
            offset = int(offset_item.text() if offset_item else "0")
            
            stops.append({
                "station_id": sid,
                "is_pick_up": is_pick_up,
                "platform_code": platform,
                "arrival_time": arr if i > 0 else None,
                "stop_duration_min": dwell,
                "departure_time": dep if i < stops_count - 1 else None,
                "day_offset": offset,
                "distance_km": ROUTE_TEMPLATE_DISTANCES.get(code, 0)
            })

        carriage_ids = []
        for i in range(plan_train_composition.count()):
            comp_item = plan_train_composition.item(i)
            if comp_item is not None:
                cid = comp_item.data(Qt.ItemDataRole.UserRole)
                if cid is not None:
                    carriage_ids.append(int(cid))

        try:
            train_id = plan_train_combo.currentData()
            if train_id is None:
                self._show_warning("Vui lòng chọn đầu máy")
                return

            self.service.create_trip(
                train_id=int(train_id),
                trip_code=trip_code,
                train_type=plan_train_type.currentText(),
                captain_id=plan_captain_combo.currentData(),
                crew_code=plan_crew_code.currentText(),
                departure_date=plan_departure_date.date().toString("yyyy-MM-dd"),
                base_price=float(plan_base_price_input.text() or "400000"),
                status="draft", # TRẠNG THÁI NHÁP
                stops=stops,
                carriage_ids=carriage_ids,
                actor_user_id=int(self.current_user["id"]),
            )
        except Exception as exc:
            self._show_warning(f"Lỗi khi lưu nháp: {str(exc)}")
            return

        self._reset_trip_planner()
        planner_stack.setCurrentIndex(0)
        planner_progress.setValue(1)
        self.refresh_all()
        QMessageBox.information(self, "Thông báo", f"Đã lưu bản nháp chuyến tàu {trip_code}.\nBạn có thể xem lại trong Tab Điều hành Lịch trình.")

    def create_trip(self) -> None:
        # Đảm bảo UI tồn tại
        plan_trip_code = self.plan_trip_code
        plan_timetable_table = self.plan_timetable_table
        plan_train_composition = self.plan_train_composition
        plan_train_combo = self.plan_train_combo
        plan_train_type = self.plan_train_type
        plan_captain_combo = self.plan_captain_combo
        plan_crew_code = self.plan_crew_code
        plan_departure_date = self.plan_departure_date
        plan_base_price_input = self.plan_base_price_input
        planner_stack = self.planner_stack
        planner_progress = self.planner_progress

        if (plan_trip_code is None or plan_timetable_table is None or plan_train_composition is None or 
            plan_train_combo is None or plan_train_type is None or plan_captain_combo is None or 
            plan_crew_code is None or plan_departure_date is None or plan_base_price_input is None or 
            planner_stack is None or planner_progress is None):
            return

        # 1. Kiểm tra cơ bản
        trip_code = plan_trip_code.text().strip()
        if not trip_code:
            self._show_warning("Vui lòng nhập mã chuyến đi")
            return
        
        stops_count = plan_timetable_table.rowCount()
        if stops_count < 2:
            self._show_warning("Hành trình phải có ít nhất 2 ga")
            return
            
        carriages_count = plan_train_composition.count()
        if carriages_count == 0:
            self._show_warning("Vui lòng ghép ít nhất 1 toa xe")
            return

        # 2. Thu thập danh sách ga dừng
        stops = []
        stations = self.catalog.get("stations", [])
        
        for i in range(stops_count):
            ga_item = plan_timetable_table.item(i, 0)
            ga_text = ga_item.text() if ga_item else ""
            code = ga_text.split(" - ")[0]
            sid = next((s["id"] for s in stations if s["code"] == code), None)
            if sid is None: continue
            
            check_widget = plan_timetable_table.cellWidget(i, 1)
            is_pick_up = 1 if isinstance(check_widget, QCheckBox) and check_widget.isChecked() else 0
            
            plat_item = plan_timetable_table.item(i, 2)
            platform = plat_item.text() if plat_item else ""
            
            arr_widget = plan_timetable_table.cellWidget(i, 3)
            arr = cast(QTimeEdit, arr_widget).time().toString("HH:mm") if isinstance(arr_widget, QTimeEdit) else "00:00"
            
            dwell_widget = plan_timetable_table.cellWidget(i, 4)
            dwell = cast(QSpinBox, dwell_widget).value() if isinstance(dwell_widget, QSpinBox) else 0
            
            dep_widget = plan_timetable_table.cellWidget(i, 5)
            dep = cast(QTimeEdit, dep_widget).time().toString("HH:mm") if isinstance(dep_widget, QTimeEdit) else "00:00"
            
            offset_item = plan_timetable_table.item(i, 6)
            offset = int(offset_item.text() if offset_item else "0")
            
            stops.append({
                "station_id": sid,
                "is_pick_up": is_pick_up,
                "platform_code": platform,
                "arrival_time": arr if i > 0 else None,
                "stop_duration_min": dwell,
                "departure_time": dep if i < stops_count - 1 else None,
                "day_offset": offset,
                "distance_km": ROUTE_TEMPLATE_DISTANCES.get(code, 0)
            })

        # 3. Thu thập danh sách toa xe
        carriage_ids = []
        for i in range(carriages_count):
            comp_item = plan_train_composition.item(i)
            if comp_item is not None:
                cid = comp_item.data(Qt.ItemDataRole.UserRole)
                carriage_ids.append(int(cid))

        try:
            train_id = plan_train_combo.currentData()
            if train_id is None:
                self._show_warning("Vui lòng chọn đầu máy.")
                return

            self.service.create_trip(
                train_id=int(train_id),
                trip_code=trip_code,
                train_type=plan_train_type.currentText(),
                captain_id=plan_captain_combo.currentData(),
                crew_code=plan_crew_code.currentText(),
                departure_date=plan_departure_date.date().toString("yyyy-MM-dd"),
                base_price=float(plan_base_price_input.text() or "400000"),
                status="open",
                stops=stops,
                carriage_ids=carriage_ids,
                actor_user_id=int(self.current_user["id"]),
            )

        except Exception as exc:
            self._show_warning(f"Lỗi khi tạo chuyến: {str(exc)}")
            return

        self._reset_trip_planner()
        planner_stack.setCurrentIndex(0)
        planner_progress.setValue(1)
        self.refresh_all()
        self.statusBar().showMessage(f"Đã xuất bản chuyến tàu {trip_code}", 5000)

    def add_planned_carriage(self) -> None:
        plan_carriage_combo = self.plan_carriage_combo
        if plan_carriage_combo is None:
            return
        carriage_id_raw = plan_carriage_combo.currentData()
        if carriage_id_raw is None:
            self._show_warning("Không có toa để chọn")
            return
        carriage_id = int(carriage_id_raw)
        if carriage_id in self.planned_carriage_ids:
            self._show_warning("Toa này đã có trong chuyến")
            return
        self.planned_carriage_ids.append(carriage_id)
        self._refresh_planned_carriage_list()

    def remove_planned_carriage(self) -> None:
        plan_carriage_list = self.plan_carriage_list
        if plan_carriage_list is None:
            return
        row = plan_carriage_list.currentRow()
        if row < 0 or row >= len(self.planned_carriage_ids):
            self._show_warning("Vui lòng chọn toa cần bỏ")
            return
        del self.planned_carriage_ids[row]
        self._refresh_planned_carriage_list()

    def remove_planned_stop(self) -> None:
        plan_stop_list = self.plan_stop_list
        if plan_stop_list is None:
            return
        row = plan_stop_list.currentRow()
        if row < 0 or row >= len(self.planned_stops):
            self._show_warning("Vui lòng chọn ga cần xóa khỏi hành trình")
            return
        if row == 0 or row == len(self.planned_stops) - 1:
            self._show_warning("Chỉ được xóa ga trung gian, không được xóa ga khởi hành hoặc ga kết thúc")
            return
        removed_stop = self.planned_stops[row]
        del self.planned_stops[row]
        self._refresh_planned_stop_list()
        station_map = {item["id"]: item for item in self.catalog["stations"]}
        station = station_map.get(removed_stop["station_id"], {})
        self.statusBar().showMessage(
            f"Đã xóa ga trung gian {station.get('name', 'đã chọn')} khỏi hành trình",
            4000,
        )

    def generate_planned_route(self) -> None:
        plan_origin_combo = self.plan_origin_combo
        plan_destination_combo = self.plan_destination_combo
        plan_departure_input = self.plan_departure_input
        if plan_origin_combo is None or plan_destination_combo is None or plan_departure_input is None:
            return
        station_by_id = {item["id"]: item for item in self.catalog["stations"]}
        origin_id_raw = plan_origin_combo.currentData()
        destination_id_raw = plan_destination_combo.currentData()
        if origin_id_raw is None or destination_id_raw is None:
            self._show_warning("Vui lòng chọn ga đầu và ga cuối")
            return
        
        origin_id = int(origin_id_raw)
        destination_id = int(destination_id_raw)

        origin_station = station_by_id.get(origin_id)
        destination_station = station_by_id.get(destination_id)
        if not origin_station or not destination_station:
            self._show_warning("Không xác định được ga đầu hoặc ga cuối")
            return

        origin_code = origin_station["code"]
        destination_code = destination_station["code"]
        if origin_code == destination_code:
            self._show_warning("Ga khởi hành và ga kết thúc phải khác nhau")
            return
        if origin_code not in ROUTE_TEMPLATE_ORDER or destination_code not in ROUTE_TEMPLATE_ORDER:
            self._show_warning("Chỉ hỗ trợ tạo nhanh cho các ga trên tuyến mẫu HN - V - HU - DN - NT - SG")
            return

        origin_index = ROUTE_TEMPLATE_ORDER.index(origin_code)
        destination_index = ROUTE_TEMPLATE_ORDER.index(destination_code)
        step = 1 if origin_index < destination_index else -1
        route_codes = ROUTE_TEMPLATE_ORDER[origin_index : destination_index + step : step]
        departure_time_text = plan_departure_input.time().toString("HH:mm")

        current_time = datetime.strptime(departure_time_text, "%H:%M")
        station_code_map = {item["code"]: item["id"] for item in self.catalog["stations"]}
        missing_codes = [code for code in route_codes if code not in station_code_map]
        if missing_codes:
            self._show_warning(f"Thiếu dữ liệu ga cho tuyến mẫu: {', '.join(missing_codes)}")
            return
        planned_stops: list[dict[str, Any]] = []

        for index, code in enumerate(route_codes):
            dist = ROUTE_TEMPLATE_DISTANCES.get(code, 0)
            if index == 0:
                planned_stops.append(
                    {
                        "station_id": station_code_map[code],
                        "arrival_time": "",
                        "departure_time": current_time.strftime("%H:%M"),
                        "distance_km": dist,
                    }
                )
                continue

            previous_code = route_codes[index - 1]
            km_diff = abs(dist - ROUTE_TEMPLATE_DISTANCES.get(previous_code, 0))
            # Rough estimate: 1.5 min per km
            current_time += timedelta(minutes=km_diff * 1.5)
            arrival_time = current_time.strftime("%H:%M")

            if index == len(route_codes) - 1:
                planned_stops.append(
                    {
                        "station_id": station_code_map[code],
                        "arrival_time": arrival_time,
                        "departure_time": "",
                        "distance_km": dist,
                    }
                )
                continue

            current_time += timedelta(minutes=10) # 10 min dwell
            planned_stops.append(
                {
                    "station_id": station_code_map[code],
                    "arrival_time": arrival_time,
                    "departure_time": current_time.strftime("%H:%M"),
                    "distance_km": dist,
                }
            )

        self.planned_stops = planned_stops
        self._refresh_planned_stop_list()
        self.statusBar().showMessage(
            f"Đã tạo nhanh hành trình {origin_station['name']} -> {destination_station['name']}",
            4000,
        )

    def _refresh_planned_stop_list(self) -> None:
        plan_stop_list = self.plan_stop_list
        if plan_stop_list is None:
            return
        station_map = {item["id"]: item for item in self.catalog["stations"]}
        plan_stop_list.clear()
        for index, stop in enumerate(self.planned_stops, start=1):
            station = station_map.get(stop["station_id"], {})
            arrival = stop.get("arrival_time") or "--"
            departure = stop.get("departure_time") or "--"
            stop_role = "Ga khởi hành" if index == 1 else "Ga kết thúc" if index == len(self.planned_stops) else "Ga trung gian"
            plan_stop_list.addItem(
                f"{index}. {station.get('code', '?')} - {station.get('name', '?')} | "
                f"{stop_role} | đến {arrival} | đi {departure}"
            )

    def _refresh_planned_carriage_list(self) -> None:
        plan_carriage_list = self.plan_carriage_list
        if plan_carriage_list is None:
            # Nếu đang dùng Wizard Step 3
            plan_train_composition = self.plan_train_composition
            if plan_train_composition is not None:
                # Cập nhật wizard nếu cần (từ mẫu template)
                plan_train_composition.clear()
                carriage_map = {item["id"]: item for item in self.catalog["carriages"]}
                for cid in self.planned_carriage_ids:
                    c = carriage_map.get(cid)
                    if c:
                        item = QListWidgetItem(f"{c['carriage_code']} - {c['seat_type']}")
                        item.setData(Qt.ItemDataRole.UserRole, cid)
                        plan_train_composition.addItem(item)
            return
        carriage_map = {item["id"]: item for item in self.catalog["carriages"]}
        plan_carriage_list.clear()
        for carriage_id in self.planned_carriage_ids:
            carriage = carriage_map.get(carriage_id, {})
            plan_carriage_list.addItem(
                f"{carriage.get('carriage_code', '?')} - {carriage.get('seat_type', '?')} ({carriage.get('seat_count', '?')} ghế)"
            )

    def _reset_trip_planner(self) -> None:
        if self.plan_trip_code is not None:
            self.plan_trip_code.clear()
        if self.plan_trip_code_input is not None:
            self.plan_trip_code_input.clear()

        if self.plan_base_price_input is not None:
            self.plan_base_price_input.setText("400000")

        if self.plan_departure_input is not None:
            self.plan_departure_input.setTime(self.plan_departure_input.minimumTime())

        if self.plan_origin_combo is not None and self.plan_origin_combo.count() > 0:
            self.plan_origin_combo.setCurrentIndex(0)

        if self.plan_destination_combo is not None and self.plan_destination_combo.count() > 1:
            self.plan_destination_combo.setCurrentIndex(self.plan_destination_combo.count() - 1)
        self.planned_stops = []
        self.planned_carriage_ids = []
        self._refresh_planned_stop_list()
        self._refresh_planned_carriage_list()

    def cancel_selected_trip_manual(self) -> None:
        schedule_table = self.schedule_table
        if schedule_table is None:
            return
        row = schedule_table.currentRow()
        if row < 0 or row >= len(self.schedule_rows):
            self._show_warning("Vui lòng chọn chuyến cần hủy")
            return
        trip = self.schedule_rows[row]
        confirm = QMessageBox.question(self, "Xác nhận", f"Hủy chuyến {trip['trip_code']} do sự cố?")
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            self.service.cancel_trip_manual(int(trip["id"]), int(self.current_user["id"]))
        except ValueError as exc:
            self._show_warning(str(exc))
            return
        self.refresh_all()
        self.statusBar().showMessage(f"Đã hủy chuyến {trip['trip_code']}", 5000)

    def delete_selected_trip(self) -> None:
        schedule_table = self.schedule_table
        if schedule_table is None:
            return
        row = schedule_table.currentRow()
        if row < 0 or row >= len(self.schedule_rows):
            self._show_warning("Vui lòng chọn chuyến cần xóa")
            return
        trip = self.schedule_rows[row]
        confirm = QMessageBox.question(self, "Xác nhận", f"Xóa chuyến {trip['trip_code']}?")
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.service.delete_trip(int(trip["id"]), int(self.current_user["id"]))
        self.refresh_all()
        self.statusBar().showMessage(f"Đã xóa chuyến {trip['trip_code']}", 4000)

    def _fill_table(self, table: QTableWidget, rows: list[dict[str, Any]], fields: list[str]) -> None:
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self._set_row(table, row_index, [row[field] for field in fields])

    def _set_row(self, table: QTableWidget, row_index: int, values: list[Any]) -> None:
        for column_index, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_index, column_index, item)

    def _render_dashboard_chart(
        self,
        widget_ref: QWidget,
        title: str,
        items: list[dict[str, Any]],
        *,
        value_suffix: str,
    ) -> None:
        if QChartView is None or QChart is None or QBarSeries is None or QBarSet is None or QBarCategoryAxis is None or QValueAxis is None:
            if isinstance(widget_ref, QLabel):
                if not items:
                    widget_ref.setText(f"Chưa có dữ liệu cho {title.lower()}")
                else:
                    widget_ref.setText(
                        "\n".join(f"{item['label']}: {item['value'] if 'value' in item else item['occupancy_rate']}{value_suffix}" for item in items)
                    )
            return

        parent = widget_ref.parentWidget()
        layout = parent.layout() if parent else None
        if layout is None:
            return
        data_values = [float(item["value"] if "value" in item else item["occupancy_rate"]) for item in items] or [0.0]
        labels = [str(item["label"]) for item in items] or ["Chưa có dữ liệu"]
        bar_set = QBarSet(title)
        for value in data_values:
            bar_set.append(value)
        series = QBarSeries()
        series.append(bar_set)
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        axis_y = QValueAxis()
        axis_y.setRange(0, max(data_values) * 1.2 if max(data_values) else 10)
        axis_y.setLabelFormat("%d")
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        chart.legend().setVisible(False)
        if isinstance(widget_ref, QChartView):
            widget_ref.setChart(chart)
            return
        
        chart_view = QChartView(chart)
        chart_view.setMinimumHeight(260)
        
        # Replace only if layout exists
        if layout is not None:
            layout.replaceWidget(widget_ref, chart_view)
            widget_ref.deleteLater()
            
        if title == "Doanh thu theo tháng":
            self.revenue_chart_placeholder = chart_view
        else:
            self.occupancy_chart_placeholder = chart_view

    def _parse_time(self, value: str) -> QTime:
        return QTime.fromString(str(value), "HH:mm")

    def _currency(self, value: float) -> str:
        return f"{value:,.0f} VND".replace(",", ".")

    def _show_warning(self, message: str) -> None:
        QMessageBox.warning(self, "Thông báo", message)

    def _show_info(self, message: str) -> None:
        QMessageBox.information(self, "Thông báo", message)


def run() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Hệ thống quản lý bán vé tàu")

    database = DatabaseManager()
    database.initialize()
    service = TicketService(database)

    login_dialog = LoginDialog(service)
    if login_dialog.exec() != QDialog.DialogCode.Accepted or not login_dialog.user:
        return

    window = MainWindow(service, login_dialog.user)
    window.show()
    sys.exit(app.exec())
