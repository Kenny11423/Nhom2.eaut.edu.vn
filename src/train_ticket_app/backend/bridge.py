from __future__ import annotations

import json
import sqlite3
from datetime import datetime

import numpy as np
from PySide6.QtCore import QObject, Slot

from src.train_ticket_app.backend.database import DatabaseManager


class AppBridge(QObject):
    def __init__(self, database: DatabaseManager) -> None:
        super().__init__()
        self.database = database
        self.current_user: dict[str, str] | None = None

    @Slot(str, result=str)
    def login(self, payload: str) -> str:
        data = json.loads(payload or "{}")
        with self.database.connect() as connection:
            user = connection.execute(
                """
                SELECT id, username, full_name, role
                FROM users
                WHERE username = ? AND password = ?
                """,
                (data.get("username", "").strip(), data.get("password", "").strip()),
            ).fetchone()
        if not user:
            return self._response(False, "Sai tai khoan hoac mat khau")

        self.current_user = dict(user)
        dashboard = self._build_dashboard_payload()
        return self._response(True, "Dang nhap thanh cong", {"user": self.current_user, "dashboard": dashboard})

    @Slot(result=str)
    def bootstrap(self) -> str:
        return self._response(
            True,
            "Bootstrap du lieu thanh cong",
            {
                "dashboard": self._build_dashboard_payload(),
                "schedules": self._get_schedule_rows(),
                "tickets": self._search_tickets(""),
            },
        )

    @Slot(str, result=str)
    def searchTrips(self, payload: str) -> str:
        data = json.loads(payload or "{}")
        origin = data.get("origin", "").strip()
        destination = data.get("destination", "").strip()
        travel_date = data.get("travel_date", "").strip()
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    trips.id,
                    trips.trip_code,
                    trains.code AS train_code,
                    origin.name AS origin_name,
                    destination.name AS destination_name,
                    trips.departure_date,
                    trips.departure_time,
                    trips.arrival_time,
                    trips.base_price,
                    SUM(CASE WHEN trip_seats.status = 'available' THEN 1 ELSE 0 END) AS available_seats
                FROM trips
                JOIN trains ON trains.id = trips.train_id
                JOIN stations AS origin ON origin.id = trips.origin_station_id
                JOIN stations AS destination ON destination.id = trips.destination_station_id
                JOIN trip_seats ON trip_seats.trip_id = trips.id
                WHERE origin.city LIKE ?
                  AND destination.city LIKE ?
                  AND trips.departure_date LIKE ?
                GROUP BY trips.id
                ORDER BY trips.departure_date, trips.departure_time
                """,
                (f"%{origin}%", f"%{destination}%", f"%{travel_date}%"),
            ).fetchall()

        trips = [dict(row) for row in rows]
        return self._response(True, "Tim thay ket qua", {"trips": trips})

    @Slot(str, result=str)
    def getTripSeats(self, payload: str) -> str:
        data = json.loads(payload or "{}")
        trip_id = data.get("trip_id")
        with self.database.connect() as connection:
            trip = connection.execute(
                """
                SELECT trips.id, trips.trip_code, trains.code AS train_code,
                       origin.name AS origin_name, destination.name AS destination_name,
                       trips.departure_date, trips.departure_time, trips.arrival_time
                FROM trips
                JOIN trains ON trains.id = trips.train_id
                JOIN stations AS origin ON origin.id = trips.origin_station_id
                JOIN stations AS destination ON destination.id = trips.destination_station_id
                WHERE trips.id = ?
                """,
                (trip_id,),
            ).fetchone()
            seats = connection.execute(
                """
                SELECT id, carriage_code, seat_code, seat_type, seat_price, status
                FROM trip_seats
                WHERE trip_id = ?
                ORDER BY carriage_code, seat_code
                """,
                (trip_id,),
            ).fetchall()

        return self._response(True, "Lay so do cho thanh cong", {"trip": dict(trip) if trip else None, "seats": [dict(row) for row in seats]})

    @Slot(str, result=str)
    def createBooking(self, payload: str) -> str:
        if not self.current_user:
            return self._response(False, "Can dang nhap truoc khi dat ve")

        data = json.loads(payload or "{}")
        with self.database.connect() as connection:
            seat = connection.execute(
                """
                SELECT id, status, seat_price, carriage_code, seat_code
                FROM trip_seats
                WHERE trip_id = ? AND id = ?
                """,
                (data.get("trip_id"), data.get("seat_id")),
            ).fetchone()
            if not seat:
                return self._response(False, "Khong tim thay cho ngoi")
            if seat["status"] != "available":
                return self._response(False, "Cho ngoi da duoc dat")

            passenger_id = self._upsert_passenger(connection, data)
            ticket_code = f"VE{int(datetime.now().timestamp())}"
            connection.execute(
                """
                INSERT INTO tickets (ticket_code, passenger_id, trip_id, trip_seat_id, booked_by, price, status)
                VALUES (?, ?, ?, ?, ?, ?, 'paid')
                """,
                (
                    ticket_code,
                    passenger_id,
                    data.get("trip_id"),
                    seat["id"],
                    self.current_user["id"],
                    seat["seat_price"],
                ),
            )
            connection.execute(
                "UPDATE trip_seats SET status = 'booked' WHERE id = ?",
                (seat["id"],),
            )
            connection.commit()

        return self._response(
            True,
            "Dat ve thanh cong",
            {
                "ticket_code": ticket_code,
                "seat_label": f"{seat['carriage_code']}-{seat['seat_code']}",
                "price": seat["seat_price"],
                "dashboard": self._build_dashboard_payload(),
                "tickets": self._search_tickets(""),
            },
        )

    @Slot(str, result=str)
    def searchTickets(self, payload: str) -> str:
        data = json.loads(payload or "{}")
        query = data.get("query", "").strip()
        return self._response(True, "Lay danh sach ve thanh cong", {"tickets": self._search_tickets(query)})

    @Slot(str, result=str)
    def cancelTicket(self, payload: str) -> str:
        data = json.loads(payload or "{}")
        ticket_code = data.get("ticket_code", "").strip()
        with self.database.connect() as connection:
            ticket = connection.execute(
                """
                SELECT tickets.id, tickets.trip_seat_id, tickets.status
                FROM tickets
                WHERE ticket_code = ?
                """,
                (ticket_code,),
            ).fetchone()
            if not ticket:
                return self._response(False, "Khong tim thay ve")
            if ticket["status"] == "cancelled":
                return self._response(False, "Ve da huy truoc do")

            connection.execute(
                "UPDATE tickets SET status = 'cancelled' WHERE id = ?",
                (ticket["id"],),
            )
            connection.execute(
                "UPDATE trip_seats SET status = 'available' WHERE id = ?",
                (ticket["trip_seat_id"],),
            )
            connection.commit()

        return self._response(
            True,
            "Huy ve thanh cong",
            {
                "dashboard": self._build_dashboard_payload(),
                "tickets": self._search_tickets(""),
            },
        )

    @Slot(result=str)
    def getSchedules(self) -> str:
        return self._response(True, "Lay lich trinh thanh cong", {"schedules": self._get_schedule_rows()})

    def _search_tickets(self, query: str) -> list[dict[str, object]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    tickets.ticket_code,
                    passengers.full_name,
                    passengers.id_number,
                    passengers.phone,
                    trips.trip_code,
                    trains.code AS train_code,
                    origin.name AS origin_name,
                    destination.name AS destination_name,
                    trip_seats.carriage_code,
                    trip_seats.seat_code,
                    tickets.price,
                    tickets.status,
                    tickets.booked_at
                FROM tickets
                JOIN passengers ON passengers.id = tickets.passenger_id
                JOIN trips ON trips.id = tickets.trip_id
                JOIN trains ON trains.id = trips.train_id
                JOIN stations AS origin ON origin.id = trips.origin_station_id
                JOIN stations AS destination ON destination.id = trips.destination_station_id
                JOIN trip_seats ON trip_seats.id = tickets.trip_seat_id
                WHERE tickets.ticket_code LIKE ?
                   OR passengers.id_number LIKE ?
                   OR passengers.phone LIKE ?
                   OR passengers.full_name LIKE ?
                ORDER BY tickets.booked_at DESC
                """,
                (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"),
            ).fetchall()
        return [dict(row) for row in rows]

    def _get_schedule_rows(self) -> list[dict[str, object]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    trips.trip_code,
                    trains.code AS train_code,
                    origin.name AS origin_name,
                    destination.name AS destination_name,
                    trips.departure_date,
                    trips.departure_time,
                    trips.arrival_time,
                    trips.status
                FROM trips
                JOIN trains ON trains.id = trips.train_id
                JOIN stations AS origin ON origin.id = trips.origin_station_id
                JOIN stations AS destination ON destination.id = trips.destination_station_id
                ORDER BY trips.departure_date, trips.departure_time
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def _build_dashboard_payload(self) -> dict[str, object]:
        with self.database.connect() as connection:
            trip_rows = connection.execute(
                """
                SELECT
                    trips.id,
                    SUM(CASE WHEN trip_seats.status = 'available' THEN 1 ELSE 0 END) AS available_count,
                    COUNT(trip_seats.id) AS total_count
                FROM trips
                JOIN trip_seats ON trip_seats.trip_id = trips.id
                GROUP BY trips.id
                """
            ).fetchall()
            ticket_rows = connection.execute(
                "SELECT price, status FROM tickets"
            ).fetchall()

        total_capacity = np.array([row["total_count"] for row in trip_rows], dtype=np.float64)
        available_capacity = np.array([row["available_count"] for row in trip_rows], dtype=np.float64)
        sold_capacity = total_capacity - available_capacity
        occupancy_rate = float(np.round((sold_capacity.sum() / total_capacity.sum()) * 100, 2)) if total_capacity.size else 0.0

        ticket_prices = np.array(
            [row["price"] for row in ticket_rows if row["status"] != "cancelled"],
            dtype=np.float64,
        )
        cancelled_count = int(sum(1 for row in ticket_rows if row["status"] == "cancelled"))

        return {
            "tickets_sold": int(ticket_prices.size),
            "revenue": float(ticket_prices.sum()) if ticket_prices.size else 0.0,
            "active_trips": int(len(trip_rows)),
            "cancelled_tickets": cancelled_count,
            "occupancy_rate": occupancy_rate,
        }

    def _upsert_passenger(self, connection: sqlite3.Connection, data: dict[str, object]) -> int:
        passenger = connection.execute(
            "SELECT id FROM passengers WHERE id_number = ?",
            (data.get("id_number"),),
        ).fetchone()
        if passenger:
            connection.execute(
                """
                UPDATE passengers
                SET full_name = ?, phone = ?
                WHERE id = ?
                """,
                (data.get("full_name"), data.get("phone"), passenger["id"]),
            )
            return int(passenger["id"])

        cursor = connection.execute(
            """
            INSERT INTO passengers (full_name, id_number, phone)
            VALUES (?, ?, ?)
            """,
            (data.get("full_name"), data.get("id_number"), data.get("phone")),
        )
        return int(cursor.lastrowid)

    def _response(self, ok: bool, message: str, data: dict[str, object] | None = None) -> str:
        return json.dumps({"ok": ok, "message": message, "data": data or {}}, ensure_ascii=False)
