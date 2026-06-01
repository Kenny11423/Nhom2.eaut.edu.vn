from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "12"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS app_meta (
    meta_key VARCHAR(100) PRIMARY KEY,
    meta_value VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS trains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS carriages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    carriage_code VARCHAR(20) NOT NULL UNIQUE,
    seat_type VARCHAR(100) NOT NULL,
    seat_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS train_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS train_template_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    carriage_id INTEGER NOT NULL,
    item_order INTEGER NOT NULL,
    UNIQUE (template_id, carriage_id),
    UNIQUE (template_id, item_order),
    FOREIGN KEY (template_id) REFERENCES train_templates(id) ON DELETE CASCADE,
    FOREIGN KEY (carriage_id) REFERENCES carriages(id)
);

CREATE TABLE IF NOT EXISTS railway_routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS route_stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL,
    station_id INTEGER NOT NULL,
    stop_order INTEGER NOT NULL,
    distance_km REAL NOT NULL,
    UNIQUE (route_id, station_id),
    UNIQUE (route_id, stop_order),
    FOREIGN KEY (route_id) REFERENCES railway_routes(id) ON DELETE CASCADE,
    FOREIGN KEY (station_id) REFERENCES stations(id)
);

CREATE TABLE IF NOT EXISTS train_staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR(255) NOT NULL,
    staff_role VARCHAR(50) NOT NULL, -- 'captain', 'crew'
    status VARCHAR(50) DEFAULT 'available'
);

CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_id INTEGER NOT NULL,
    trip_code VARCHAR(50) NOT NULL UNIQUE,
    train_type VARCHAR(100),
    captain_id INTEGER,
    crew_code VARCHAR(50),
    departure_date VARCHAR(20) NOT NULL,
    departure_time VARCHAR(20) NOT NULL,
    arrival_time VARCHAR(20) NOT NULL,
    base_price REAL NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    FOREIGN KEY (train_id) REFERENCES trains(id),
    FOREIGN KEY (captain_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS station_trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL,
    station_id INTEGER NOT NULL,
    stop_order INTEGER NOT NULL,
    is_pick_up INTEGER DEFAULT 1,
    platform_code VARCHAR(20),
    arrival_time VARCHAR(20),
    stop_duration_min INTEGER DEFAULT 0,
    departure_time VARCHAR(20),
    day_offset INTEGER DEFAULT 0,
    distance_km REAL DEFAULT 0,
    custom_fare REAL DEFAULT 0,
    UNIQUE (trip_id, stop_order),
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    FOREIGN KEY (station_id) REFERENCES stations(id)
);

CREATE TABLE IF NOT EXISTS carriage_trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL,
    carriage_id INTEGER NOT NULL,
    carriage_order INTEGER NOT NULL,
    UNIQUE (trip_id, carriage_id),
    UNIQUE (trip_id, carriage_order),
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    FOREIGN KEY (carriage_id) REFERENCES carriages(id)
);

