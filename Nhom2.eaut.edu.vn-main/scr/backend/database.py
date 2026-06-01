from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    city TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    carriage_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS carriages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_id INTEGER NOT NULL,
    carriage_code TEXT NOT NULL,
    seat_type TEXT NOT NULL,
    seat_count INTEGER NOT NULL,
    FOREIGN KEY (train_id) REFERENCES trains(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_id INTEGER NOT NULL,
    trip_code TEXT NOT NULL UNIQUE,
    origin_station_id INTEGER NOT NULL,
    destination_station_id INTEGER NOT NULL,
    departure_date TEXT NOT NULL,
    departure_time TEXT NOT NULL,
    arrival_time TEXT NOT NULL,
    base_price REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    FOREIGN KEY (train_id) REFERENCES trains(id),
    FOREIGN KEY (origin_station_id) REFERENCES stations(id),
    FOREIGN KEY (destination_station_id) REFERENCES stations(id)
);

CREATE TABLE IF NOT EXISTS trip_seats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL,
    carriage_code TEXT NOT NULL,
    seat_code TEXT NOT NULL,
    seat_type TEXT NOT NULL,
    seat_price REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'available',
    UNIQUE (trip_id, carriage_code, seat_code),
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS passengers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    id_number TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_code TEXT NOT NULL UNIQUE,
    passenger_id INTEGER NOT NULL,
    trip_id INTEGER NOT NULL,
    trip_seat_id INTEGER NOT NULL,
    booked_by INTEGER NOT NULL,
    price REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'paid',
    booked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (passenger_id) REFERENCES passengers(id),
    FOREIGN KEY (trip_id) REFERENCES trips(id),
    FOREIGN KEY (trip_seat_id) REFERENCES trip_seats(id),
    FOREIGN KEY (booked_by) REFERENCES users(id)
);
"""


class DatabaseManager:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA_SQL)
            self._seed_data(connection)
            connection.commit()

    def _seed_data(self, connection: sqlite3.Connection) -> None:
        user_count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count:
            return

        connection.executemany(
            "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
            [
                ("admin", "admin123", "Quan tri vien", "admin"),
                ("staff", "staff123", "Nhan vien ban ve", "staff"),
            ],
        )

        connection.executemany(
            "INSERT INTO stations (code, name, city) VALUES (?, ?, ?)",
            [
                ("SG", "Ga Sai Gon", "Ho Chi Minh"),
                ("NT", "Ga Nha Trang", "Khanh Hoa"),
                ("DN", "Ga Da Nang", "Da Nang"),
                ("HU", "Ga Hue", "Thua Thien Hue"),
                ("HN", "Ga Ha Noi", "Ha Noi"),
            ],
        )

        connection.executemany(
            "INSERT INTO trains (code, name, carriage_count) VALUES (?, ?, ?)",
            [
                ("SE01", "Tau Thong Nhat 01", 3),
                ("SE03", "Tau Thong Nhat 03", 3),
            ],
        )

        trains = {
            row["code"]: row["id"] for row in connection.execute("SELECT id, code FROM trains")
        }
        connection.executemany(
            "INSERT INTO carriages (train_id, carriage_code, seat_type, seat_count) VALUES (?, ?, ?, ?)",
            [
                (trains["SE01"], "A1", "Ghe mem", 8),
                (trains["SE01"], "B1", "Giuong nam", 8),
                (trains["SE01"], "C1", "Ghe cung", 8),
                (trains["SE03"], "A2", "Ghe mem", 8),
                (trains["SE03"], "B2", "Giuong nam", 8),
                (trains["SE03"], "C2", "Ghe cung", 8),
            ],
        )

        stations = {
            row["code"]: row["id"] for row in connection.execute("SELECT id, code FROM stations")
        }
        connection.executemany(
            """
            INSERT INTO trips (
                train_id, trip_code, origin_station_id, destination_station_id,
                departure_date, departure_time, arrival_time, base_price, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (trains["SE01"], "SE01-2026-04-20", stations["SG"], stations["NT"], "2026-04-20", "07:00", "14:30", 350000, "open"),
                (trains["SE01"], "SE01-2026-04-21", stations["SG"], stations["DN"], "2026-04-21", "08:00", "22:00", 620000, "open"),
                (trains["SE03"], "SE03-2026-04-20", stations["SG"], stations["HU"], "2026-04-20", "09:30", "04:50", 710000, "open"),
            ],
        )

        trips = connection.execute("SELECT id, train_id, base_price FROM trips").fetchall()
        carriage_rows = connection.execute(
            "SELECT train_id, carriage_code, seat_type, seat_count FROM carriages"
        ).fetchall()

        seat_rows = []
        for trip in trips:
            for carriage in carriage_rows:
                if carriage["train_id"] != trip["train_id"]:
                    continue
                for index in range(1, carriage["seat_count"] + 1):
                    multiplier = 1.0 if carriage["seat_type"] == "Ghe cung" else 1.15 if carriage["seat_type"] == "Ghe mem" else 1.35
                    seat_rows.append(
                        (
                            trip["id"],
                            carriage["carriage_code"],
                            f"{index:02d}",
                            carriage["seat_type"],
                            trip["base_price"] * multiplier,
                            "available",
                        )
                    )

        connection.executemany(
            """
            INSERT INTO trip_seats (trip_id, carriage_code, seat_code, seat_type, seat_price, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            seat_rows,
        )

        connection.execute(
            "UPDATE trip_seats SET status = 'booked' WHERE trip_id = 1 AND carriage_code = 'A1' AND seat_code IN ('01', '02', '03')"
        )
        connection.execute(
            "UPDATE trip_seats SET status = 'booked' WHERE trip_id = 2 AND carriage_code = 'B1' AND seat_code IN ('04', '05')"
        )