CREATE TABLE IF NOT EXISTS trip_seats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    carriage_trip_id INTEGER NOT NULL,
    seat_code VARCHAR(20) NOT NULL,
    seat_type VARCHAR(100) NOT NULL,
    seat_price REAL NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'available',
    UNIQUE (carriage_trip_id, seat_code),
    FOREIGN KEY (carriage_trip_id) REFERENCES carriage_trips(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS passengers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR(255) NOT NULL,
    id_number VARCHAR(50) NOT NULL UNIQUE,
    phone VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_code VARCHAR(50) NOT NULL UNIQUE,
    passenger_id INTEGER NOT NULL,
    trip_id INTEGER NOT NULL,
    trip_seat_id INTEGER NOT NULL,
    boarding_station_trip_id INTEGER NOT NULL,
    alighting_station_trip_id INTEGER NOT NULL,
    booked_by INTEGER NOT NULL,
    price REAL NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'booked',
    booked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (passenger_id) REFERENCES passengers(id),
    FOREIGN KEY (trip_id) REFERENCES trips(id),
    FOREIGN KEY (trip_seat_id) REFERENCES trip_seats(id),
    FOREIGN KEY (boarding_station_trip_id) REFERENCES station_trips(id),
    FOREIGN KEY (alighting_station_trip_id) REFERENCES station_trips(id),
    FOREIGN KEY (booked_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id VARCHAR(100),
    target_label VARCHAR(255),
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


class ConnectionAdapter:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def __enter__(self) -> ConnectionAdapter:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            self.connection.rollback()
        else:
            self.connection.commit()
        self.connection.close()

    def execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        return self.connection.execute(sql, parameters)

    def executemany(self, sql: str, parameters: list[tuple[Any, ...]]) -> sqlite3.Cursor:
        return self.connection.executemany(sql, parameters)

    def executescript(self, sql: str) -> sqlite3.Cursor:
        return self.connection.executescript(sql)

    def commit(self) -> None:
        self.connection.commit()


def _build_upsert_query(table: str, keys: list[str], values: list[str]) -> str:
    key_str = ", ".join(keys)
    val_str = ", ".join(f":{v}" for v in values)
    update_str = ", ".join(f"{v}=excluded.{v}" for v in values if v not in keys)
    query = f"INSERT INTO {table} ({key_str}) VALUES ({val_str}) ON CONFLICT({', '.join(keys)}) DO UPDATE SET {update_str}"
    return query


def _quote_identifier(identifier: str) -> str:
    return f"`{identifier.replace('`', '``')}`"


class DatabaseManager:
    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            # Get the project root directory
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            self.db_path = base_dir / "train_ticket.db"
        else:
            self.db_path = Path(db_path)

    def connect(self) -> ConnectionAdapter:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return ConnectionAdapter(connection)

    def initialize(self) -> None:
        # SQLite creates the file automatically, so we just connect and initialize
        with self.connect() as connection:
            if self._get_schema_version(connection) != SCHEMA_VERSION:
                # Ensure all tables from SCHEMA_SQL exist (using CREATE TABLE IF NOT EXISTS)
                connection.executescript(SCHEMA_SQL)

                # Migration: add custom_fare column if it's missing from existing station_trips table
                cursor = connection.execute("PRAGMA table_info(station_trips)")
                columns = [row[1] for row in cursor.fetchall()]
                if "custom_fare" not in columns:
                    connection.execute("ALTER TABLE station_trips ADD COLUMN custom_fare REAL DEFAULT 0")
                
                # Update version
                connection.execute(
                    "INSERT OR REPLACE INTO app_meta (meta_key, meta_value) VALUES (?, ?)",
                    ("schema_version", SCHEMA_VERSION)
                )

            self._seed_data(connection)
            connection.commit()

    def _ensure_database_exists(self) -> None:
        # No-op for SQLite
        pass

    def _has_table(self, connection: ConnectionAdapter, table_name: str) -> bool:
        row = connection.execute(
            "SELECT count(*) as total FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        return bool(row and row["total"])

    def _get_schema_version(self, connection: ConnectionAdapter) -> str | None:
        if not self._has_table(connection, "app_meta"):
            return None
        row = connection.execute(
            "SELECT meta_value FROM app_meta WHERE meta_key = 'schema_version'"
        ).fetchone()
        return str(row["meta_value"]) if row else None

    def _rebuild_schema(self, connection: ConnectionAdapter) -> None:
        connection.execute("PRAGMA foreign_keys = OFF")
        for table_name in [
            "audit_logs",
            "tickets",
            "trip_seats",
            "carriage_trips",
            "station_trips",
            "railway_routes",
            "route_stations",
            "train_staff",
            "passengers",
            "trips",
            "train_template_items",
            "train_templates",
            "carriages",
            "trains",
            "stations",
            "users",
            "app_meta",
        ]:
            connection.execute(f"DROP TABLE IF EXISTS {_quote_identifier(table_name)}")
        connection.executescript(SCHEMA_SQL)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "INSERT INTO app_meta (meta_key, meta_value) VALUES ('schema_version', ?)",
            (SCHEMA_VERSION,),
        )

    def _seed_data(self, connection: ConnectionAdapter) -> None:
        user_count = connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
        if user_count:
            return

        # 1. Users
        connection.executemany(
            "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
            [
                ("admin", "admin123", "Quản trị viên", "admin"),
                ("staff", "staff123", "Nhân viên bán vé", "staff"),
                ("user", "user", "Người dùng", "customer"),
            ],
        )

        # 2. 7 Tuyến đường sắt chính
        routes_data = [
            ("Đường sắt Bắc - Nam", "Hà Nội - Sài Gòn"),
            ("Hà Nội - Lào Cai", "Tuyến Tây Bắc"),
            ("Hà Nội - Hải Phòng", "Tuyến phía Đông"),
            ("Hà Nội - Đồng Đăng", "Tuyến Lạng Sơn"),
            ("Hà Nội - Quán Triều", "Tuyến Thái Nguyên"),
            ("Yên Viên - Hạ Long", "Tuyến Quảng Ninh"),
            ("Sài Gòn - Phan Thiết", "Tuyến du lịch")
        ]
        route_ids = {}
        for name, desc in routes_data:
            cur = connection.execute("INSERT INTO railway_routes (route_name, description) VALUES (?, ?)", (name, desc))
            route_ids[name] = cur.lastrowid

        # 3. Các Ga (Master Data)
        all_stations = [
            ('HN', 'Hà Nội', 'Hà Nội'), ('PL', 'Phủ Lý', 'Hà Nam'), ('ND', 'Nam Định', 'Nam Định'),
            ('NB', 'Ninh Bình', 'Ninh Bình'), ('TH', 'Thanh Hóa', 'Thanh Hóa'), ('V', 'Vinh', 'Nghệ An'),
            ('HU', 'Huế', 'Huế'), ('DN', 'Đà Nẵng', 'Đà Nẵng'), ('NT', 'Nha Trang', 'Khánh Hòa'),
            ('SG', 'Sài Gòn', 'TP.HCM'), ('LC', 'Lào Cai', 'Lào Cai'), ('HP', 'Hải Phòng', 'Hải Phòng'),
            ('DD', 'Đồng Đăng', 'Lạng Sơn'), ('QT', 'Quán Triều', 'Thái Nguyên'), ('HL', 'Hạ Long', 'Quảng Ninh'),
            ('PT', 'Phan Thiết', 'Bình Thuận'), ('GL', 'Gia Lâm', 'Hà Nội'), ('YV', 'Yên Viên', 'Hà Nội'),
            ('VT', 'Việt Trì', 'Phú Thọ'), ('YB', 'Yên Bái', 'Yên Bái'), ('HD', 'Hải Dương', 'Hải Dương'),
            ('UP', 'Uông Bí', 'Quảng Ninh')
        ]
        station_ids = {}
        for code, name, city in all_stations:
            cur = connection.execute("INSERT INTO stations (code, name, city) VALUES (?, ?, ?)", (code, name, city))
            station_ids[code] = cur.lastrowid

        # 4. Ánh xạ Ga vào Tuyến
        rid_bn = route_ids["Đường sắt Bắc - Nam"]
        bn = [('HN', 1, 0), ('PL', 2, 56), ('ND', 3, 87), ('NB', 4, 115), ('TH', 5, 176), ('V', 6, 319), ('HU', 7, 688), ('DN', 8, 791), ('NT', 9, 1315), ('SG', 10, 1726)]
        for code, order, dist in bn:
            connection.execute("INSERT INTO route_stations (route_id, station_id, stop_order, distance_km) VALUES (?, ?, ?, ?)", 
                             (rid_bn, station_ids[code], order, dist))
        
        rid_lc = route_ids["Hà Nội - Lào Cai"]
        lc = [('HN', 1, 0), ('GL', 2, 5), ('YV', 3, 11), ('VT', 4, 73), ('YB', 5, 155), ('LC', 6, 296)]
        for code, order, dist in lc:
            connection.execute("INSERT INTO route_stations (route_id, station_id, stop_order, distance_km) VALUES (?, ?, ?, ?)", 
                             (rid_lc, station_ids[code], order, dist))
        
        rid_hp = route_ids["Hà Nội - Hải Phòng"]
        hp = [('HN', 1, 0), ('GL', 2, 5), ('HD', 3, 57), ('HP', 4, 102)]
        for code, order, dist in hp:
            connection.execute("INSERT INTO route_stations (route_id, station_id, stop_order, distance_km) VALUES (?, ?, ?, ?)", 
                             (rid_hp, station_ids[code], order, dist))
        
        rid_hl = route_ids["Yên Viên - Hạ Long"]
        hl = [('YV', 1, 0), ('UP', 2, 120), ('HL', 3, 160)]
        for code, order, dist in hl:
            connection.execute("INSERT INTO route_stations (route_id, station_id, stop_order, distance_km) VALUES (?, ?, ?, ?)", 
                             (rid_hl, station_ids[code], order, dist))

        # 5. Trưởng tàu
        captains = ["Nguyễn Văn Mạnh", "Trần Đức Thắng", "Lê Hồng Anh", "Phạm Minh Hoàng", "Vũ Quang Huy", "Đặng Quốc Bảo"]
        for name in captains:
            connection.execute("INSERT INTO train_staff (full_name, staff_role) VALUES (?, 'captain')", (name,))

        # 6. Tàu, Toa, Mẫu
        connection.executemany("INSERT INTO trains (code, name) VALUES (?, ?)", [("SE1", "SE1 Express"), ("SE3", "SE3 Express")])
        connection.executemany("INSERT INTO carriages (carriage_code, seat_type, seat_count) VALUES (?, ?, ?)", [
            ("A1", "Ghế mềm", 64), ("B1", "Giường nằm", 28), ("C1", "Ghế cứng", 80), ("VIP1", "Khoang VIP", 12)
        ])
        
        c_map = {r["carriage_code"]: r["id"] for r in connection.execute("SELECT id, carriage_code FROM carriages").fetchall()}
        tid = connection.execute("INSERT INTO train_templates (name, description) VALUES (?, ?)", ("Mẫu SE chuẩn", "Mẫu chuẩn 4 toa")).lastrowid
        connection.executemany("INSERT INTO train_template_items (template_id, carriage_id, item_order) VALUES (?, ?, ?)", [
            (tid, c_map["A1"], 1), (tid, c_map["B1"], 2), (tid, c_map["C1"], 3), (tid, c_map["VIP1"], 4)
        ])
