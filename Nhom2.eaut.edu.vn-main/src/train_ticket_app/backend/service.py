from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import numpy as np

from src.train_ticket_app.backend.database import DatabaseManager


class TicketService:
    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def login(self, username: str, password: str) -> dict[str, Any] | None:
        with self.database.connect() as connection:
            user = connection.execute(
                """
                SELECT id, username, full_name, role
                FROM users
                WHERE username = ? AND password = ?
                """,
                (username.strip(), password.strip()),
            ).fetchone()
        return dict(user) if user else None

    def bootstrap_payload(self) -> dict[str, Any]:
        return {
            "dashboard": self.get_dashboard(),
            "schedules": self.get_schedules(),
            "tickets": self.search_tickets(""),
            "catalog": self.get_catalog(),
        }

    def get_catalog(self) -> dict[str, list[dict[str, Any]]]:
        with self.database.connect() as connection:
            stations = connection.execute(
                "SELECT id, code, name, city FROM stations ORDER BY code"
            ).fetchall()
            trains = connection.execute(
                "SELECT id, code, name FROM trains ORDER BY code"
            ).fetchall()
            carriages = connection.execute(
                "SELECT id, carriage_code, seat_type, seat_count FROM carriages ORDER BY carriage_code"
            ).fetchall()
            routes = connection.execute(
                "SELECT id, route_name FROM railway_routes ORDER BY id"
            ).fetchall()
            captains = connection.execute(
                "SELECT id, full_name FROM train_staff WHERE staff_role = 'captain' AND status = 'available' ORDER BY full_name"
            ).fetchall()
            
            return {
                "stations": [dict(r) for r in stations],
                "trains": [dict(r) for r in trains],
                "carriages": [dict(r) for r in carriages],
                "routes": [dict(r) for r in routes],
                "captains": [dict(r) for r in captains],
                "users": self.get_users(),
            }

    def get_users(self) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT id, username, full_name, role FROM users ORDER BY role, username"
            ).fetchall()
            return [dict(r) for r in rows]

    def add_user(
        self, username: str, password: str, full_name: str, role: str, actor_user_id: int | None = None
    ) -> int:
        username = username.strip()
        full_name = full_name.strip()
        if not username or not password or not full_name:
            raise ValueError("Vui lòng nhập đầy đủ thông tin người dùng")
        
        with self.database.connect() as connection:
            # Kiểm tra username trùng
            exists = connection.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if exists:
                raise ValueError(f"Tên đăng nhập '{username}' đã tồn tại")

            user_id = connection.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                (username, password.strip(), full_name, role),
            ).lastrowid
            
            self._write_audit_log(
                connection,
                user_id=actor_user_id,
                action="CREATE_USER",
                target_type="user",
                target_id=str(user_id),
                target_label=f"{username} ({full_name})",
                details=f"Thêm người dùng mới với vai trò {role}",
            )
            connection.commit()
            return int(user_id)

    def update_user(
        self, user_id: int, username: str, password: str, full_name: str, role: str, actor_user_id: int | None = None
    ) -> None:
        username = username.strip()
        full_name = full_name.strip()
        if not username or not full_name:
            raise ValueError("Tên đăng nhập và Họ tên không được để trống")

        with self.database.connect() as connection:
            # Kiểm tra username trùng (trừ chính nó)
            exists = connection.execute(
                "SELECT id FROM users WHERE username = ? AND id != ?", (username, user_id)
            ).fetchone()
            if exists:
                raise ValueError(f"Tên đăng nhập '{username}' đã tồn tại")

            if password.strip():
                connection.execute(
                    "UPDATE users SET username = ?, password = ?, full_name = ?, role = ? WHERE id = ?",
                    (username, password.strip(), full_name, role, user_id),
                )
            else:
                connection.execute(
                    "UPDATE users SET username = ?, full_name = ?, role = ? WHERE id = ?",
                    (username, full_name, role, user_id),
                )
            
            self._write_audit_log(
                connection,
                user_id=actor_user_id,
                action="UPDATE_USER",
                target_type="user",
                target_id=str(user_id),
                target_label=f"{username} ({full_name})",
                details=f"Cập nhật thông tin người dùng (Vai trò: {role})",
            )
            connection.commit()

    def delete_user(self, user_id: int, actor_user_id: int | None = None) -> None:
        if user_id == actor_user_id:
            raise ValueError("Không thể tự xóa chính mình")

        with self.database.connect() as connection:
            user = connection.execute("SELECT username, full_name FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user:
                raise ValueError("Không tìm thấy người dùng để xóa")
            
            # Kiểm tra xem user có đang gán làm captain cho chuyến nào không
            used = connection.execute("SELECT id FROM trips WHERE captain_id = ? LIMIT 1", (user_id,)).fetchone()
            if used:
                raise ValueError("Không thể xóa người dùng đang được gán làm Trưởng tàu cho chuyến đi")

            connection.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            self._write_audit_log(
                connection,
                user_id=actor_user_id,
                action="DELETE_USER",
                target_type="user",
                target_id=str(user_id),
                target_label=f"{user['username']} ({user['full_name']})",
                details="Xóa người dùng khỏi hệ thống",
            )
            connection.commit()


    def get_dashboard(self) -> dict[str, float | int]:
        with self.database.connect() as connection:
            trip_rows = connection.execute(
                """
                SELECT
                    trips.trip_code,
                    trips.status,
                    seat_stats.available_count,
                    seat_stats.total_count
                FROM trips
                JOIN (
                    SELECT
                        carriage_trips.trip_id,
                        SUM(
                            CASE
                                WHEN EXISTS (
                                    SELECT 1
                                    FROM tickets
                                    WHERE tickets.trip_seat_id = trip_seats.id
                                      AND tickets.status != 'cancelled'
                                ) THEN 0
                                ELSE 1
                            END
                        ) AS available_count,
                        COUNT(trip_seats.id) AS total_count
                    FROM carriage_trips
                    JOIN trip_seats ON trip_seats.carriage_trip_id = carriage_trips.id
                    GROUP BY carriage_trips.trip_id
                ) AS seat_stats ON seat_stats.trip_id = trips.id
                GROUP BY trips.id, trips.trip_code, trips.status, seat_stats.available_count, seat_stats.total_count
                """
            ).fetchall()
            ticket_rows = connection.execute("SELECT price, status, booked_at FROM tickets").fetchall()

        total_capacity = np.array([row["total_count"] or 0 for row in trip_rows], dtype=np.float64)
        available_capacity = np.array([row["available_count"] or 0 for row in trip_rows], dtype=np.float64)
        sold_capacity = total_capacity - available_capacity
        occupancy_rate = float(np.round((sold_capacity.sum() / total_capacity.sum()) * 100, 2)) if total_capacity.size and total_capacity.sum() else 0.0
        ticket_prices = np.array(
            [row["price"] for row in ticket_rows if row["status"] != "cancelled"],
            dtype=np.float64,
        )
        revenue_by_month: dict[str, float] = {}
        for row in ticket_rows:
            if row["status"] == "cancelled":
                continue
            month_key = str(datetime.now().strftime("%Y-%m"))
            if "booked_at" in row and row["booked_at"]:
                month_key = str(row["booked_at"])[:7]
            revenue_by_month[month_key] = revenue_by_month.get(month_key, 0.0) + float(row["price"])

        occupancy_by_trip = [
            {
                "label": str(row["trip_code"]),
                "occupancy_rate": round(
                    ((float(row["total_count"] or 0) - float(row["available_count"] or 0)) / float(row["total_count"] or 1)) * 100,
                    2,
                ) if float(row["total_count"] or 0) else 0.0,
            }
            for row in trip_rows
        ]
        return {
            "tickets_sold": int(ticket_prices.size),
            "revenue": float(ticket_prices.sum()) if ticket_prices.size else 0.0,
            "active_trips": int(sum(1 for row in trip_rows if row["status"] in {"open", "Đang bán"})),
            "cancelled_tickets": int(sum(1 for row in ticket_rows if row["status"] == "cancelled")),
            "occupancy_rate": occupancy_rate,
            "revenue_by_month": [
                {"label": month, "value": round(value, 2)}
                for month, value in sorted(revenue_by_month.items())
            ],
            "occupancy_by_trip": occupancy_by_trip[:8],
        }

    def search_trips(self, origin: str, destination: str, travel_date: str) -> list[dict[str, Any]]:
        pattern_origin = f"%{origin.strip()}%"
        pattern_destination = f"%{destination.strip()}%"
        pattern_date = f"%{travel_date.strip()}%"
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    trips.id,
                    trips.trip_code,
                    trains.code AS train_code,
                    origin_station.name AS origin_name,
                    destination_station.name AS destination_name,
                    trips.departure_date,
                    origin_stop.departure_time AS departure_time,
                    COALESCE(destination_stop.arrival_time, destination_stop.departure_time) AS arrival_time,
                    (destination_stop.distance_km - origin_stop.distance_km) AS segment_distance,
                    ABS(destination_stop.distance_km - origin_stop.distance_km) * 1000 AS segment_base_price_raw,
                    origin_stop.id AS boarding_station_trip_id,
                    destination_stop.id AS alighting_station_trip_id,
                    SUM(
                        CASE
                            WHEN NOT EXISTS (
                                SELECT 1
                                FROM tickets
                                JOIN station_trips AS booked_origin
                                    ON booked_origin.id = tickets.boarding_station_trip_id
                                JOIN station_trips AS booked_destination
                                    ON booked_destination.id = tickets.alighting_station_trip_id
                                WHERE tickets.trip_seat_id = trip_seats.id
                                  AND tickets.status != 'cancelled'
                                  AND booked_origin.stop_order < destination_stop.stop_order
                                  AND booked_destination.stop_order > origin_stop.stop_order
                            ) THEN 1
                            ELSE 0
                        END
                    ) AS available_seats
                FROM trips
                JOIN trains ON trains.id = trips.train_id
                JOIN station_trips AS origin_stop ON origin_stop.trip_id = trips.id
                JOIN stations AS origin_station ON origin_station.id = origin_stop.station_id
                JOIN station_trips AS destination_stop ON destination_stop.trip_id = trips.id
                JOIN stations AS destination_station ON destination_station.id = destination_stop.station_id
                JOIN carriage_trips ON carriage_trips.trip_id = trips.id
                JOIN trip_seats ON trip_seats.carriage_trip_id = carriage_trips.id
                WHERE (
                        origin_station.city LIKE ?
                     OR origin_station.name LIKE ?
                     OR origin_station.code LIKE ?
                )
                  AND (
                        destination_station.city LIKE ?
                     OR destination_station.name LIKE ?
                     OR destination_station.code LIKE ?
                  )
                  AND trips.departure_date LIKE ?
                  AND origin_stop.stop_order < destination_stop.stop_order
                  AND trips.status IN ('open', 'Đang bán')
                GROUP BY trips.id, origin_stop.id, destination_stop.id
                HAVING available_seats > 0
                ORDER BY trips.departure_date, departure_time
                """,
                (
                    pattern_origin,
                    pattern_origin,
                    pattern_origin,
                    pattern_destination,
                    pattern_destination,
                    pattern_destination,
                    pattern_date,
                ),
            ).fetchall()
        
        results = []
        for row in rows:
            d = dict(row)
            # Round segment price to nearest 1000
            d["segment_base_price"] = round(d["segment_base_price_raw"] / 1000) * 1000
            # Override base_price with segment price for dynamic display
            d["base_price"] = d["segment_base_price"]
            results.append(d)
        return results

    def get_trip_carriages(
        self,
        trip_id: int,
        boarding_station_trip_id: int | None = None,
        alighting_station_trip_id: int | None = None,
    ) -> dict[str, Any]:
        with self.database.connect() as connection:
            trip = connection.execute(
                """
                SELECT
                    trips.id,
                    trips.trip_code,
                    trains.code AS train_code,
                    trips.departure_date,
                    trips.status,
                    origin_station.name AS origin_name,
                    destination_station.name AS destination_name,
                    origin_stop.departure_time AS departure_time,
                    COALESCE(destination_stop.arrival_time, destination_stop.departure_time) AS arrival_time
                FROM trips
                JOIN trains ON trains.id = trips.train_id
                JOIN station_trips AS origin_stop
                    ON origin_stop.id = (
                        SELECT st.id
                        FROM station_trips AS st
                        WHERE st.trip_id = trips.id
                        ORDER BY st.stop_order
                        LIMIT 1
                    )
                JOIN stations AS origin_station ON origin_station.id = origin_stop.station_id
                JOIN station_trips AS destination_stop
                    ON destination_stop.id = (
                        SELECT st.id
                        FROM station_trips AS st
                        WHERE st.trip_id = trips.id
                        ORDER BY st.stop_order DESC
                        LIMIT 1
                    )
                JOIN stations AS destination_station ON destination_station.id = destination_stop.station_id
                WHERE trips.id = ?
                """,
                (trip_id,),
            ).fetchone()
            if not trip:
                raise ValueError("Không tìm thấy chuyến tàu")
            boarding_station_trip_id, alighting_station_trip_id = self._resolve_segment_ids(
                connection,
                trip_id,
                boarding_station_trip_id,
                alighting_station_trip_id,
            )
            boarding_order, alighting_order = self._get_segment_orders(
                connection,
                boarding_station_trip_id,
                alighting_station_trip_id,
            )

            itinerary = connection.execute(
                """
                SELECT
                    station_trips.id,
                    stations.code AS station_code,
                    stations.name AS station_name,
                    stations.city,
                    station_trips.stop_order,
                    station_trips.arrival_time,
                    station_trips.departure_time
                FROM station_trips
                JOIN stations ON stations.id = station_trips.station_id
                WHERE station_trips.trip_id = ?
                ORDER BY station_trips.stop_order
                """,
                (trip_id,),
            ).fetchall()
            carriages = connection.execute(
                """
                SELECT
                    carriage_trips.id,
                    carriage_trips.carriage_order,
                    carriages.carriage_code,
                    carriages.seat_type,
                    carriages.seat_count,
                    SUM(
                        CASE
                            WHEN NOT EXISTS (
                                SELECT 1
                                FROM tickets
                                JOIN station_trips AS booked_origin
                                    ON booked_origin.id = tickets.boarding_station_trip_id
                                JOIN station_trips AS booked_destination
                                    ON booked_destination.id = tickets.alighting_station_trip_id
                                WHERE tickets.trip_seat_id = trip_seats.id
                                  AND tickets.status != 'cancelled'
                                  AND booked_origin.stop_order < ?
                                  AND booked_destination.stop_order > ?
                            ) THEN 1
                            ELSE 0
                        END
                    ) AS available_seats,
                    COUNT(trip_seats.id) AS total_seats
                FROM carriage_trips
                JOIN carriages ON carriages.id = carriage_trips.carriage_id
                LEFT JOIN trip_seats ON trip_seats.carriage_trip_id = carriage_trips.id
                WHERE carriage_trips.trip_id = ?
                GROUP BY carriage_trips.id
                ORDER BY carriage_trips.carriage_order
                """,
                (alighting_order, boarding_order, trip_id),
            ).fetchall()

        return {
            "trip": dict(trip),
            "itinerary": [dict(row) for row in itinerary],
            "carriages": [dict(row) for row in carriages],
        }

    def get_carriage_seats(
        self,
        carriage_trip_id: int,
        boarding_station_trip_id: int | None = None,
        alighting_station_trip_id: int | None = None,
    ) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            carriage_trip = connection.execute(
                "SELECT trip_id FROM carriage_trips WHERE id = ?",
                (carriage_trip_id,),
            ).fetchone()
            if not carriage_trip:
                raise ValueError("Không tìm thấy toa của chuyến")
            boarding_station_trip_id, alighting_station_trip_id = self._resolve_segment_ids(
                connection,
                int(carriage_trip["trip_id"]),
                boarding_station_trip_id,
                alighting_station_trip_id,
            )
            boarding_order, alighting_order = self._get_segment_orders(
                connection,
                boarding_station_trip_id,
                alighting_station_trip_id,
            )
            
            # Fetch distances for price calculation
            boarding_dist = connection.execute(
                "SELECT distance_km FROM station_trips WHERE id = ?", (boarding_station_trip_id,)
            ).fetchone()["distance_km"]
            alighting_dist = connection.execute(
                "SELECT distance_km FROM station_trips WHERE id = ?", (alighting_station_trip_id,)
            ).fetchone()["distance_km"]
            segment_distance = abs(float(alighting_dist) - float(boarding_dist))
            
            rows = connection.execute(
                """
                SELECT
                    trip_seats.id,
                    trip_seats.carriage_trip_id,
                    carriages.carriage_code,
                    trip_seats.seat_code,
                    trip_seats.seat_type,
                    trip_seats.seat_price,
                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM tickets
                            JOIN station_trips AS booked_origin
                                ON booked_origin.id = tickets.boarding_station_trip_id
                            JOIN station_trips AS booked_destination
                                ON booked_destination.id = tickets.alighting_station_trip_id
                            WHERE tickets.trip_seat_id = trip_seats.id
                              AND tickets.status != 'cancelled'
                              AND booked_origin.stop_order < ?
                              AND booked_destination.stop_order > ?
                        ) THEN 'booked'
                        ELSE 'available'
                    END AS status
                FROM trip_seats
                JOIN carriage_trips ON carriage_trips.id = trip_seats.carriage_trip_id
                JOIN carriages ON carriages.id = carriage_trips.carriage_id
                WHERE trip_seats.carriage_trip_id = ?
                ORDER BY trip_seats.seat_code
                """,
                (alighting_order, boarding_order, carriage_trip_id),
            ).fetchall()
            
            results = []
            for row in rows:
                d = dict(row)
                # Recalculate seat price based on segment distance
                multiplier = self._seat_multiplier(str(d["seat_type"]))
                d["seat_price"] = round(segment_distance * 1000 * multiplier / 1000) * 1000
                results.append(d)
            return results

    def create_booking(
        self,
        user_id: int,
        trip_id: int,
        seat_id: int,
        boarding_station_trip_id: int,
        alighting_station_trip_id: int,
        full_name: str,
        id_number: str,
        phone: str,
    ) -> dict[str, Any]:
        full_name = full_name.strip()
        id_number = id_number.strip()
        phone = phone.strip()

        if not full_name or not id_number or not phone:
            raise ValueError("Vui lòng nhập đầy đủ họ tên, CCCD và số điện thoại")
        
        if not id_number.isdigit():
            raise ValueError("Số CCCD không hợp lệ (chỉ được chứa chữ số). Vui lòng nhập lại.")
        if len(id_number) != 12:
            raise ValueError("Số CCCD phải có đúng 12 chữ số. Vui lòng kiểm tra lại.")
            
        if not phone.isdigit():
            raise ValueError("Số điện thoại không hợp lệ (chỉ được chứa chữ số). Vui lòng nhập lại.")
        if len(phone) != 10:
            raise ValueError("Số điện thoại phải có đúng 10 chữ số. Vui lòng kiểm tra lại.")
        if not phone.startswith("0"):
            raise ValueError("Số điện thoại không hợp lệ (phải bắt đầu bằng số 0). Vui lòng nhập lại.")

        with self.database.connect() as connection:
            seat = connection.execute(
                """
                SELECT
                    trip_seats.id,
                    trip_seats.status,
                    trip_seats.seat_price,
                    trip_seats.seat_type,
                    carriages.carriage_code,
                    trip_seats.seat_code,
                    carriage_trips.trip_id
                FROM trip_seats
                JOIN carriage_trips ON carriage_trips.id = trip_seats.carriage_trip_id
                JOIN carriages ON carriages.id = carriage_trips.carriage_id
                WHERE trip_seats.id = ?
                """,
                (seat_id,),
            ).fetchone()
            if not seat or int(seat["trip_id"]) != trip_id:
                raise ValueError("Không tìm thấy ghế thuộc chuyến đã chọn")

            boarding = connection.execute(
                "SELECT trip_id, stop_order FROM station_trips WHERE id = ?",
                (boarding_station_trip_id,),
            ).fetchone()
            alighting = connection.execute(
                "SELECT trip_id, stop_order FROM station_trips WHERE id = ?",
                (alighting_station_trip_id,),
            ).fetchone()
            if not boarding or not alighting:
                raise ValueError("Thiếu thông tin ga lên/xuống")
            if int(boarding["trip_id"]) != trip_id or int(alighting["trip_id"]) != trip_id:
                raise ValueError("Ga lên/xuống không thuộc chuyến đã chọn")
            if int(boarding["stop_order"]) >= int(alighting["stop_order"]):
                raise ValueError("Ga xuống phải nằm sau ga lên trên hành trình")
            
            # Distance-based pricing with COALESCE for safety
            boarding_dist_row = connection.execute(
                "SELECT COALESCE(distance_km, 0) AS distance_km FROM station_trips WHERE id = ?", (boarding_station_trip_id,)
            ).fetchone()
            alighting_dist_row = connection.execute(
                "SELECT COALESCE(distance_km, 0) AS distance_km FROM station_trips WHERE id = ?", (alighting_station_trip_id,)
            ).fetchone()
            
            boarding_dist = float(boarding_dist_row["distance_km"] if boarding_dist_row else 0)
            alighting_dist = float(alighting_dist_row["distance_km"] if alighting_dist_row else 0)
            
            # Check for custom fare in station_trips
            custom_fare_row = connection.execute(
                "SELECT custom_fare FROM station_trips WHERE id = ?", (alighting_station_trip_id,)
            ).fetchone()
            
            if custom_fare_row and custom_fare_row["custom_fare"] is not None:
                # If a custom fare is set for the destination station, we use it as the base for origin-to-destination
                # (Assuming custom_fare in station_trips is the fare from trip origin to that station)
                # To get segment price: custom_fare(alighting) - custom_fare(boarding)
                boarding_custom_row = connection.execute(
                    "SELECT custom_fare FROM station_trips WHERE id = ?", (boarding_station_trip_id,)
                ).fetchone()
                
                b_fare = float(boarding_custom_row["custom_fare"] or 0)
                a_fare = float(custom_fare_row["custom_fare"] or 0)
                
                if a_fare > b_fare:
                    base_segment_price = a_fare - b_fare
                else:
                    # Fallback to distance if custom fares are not logical
                    segment_distance = abs(alighting_dist - boarding_dist) or 100.0
                    base_segment_price = segment_distance * 1000
            else:
                segment_distance = abs(alighting_dist - boarding_dist)
                # Fallback if distance is 0 but it's a valid segment (e.g. seeded data without distances)
                if segment_distance <= 0:
                    segment_distance = 100.0 # Default fallback distance
                base_segment_price = segment_distance * 1000

            multiplier = self._seat_multiplier(str(seat["seat_type"]))
            final_price = round(base_segment_price * multiplier / 1000) * 1000

            conflict = connection.execute(
                """
                SELECT tickets.id
                FROM tickets
                JOIN station_trips AS booked_origin
                    ON booked_origin.id = tickets.boarding_station_trip_id
                JOIN station_trips AS booked_destination
                    ON booked_destination.id = tickets.alighting_station_trip_id
                WHERE tickets.trip_seat_id = ?
                  AND tickets.status != 'cancelled'
                  AND booked_origin.stop_order < ?
                  AND booked_destination.stop_order > ?
                LIMIT 1
                """,
                (seat_id, int(alighting["stop_order"]), int(boarding["stop_order"])),
            ).fetchone()
            if conflict:
                raise ValueError("Ghế này đã được đặt ở chặng bị trùng")

            passenger = connection.execute(
                "SELECT id FROM passengers WHERE id_number = ?",
                (id_number.strip(),),
            ).fetchone()
            if passenger:
                passenger_id = int(passenger["id"])
                connection.execute(
                    """
                    UPDATE passengers
                    SET full_name = ?, phone = ?
                    WHERE id = ?
                    """,
                    (full_name.strip(), phone.strip(), passenger_id),
                )
            else:
                passenger_id = int(
                    connection.execute(
                        """
                        INSERT INTO passengers (full_name, id_number, phone)
                        VALUES (?, ?, ?)
                        """,
                        (full_name.strip(), id_number.strip(), phone.strip()),
                    ).lastrowid
                )

            ticket_code = f"VE{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            connection.execute(
                """
                INSERT INTO tickets (
                    ticket_code,
                    passenger_id,
                    trip_id,
                    trip_seat_id,
                    boarding_station_trip_id,
                    alighting_station_trip_id,
                    booked_by,
                    price,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'booked')
                """,
                (
                    ticket_code,
                    passenger_id,
                    trip_id,
                    seat_id,
                    boarding_station_trip_id,
                    alighting_station_trip_id,
                    user_id,
                    final_price,
                ),
            )
            self._refresh_trip_seat_status(connection, seat_id)
            self._write_audit_log(
                connection,
                user_id=user_id,
                action="CREATE_TICKET",
                target_id=ticket_code,
                target_label=ticket_code,
                target_type="ticket",
                details=f"Đặt chỗ {seat['carriage_code']}-{seat['seat_code']} cho {full_name.strip()} (Giá: {final_price})",
            )
            connection.commit()

        return {
            "ticket_code": ticket_code,
            "seat_label": f"{seat['carriage_code']}-{seat['seat_code']}",
            "price": float(final_price),
        }

    def get_route_stations(self, route_id: int) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT 
                    stations.id, 
                    stations.code, 
                    stations.name, 
                    stations.city,
                    route_stations.stop_order,
                    route_stations.distance_km
                FROM route_stations
                JOIN stations ON stations.id = route_stations.station_id
                WHERE route_stations.route_id = ?
                ORDER BY route_stations.stop_order
                """,
                (route_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_ticket_detail(self, ticket_code: str) -> dict[str, Any] | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    tickets.ticket_code,
                    passengers.full_name,
                    passengers.id_number,
                    passengers.phone,
                    trips.trip_code,
                    trains.code AS train_code,
                    boarding_station.name AS boarding_name,
                    alighting_station.name AS alighting_name,
                    carriages.carriage_code,
                    trip_seats.seat_code,
                    trip_seats.seat_type,
                    tickets.price,
                    tickets.status,
                    tickets.booked_at,
                    trips.departure_date,
                    boarding_stop.departure_time,
                    alighting_stop.arrival_time
                FROM tickets
                JOIN passengers ON passengers.id = tickets.passenger_id
                JOIN trips ON trips.id = tickets.trip_id
                JOIN trains ON trains.id = trips.train_id
                JOIN trip_seats ON trip_seats.id = tickets.trip_seat_id
                JOIN carriage_trips ON carriage_trips.id = trip_seats.carriage_trip_id
                JOIN carriages ON carriages.id = carriage_trips.carriage_id
                JOIN station_trips AS boarding_stop ON boarding_stop.id = tickets.boarding_station_trip_id
                JOIN stations AS boarding_station ON boarding_station.id = boarding_stop.station_id
                JOIN station_trips AS alighting_stop ON alighting_stop.id = tickets.alighting_station_trip_id
                JOIN stations AS alighting_station ON alighting_station.id = alighting_stop.station_id
                WHERE tickets.ticket_code = ?
                """,
                (ticket_code,),
            ).fetchone()
            return dict(row) if row else None

    def search_tickets(self, query: str) -> list[dict[str, Any]]:
        pattern = f"%{query.strip()}%"
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
                    boarding_station.name AS boarding_name,
                    alighting_station.name AS alighting_name,
                    carriages.carriage_code,
                    trip_seats.seat_code,
                    tickets.price,
                    tickets.status,
                    tickets.booked_at,
                    tickets.booked_by AS booked_by_id,
                    booker.username AS booked_by_username,
                    booker.full_name AS booked_by_name
                FROM tickets
                JOIN passengers ON passengers.id = tickets.passenger_id
                JOIN trips ON trips.id = tickets.trip_id
                JOIN trains ON trains.id = trips.train_id
                JOIN trip_seats ON trip_seats.id = tickets.trip_seat_id
                JOIN carriage_trips ON carriage_trips.id = trip_seats.carriage_trip_id
                JOIN carriages ON carriages.id = carriage_trips.carriage_id
                JOIN station_trips AS boarding_stop ON boarding_stop.id = tickets.boarding_station_trip_id
                JOIN stations AS boarding_station ON boarding_station.id = boarding_stop.station_id
                JOIN station_trips AS alighting_stop ON alighting_stop.id = tickets.alighting_station_trip_id
                JOIN stations AS alighting_station ON alighting_station.id = alighting_stop.station_id
                LEFT JOIN users AS booker ON booker.id = tickets.booked_by
                WHERE tickets.ticket_code LIKE ?
                   OR passengers.id_number LIKE ?
                   OR passengers.phone LIKE ?
                   OR passengers.full_name LIKE ?
                ORDER BY tickets.booked_at DESC
                """,
                (pattern, pattern, pattern, pattern),
            ).fetchall()
        return [dict(row) for row in rows]

    def cancel_ticket(self, ticket_code: str, actor_user_id: int | None = None) -> None:
        with self.database.connect() as connection:
            ticket = connection.execute(
                "SELECT id, trip_seat_id FROM tickets WHERE ticket_code = ?",
                (ticket_code.strip(),),
            ).fetchone()
            if not ticket:
                raise ValueError("Không tìm thấy vé")
            
            # Xóa vé hoàn toàn khỏi hệ thống
            connection.execute("DELETE FROM tickets WHERE id = ?", (ticket["id"],))
            self._refresh_trip_seat_status(connection, int(ticket["trip_seat_id"]))
            self._write_audit_log(
                connection,
                user_id=actor_user_id,
                action="CANCEL_TICKET",
                target_type="ticket",
                target_id=str(ticket["id"]),
                target_label=ticket_code.strip(),
                details="Hủy vé",
            )
            connection.commit()

    def get_schedules(self, date_filter: str | None = None) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            query = """
                SELECT
                    trips.id,
                    trips.trip_code,
                    trains.code AS train_code,
                    origin_station.name AS origin_name,
                    destination_station.name AS destination_name,
                    trips.departure_date,
                    trips.departure_time,
                    trips.arrival_time,
                    trips.status,
                    stop_stats.stop_count,
                    seat_stats.carriage_count,
                    seat_stats.available_seats,
                    seat_stats.total_seats
                FROM trips
                JOIN trains ON trains.id = trips.train_id
                JOIN station_trips AS origin_stop
                    ON origin_stop.id = (
                        SELECT st.id
                        FROM station_trips AS st
                        WHERE st.trip_id = trips.id
                        ORDER BY st.stop_order
                        LIMIT 1
                    )
                JOIN stations AS origin_station ON origin_station.id = origin_stop.station_id
                JOIN station_trips AS destination_stop
                    ON destination_stop.id = (
                        SELECT st.id
                        FROM station_trips AS st
                        WHERE st.trip_id = trips.id
                        ORDER BY st.stop_order DESC
                        LIMIT 1
                    )
                JOIN stations AS destination_station ON destination_station.id = destination_stop.station_id
                JOIN (
                    SELECT trip_id, COUNT(*) AS stop_count
                    FROM station_trips
                    GROUP BY trip_id
                ) AS stop_stats ON stop_stats.trip_id = trips.id
                JOIN (
                    SELECT
                        carriage_trips.trip_id,
                        COUNT(DISTINCT carriage_trips.id) AS carriage_count,
                        SUM(CASE WHEN trip_seats.status = 'available' THEN 1 ELSE 0 END) AS available_seats,
                        COUNT(trip_seats.id) AS total_seats
                    FROM carriage_trips
                    JOIN trip_seats ON trip_seats.carriage_trip_id = carriage_trips.id
                    GROUP BY carriage_trips.trip_id
                ) AS seat_stats ON seat_stats.trip_id = trips.id
                WHERE 1=1
            """
            params = []
            if date_filter:
                query += " AND trips.departure_date = ?"
                params.append(date_filter)
            
            query += " ORDER BY trips.departure_date DESC, trips.departure_time DESC"
            rows = connection.execute(query, params).fetchall()
            
            results = []
            now = datetime.now()
            for row in rows:
                d = dict(row)
                # Tính toán trạng thái thực tế dựa trên thời gian
                if d["status"] == "cancelled":
                    d["status_label"] = "Đã hủy"
                elif d["status"] == "draft":
                    d["status_label"] = "Bản nháp"
                else:
                    try:
                        dep_dt = datetime.strptime(f"{d['departure_date']} {d['departure_time']}", "%Y-%m-%d %H:%M")
                        arr_dt = datetime.strptime(f"{d['departure_date']} {d['arrival_time']}", "%Y-%m-%d %H:%M")
                        if arr_dt < dep_dt: # Tàu chạy qua đêm
                            arr_dt += timedelta(days=1)
                        
                        if now < dep_dt:
                            d["status_label"] = "Chưa chạy"
                        elif dep_dt <= now <= arr_dt:
                            d["status_label"] = "Đang chạy"
                        else:
                            d["status_label"] = "Đã hoàn thành"
                    except:
                        d["status_label"] = d["status"]
                results.append(d)
        return results

    def get_schedule_detail(self, trip_id: int) -> dict[str, Any]:
        with self.database.connect() as connection:
            trip = connection.execute(
                """
                SELECT
                    trips.id,
                    trips.trip_code,
                    trains.code AS train_code,
                    trains.name AS train_name,
                    trips.departure_date,
                    trips.departure_time,
                    trips.arrival_time,
                    trips.base_price,
                    trips.status
                FROM trips
                JOIN trains ON trains.id = trips.train_id
                WHERE trips.id = ?
                """,
                (trip_id,),
            ).fetchone()
            if not trip:
                raise ValueError("Không tìm thấy lịch trình")

            stops = connection.execute(
                """
                SELECT
                    station_trips.id,
                    station_trips.trip_id,
                    station_trips.station_id,
                    station_trips.stop_order,
                    station_trips.arrival_time,
                    station_trips.departure_time,
                    stations.code AS station_code,
                    stations.name AS station_name,
                    stations.city
                FROM station_trips
                JOIN stations ON stations.id = station_trips.station_id
                WHERE station_trips.trip_id = ?
                ORDER BY station_trips.stop_order
                """,
                (trip_id,),
            ).fetchall()

        stop_rows = [dict(row) for row in stops]
        for index, stop in enumerate(stop_rows):
            if stop["arrival_time"] and stop["departure_time"]:
                arrival_dt = datetime.strptime(str(stop["arrival_time"]), "%H:%M")
                departure_dt = datetime.strptime(str(stop["departure_time"]), "%H:%M")
                if departure_dt < arrival_dt:
                    departure_dt += timedelta(days=1)
                stop["dwell_minutes"] = int((departure_dt - arrival_dt).total_seconds() // 60)
            else:
                stop["dwell_minutes"] = 0
            stop["role_name"] = (
                "Ga đầu" if index == 0 else "Ga cuối" if index == len(stop_rows) - 1 else "Ga trung gian"
            )
        return {"trip": dict(trip), "stops": stop_rows}

    def get_train_templates(self) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    train_templates.id,
                    train_templates.name,
                    train_templates.description,
                    train_template_items.item_order,
                    carriages.id AS carriage_id,
                    carriages.carriage_code,
                    carriages.seat_type,
                    carriages.seat_count
                FROM train_templates
                LEFT JOIN train_template_items ON train_template_items.template_id = train_templates.id
                LEFT JOIN carriages ON carriages.id = train_template_items.carriage_id
                ORDER BY train_templates.name, train_template_items.item_order
                """
            ).fetchall()
        templates: dict[int, dict[str, Any]] = {}
        for row in rows:
            template_id = int(row["id"])
            if template_id not in templates:
                templates[template_id] = {
                    "id": template_id,
                    "name": row["name"],
                    "description": row["description"] or "",
                    "carriages": [],
                }
            if row["carriage_id"]:
                templates[template_id]["carriages"].append(
                    {
                        "id": int(row["carriage_id"]),
                        "carriage_code": row["carriage_code"],
                        "seat_type": row["seat_type"],
                        "seat_count": row["seat_count"],
                    }
                )
        return list(templates.values())

    def create_train_template(
        self,
        name: str,
        description: str,
        carriage_ids: list[int],
        actor_user_id: int | None = None,
    ) -> None:
        if not name.strip():
            raise ValueError("Tên mẫu đoàn tàu không được để trống")
        if not carriage_ids:
            raise ValueError("Mẫu đoàn tàu phải có ít nhất 1 toa")
        with self.database.connect() as connection:
            template_id = connection.execute(
                "INSERT INTO train_templates (name, description) VALUES (?, ?)",
                (name.strip(), description.strip()),
            ).lastrowid
            connection.executemany(
                """
                INSERT INTO train_template_items (template_id, carriage_id, item_order)
                VALUES (?, ?, ?)
                """,
                [(int(template_id), carriage_id, order) for order, carriage_id in enumerate(carriage_ids, start=1)],
            )
            self._write_audit_log(
                connection,
                user_id=actor_user_id,
                action="CREATE_TEMPLATE",
                target_type="train_template",
                target_id=str(template_id),
                target_label=name.strip(),
                details=f"{len(carriage_ids)} toa",
            )
            connection.commit()

    def delete_train_template(self, template_id: int, actor_user_id: int | None = None) -> None:
        with self.database.connect() as connection:
            template = connection.execute(
                "SELECT id, name FROM train_templates WHERE id = ?",
                (template_id,),
            ).fetchone()
            if not template:
                raise ValueError("Không tìm thấy mẫu đoàn tàu")
            connection.execute("DELETE FROM train_template_items WHERE template_id = ?", (template_id,))
            connection.execute("DELETE FROM train_templates WHERE id = ?", (template_id,))
            self._write_audit_log(
                connection,
                user_id=actor_user_id,
                action="DELETE_TEMPLATE",
                target_type="train_template",
                target_id=str(template_id),
                target_label=str(template["name"]),
                details="Xóa mẫu đoàn tàu",
            )
            connection.commit()

    def get_audit_logs(self, query: str = "") -> list[dict[str, Any]]:
        pattern = f"%{query.strip()}%"
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    audit_logs.id,
                    audit_logs.action,
                    audit_logs.target_type,
                    audit_logs.target_id,
                    audit_logs.target_label,
                    audit_logs.details,
                    audit_logs.created_at,
                    users.username,
                    users.full_name
                FROM audit_logs
                LEFT JOIN users ON users.id = audit_logs.user_id
                WHERE audit_logs.action LIKE ?
                   OR audit_logs.target_type LIKE ?
                   OR audit_logs.target_label LIKE ?
                   OR COALESCE(users.username, '') LIKE ?
                   OR COALESCE(users.full_name, '') LIKE ?
                ORDER BY audit_logs.created_at DESC, audit_logs.id DESC
                """,
                (pattern, pattern, pattern, pattern, pattern),
            ).fetchall()
        return [dict(row) for row in rows]

    def add_station(self, code: str, name: str, city: str, actor_user_id: int | None = None) -> None:
        if not code.strip() or not name.strip() or not city.strip():
            raise ValueError("Vui lòng nhập đủ mã ga, tên ga và thành phố")
        with self.database.connect() as connection:
            station_id = connection.execute(
                "INSERT INTO stations (code, name, city) VALUES (?, ?, ?)",
                (code.strip().upper(), name.strip(), city.strip()),
            ).lastrowid
            self._write_audit_log(
                connection,
                user_id=actor_user_id,
                action="CREATE_STATION",
                target_type="station",
                target_id=str(station_id),
                target_label=f"{code.strip().upper()} - {name.strip()}",
                details=city.strip(),
            )
            connection.commit()

    def delete_station(self, station_id: int, actor_user_id: int | None = None) -> None:
        with self.database.connect() as connection:
            station = connection.execute(
                "SELECT code, name FROM stations WHERE id = ?",
                (station_id,),
            ).fetchone()
            used = connection.execute(
                "SELECT id FROM station_trips WHERE station_id = ? LIMIT 1",
                (station_id,),
            ).fetchone()
            if used:
                raise ValueError("Không thể xóa ga đang được dùng trong hành trình")
            connection.execute("DELETE FROM stations WHERE id = ?", (station_id,))
            if station:
                self._write_audit_log(
                    connection,
                    user_id=actor_user_id,
                    action="DELETE_STATION",
                    target_type="station",
                    target_id=str(station_id),
                    target_label=f"{station['code']} - {station['name']}",
                    details="Xóa ga",
                )
            connection.commit()

    def add_train(self, code: str, name: str, actor_user_id: int | None = None) -> None:
        if not code.strip() or not name.strip():
            raise ValueError("Vui lòng nhập đủ mã tàu và tên tàu")
        with self.database.connect() as connection:
            train_id = connection.execute(
                "INSERT INTO trains (code, name) VALUES (?, ?)",
                (code.strip().upper(), name.strip()),
            ).lastrowid
            self._write_audit_log(
                connection,
                user_id=actor_user_id,
                action="CREATE_TRAIN",
                target_type="train",
                target_id=str(train_id),
                target_label=f"{code.strip().upper()} - {name.strip()}",
                details="Thêm tàu",
            )
            connection.commit()

    def delete_train(self, train_id: int, actor_user_id: int | None = None) -> None:
        with self.database.connect() as connection:
            train = connection.execute("SELECT code, name FROM trains WHERE id = ?", (train_id,)).fetchone()
            used = connection.execute(
                "SELECT id FROM trips WHERE train_id = ? LIMIT 1",
                (train_id,),
            ).fetchone()
            if used:
                raise ValueError("Không thể xóa tàu đang có chuyến")
            connection.execute("DELETE FROM trains WHERE id = ?", (train_id,))
            if train:
                self._write_audit_log(
                    connection,
                    user_id=actor_user_id,
                    action="DELETE_TRAIN",
                    target_type="train",
                    target_id=str(train_id),
                    target_label=f"{train['code']} - {train['name']}",
                    details="Xóa tàu",
                )
            connection.commit()

    def add_carriage(
        self,
        carriage_code: str,
        seat_type: str,
        seat_count: int,
        actor_user_id: int | None = None,
    ) -> None:
        if not carriage_code.strip() or not seat_type.strip() or seat_count <= 0:
            raise ValueError("Thông tin toa tàu không hợp lệ")
        with self.database.connect() as connection:
            carriage_id = connection.execute(
                """
                INSERT INTO carriages (carriage_code, seat_type, seat_count)
                VALUES (?, ?, ?)
                """,
                (carriage_code.strip().upper(), seat_type.strip(), seat_count),
            ).lastrowid
            self._write_audit_log(
                connection,
                user_id=actor_user_id,
                action="CREATE_CARRIAGE",
                target_type="carriage",
                target_id=str(carriage_id),
                target_label=f"{carriage_code.strip().upper()} - {seat_type.strip()}",
                details=f"{seat_count} ghế",
            )
            connection.commit()

    def delete_carriage(self, carriage_id: int, actor_user_id: int | None = None) -> None:
        with self.database.connect() as connection:
            carriage = connection.execute(
                "SELECT carriage_code, seat_type FROM carriages WHERE id = ?",
                (carriage_id,),
            ).fetchone()
            used = connection.execute(
                "SELECT id FROM carriage_trips WHERE carriage_id = ? LIMIT 1",
                (carriage_id,),
            ).fetchone()
            if used:
                raise ValueError("Không thể xóa toa đang được gán cho chuyến")
            connection.execute("DELETE FROM carriages WHERE id = ?", (carriage_id,))
            if carriage:
                self._write_audit_log(
                    connection,
                    user_id=actor_user_id,
                    action="DELETE_CARRIAGE",
                    target_type="carriage",
                    target_id=str(carriage_id),
                    target_label=f"{carriage['carriage_code']} - {carriage['seat_type']}",
                    details="Xóa toa",
                )
            connection.commit()

    def create_trip(
        self,
        *,
        train_id: int,
        trip_code: str,
        train_type: str | None = None,
        captain_id: int | None = None,
        crew_code: str | None = None,
        departure_date: str,
        base_price: float,
        status: str,
        stops: list[dict[str, Any]],
        carriage_ids: list[int],
        actor_user_id: int | None = None,
    ) -> dict[str, Any]:
        with self.database.connect() as connection:
            # 1. Insert Trip
            trip_id = connection.execute(
                """
                INSERT INTO trips (
                    train_id, trip_code, train_type, captain_id, crew_code,
                    departure_date, departure_time, arrival_time, base_price, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    train_id, trip_code.strip().upper(), train_type, captain_id, crew_code,
                    departure_date, stops[0]["departure_time"], stops[-1]["arrival_time"],
                    base_price, status
                ),
            ).lastrowid

            # 2. Insert Station Stops
            for order, stop in enumerate(stops, start=1):
                connection.execute(
                    """
                    INSERT INTO station_trips (
                        trip_id, station_id, stop_order, is_pick_up, platform_code,
                        arrival_time, stop_duration_min, departure_time, day_offset, distance_km
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        trip_id, int(stop["station_id"]), order, int(stop.get("is_pick_up", 1)),
                        stop.get("platform_code", "Số 1"), stop.get("arrival_time"),
                        int(stop.get("stop_duration_min", 0)), stop.get("departure_time"),
                        int(stop.get("day_offset", 0)), float(stop.get("distance_km", 0))
                    ),
                )

            # 3. Insert Carriages & Seats
            for order, carriage_id in enumerate(carriage_ids, start=1):
                carriage_trip_id = connection.execute(
                    """
                    INSERT INTO carriage_trips (trip_id, carriage_id, carriage_order)
                    VALUES (?, ?, ?)
                    """,
                    (trip_id, carriage_id, order),
                ).lastrowid

                carriage = connection.execute(
                    "SELECT carriage_code, seat_type, seat_count FROM carriages WHERE id = ?",
                    (carriage_id,),
                ).fetchone()

                for seat_number in range(1, int(carriage["seat_count"]) + 1):
                    connection.execute(
                        """
                        INSERT INTO trip_seats (
                            carriage_trip_id, seat_code, seat_type, seat_price, status
                        ) VALUES (?, ?, ?, ?, 'available')
                        """,
                        (
                            carriage_trip_id,
                            f"{seat_number:02d}",
                            carriage["seat_type"],
                            round(base_price * self._seat_multiplier(str(carriage["seat_type"])) / 1000) * 1000,
                        ),
                    )

            # 4. Audit Log
            self._write_audit_log(
                connection,
                user_id=actor_user_id,
                action="CREATE_TRIP",
                target_type="trip",
                target_id=str(trip_id),
                target_label=trip_code.strip().upper(),
                details=f"{len(stops)} ga dừng, {len(carriage_ids)} toa",
            )
            connection.commit()
            return {"id": trip_id, "trip_code": trip_code}

    def delete_trip(self, trip_id: int, actor_user_id: int | None = None) -> None:
        # Giữ nguyên delete_trip để xóa hẳn
        with self.database.connect() as connection:
            trip = connection.execute(
                "SELECT trip_code FROM trips WHERE id = ?",
                (trip_id,),
            ).fetchone()
            connection.execute("DELETE FROM tickets WHERE trip_id = ?", (trip_id,))
            connection.execute("DELETE FROM trip_seats WHERE carriage_trip_id IN (SELECT id FROM carriage_trips WHERE trip_id = ?)", (trip_id,))
            connection.execute("DELETE FROM carriage_trips WHERE trip_id = ?", (trip_id,))
            connection.execute("DELETE FROM station_trips WHERE trip_id = ?", (trip_id,))
            connection.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
            if trip:
                self._write_audit_log(
                    connection,
                    user_id=actor_user_id,
                    action="DELETE_TRIP",
                    target_type="trip",
                    target_id=str(trip_id),
                    target_label=str(trip["trip_code"]),
                    details="Xóa chuyến hoàn toàn",
                )
            connection.commit()

    def cancel_trip_manual(self, trip_id: int, actor_user_id: int | None = None) -> None:
        with self.database.connect() as connection:
            trip = connection.execute(
                "SELECT trip_code FROM trips WHERE id = ?",
                (trip_id,),
            ).fetchone()
            if not trip:
                raise ValueError("Không tìm thấy chuyến")
            
            connection.execute("UPDATE trips SET status = 'cancelled' WHERE id = ?", (trip_id,))
            if trip:
                self._write_audit_log(
                    connection,
                    user_id=actor_user_id,
                    action="CANCEL_TRIP",
                    target_type="trip",
                    target_id=str(trip_id),
                    target_label=str(trip["trip_code"]),
                    details="Hủy chuyến do sự cố",
                )
            connection.commit()

    def add_trip_stop(
        self,
        *,
        trip_id: int,
        station_id: int,
        stop_order: int,
        arrival_time: str | None,
        departure_time: str | None,
        actor_user_id: int | None = None,
    ) -> None:
        with self.database.connect() as connection:
            self._ensure_trip_editable(connection, trip_id)
            stop_count = connection.execute(
                "SELECT COUNT(*) AS stop_count FROM station_trips WHERE trip_id = ?",
                (trip_id,),
            ).fetchone()
            max_order = int(stop_count["stop_count"] or 0) + 1
            normalized_order = max(1, min(stop_order, max_order))
            # Shift existing stops to avoid UNIQUE constraint conflict in SQLite
            connection.execute(
                """
                UPDATE station_trips
                SET stop_order = -(stop_order + 1)
                WHERE trip_id = ? AND stop_order >= ?
                """,
                (trip_id, normalized_order),
            )
            connection.execute(
                """
                UPDATE station_trips
                SET stop_order = -stop_order
                WHERE trip_id = ? AND stop_order < 0
                """,
                (trip_id,),
            )
            connection.execute(
                """
                INSERT INTO station_trips (trip_id, station_id, stop_order, arrival_time, departure_time)
                VALUES (?, ?, ?, ?, ?)
                """,
                (trip_id, station_id, normalized_order, arrival_time, departure_time),
            )
            self._normalize_trip_stops(connection, trip_id)
            station = connection.execute("SELECT code, name FROM stations WHERE id = ?", (station_id,)).fetchone()
            self._write_audit_log(
                connection,
                user_id=actor_user_id,
                action="CREATE_STOP",
                target_type="station_trip",
                target_id=f"{trip_id}:{normalized_order}",
                target_label=f"{station['code']} - {station['name']}" if station else str(station_id),
                details=f"Thêm điểm dừng vào chuyến {trip_id}",
            )
            connection.commit()

    def update_trip_stop(
        self,
        *,
        stop_id: int,
        station_id: int,
        stop_order: int,
        arrival_time: str | None,
        departure_time: str | None,
        actor_user_id: int | None = None,
    ) -> None:
        with self.database.connect() as connection:
            trip_stop = connection.execute(
                "SELECT trip_id, stop_order FROM station_trips WHERE id = ?",
                (stop_id,),
            ).fetchone()
            if not trip_stop:
                raise ValueError("Không tìm thấy điểm dừng")
            trip_id = int(trip_stop["trip_id"])
            current_order = int(trip_stop["stop_order"])
            self._ensure_trip_editable(connection, trip_id)
            stop_count = connection.execute(
                "SELECT COUNT(*) AS stop_count FROM station_trips WHERE trip_id = ?",
                (trip_id,),
            ).fetchone()
            normalized_order = max(1, min(stop_order, int(stop_count["stop_count"] or 0)))
            if normalized_order < current_order:
                connection.execute(
                    """
                    UPDATE station_trips
                    SET stop_order = stop_order + 1
                    WHERE trip_id = ? AND stop_order >= ? AND stop_order < ?
                    """,
                    (trip_id, normalized_order, current_order),
                )
            elif normalized_order > current_order:
                connection.execute(
                    """
                    UPDATE station_trips
                    SET stop_order = stop_order - 1
                    WHERE trip_id = ? AND stop_order <= ? AND stop_order > ?
                    """,
                    (trip_id, normalized_order, current_order),
                )
            connection.execute(
                """
                UPDATE station_trips
                SET station_id = ?, stop_order = ?, arrival_time = ?, departure_time = ?
                WHERE id = ?
                """,
                (station_id, normalized_order, arrival_time, departure_time, stop_id),
            )
            self._normalize_trip_stops(connection, trip_id)
            station = connection.execute("SELECT code, name FROM stations WHERE id = ?", (station_id,)).fetchone()
            self._write_audit_log(
                connection,
                user_id=actor_user_id,
                action="UPDATE_STOP",
                target_type="station_trip",
                target_id=str(stop_id),
                target_label=f"{station['code']} - {station['name']}" if station else str(station_id),
                details=f"Cập nhật điểm dừng của chuyến {trip_id}",
            )
            connection.commit()

    def delete_trip_stop(self, stop_id: int, actor_user_id: int | None = None) -> None:
        with self.database.connect() as connection:
            trip_stop = connection.execute(
                """
                SELECT station_trips.trip_id, station_trips.stop_order, stations.code, stations.name
                FROM station_trips
                JOIN stations ON stations.id = station_trips.station_id
                WHERE station_trips.id = ?
                """,
                (stop_id,),
            ).fetchone()
            if not trip_stop:
                raise ValueError("Không tìm thấy điểm dừng")
            trip_id = int(trip_stop["trip_id"])
            stop_order = int(trip_stop["stop_order"])
            self._ensure_trip_editable(connection, trip_id)
            stop_count = connection.execute(
                "SELECT COUNT(*) AS stop_count FROM station_trips WHERE trip_id = ?",
                (trip_id,),
            ).fetchone()
            total_stops = int(stop_count["stop_count"] or 0)
            if total_stops <= 2:
                raise ValueError("Lịch trình phải còn ít nhất ga đầu và ga cuối")
            if stop_order == 1 or stop_order == total_stops:
                raise ValueError("Không được phép xóa ga đầu hoặc ga cuối")
            connection.execute("DELETE FROM station_trips WHERE id = ?", (stop_id,))
            # Shift existing stops to avoid UNIQUE constraint conflict in SQLite
            connection.execute(
                """
                UPDATE station_trips
                SET stop_order = -(stop_order - 1)
                WHERE trip_id = ? AND stop_order > ?
                """,
                (trip_id, stop_order),
            )
            connection.execute(
                """
                UPDATE station_trips
                SET stop_order = -stop_order
                WHERE trip_id = ? AND stop_order < 0
                """,
                (trip_id,),
            )
            self._normalize_trip_stops(connection, trip_id)
            self._write_audit_log(
                connection,
                user_id=actor_user_id,
                action="DELETE_STOP",
                target_type="station_trip",
                target_id=str(stop_id),
                target_label=f"{trip_stop['code']} - {trip_stop['name']}",
                details=f"Xóa điểm dừng khỏi chuyến {trip_id}",
            )
            connection.commit()

    def _seat_multiplier(self, seat_type: str) -> float:
        mapping = {
            "Ghế cứng": 1.0,      # Giá gốc
            "Ghế mềm": 1.25,      # Cao hơn 25%
            "Giường nằm": 1.6,    # Cao hơn 60%
            "Khoang VIP": 2.5,    # Cao hơn 150%
        }
        return mapping.get(seat_type, 1.0)

    def _ensure_trip_editable(self, connection: Any, trip_id: int) -> None:
        ticket = connection.execute(
            """
            SELECT id
            FROM tickets
            WHERE trip_id = ?
              AND status != 'cancelled'
            LIMIT 1
            """,
            (trip_id,),
        ).fetchone()
        if ticket:
            raise ValueError("Không thể sửa hành trình khi chuyến đã có vé đang hiệu lực")

    def _normalize_trip_stops(self, connection: Any, trip_id: int) -> None:
        stops = connection.execute(
            """
            SELECT id, station_id, stop_order, arrival_time, departure_time
            FROM station_trips
            WHERE trip_id = ?
            ORDER BY stop_order
            """,
            (trip_id,),
        ).fetchall()
        stop_rows = [dict(row) for row in stops]
        if len(stop_rows) < 2:
            raise ValueError("Lịch trình phải có ít nhất 2 ga")
        for expected_order, stop in enumerate(stop_rows, start=1):
            if int(stop["stop_order"]) != expected_order:
                connection.execute(
                    "UPDATE station_trips SET stop_order = ? WHERE id = ?",
                    (-expected_order, stop["id"]),
                )
                stop["stop_order"] = -expected_order
        
        connection.execute(
            "UPDATE station_trips SET stop_order = -stop_order WHERE trip_id = ? AND stop_order < 0",
            (trip_id,)
        )
        
        # Reload stop_rows with positive orders for subsequent checks
        stops = connection.execute(
            "SELECT id, station_id, stop_order, arrival_time, departure_time FROM station_trips WHERE trip_id = ? ORDER BY stop_order",
            (trip_id,)
        ).fetchall()
        stop_rows = [dict(row) for row in stops]

        first_stop = stop_rows[0]
        last_stop = stop_rows[-1]
        if first_stop["arrival_time"]:
            raise ValueError("Ga đầu không được có giờ đến")
        if not first_stop["departure_time"]:
            raise ValueError("Ga đầu phải có giờ đi")
        if not last_stop["arrival_time"]:
            raise ValueError("Ga cuối phải có giờ đến")
        if last_stop["departure_time"]:
            raise ValueError("Ga cuối không được có giờ đi")
        for stop in stop_rows[1:-1]:
            if not stop["arrival_time"] or not stop["departure_time"]:
                raise ValueError("Các ga trung gian phải có đủ giờ đến và giờ đi")

        trip = connection.execute(
            "SELECT train_id, departure_date, base_price FROM trips WHERE id = ?",
            (trip_id,),
        ).fetchone()
        if not trip:
            raise ValueError("Không tìm thấy chuyến để chuẩn hóa hành trình")
        normalized_stops = [
            (int(stop["station_id"]), stop["arrival_time"], stop["departure_time"])
            for stop in stop_rows
        ]
        self._validate_trip_rules(
            connection,
            train_id=int(trip["train_id"]),
            departure_date=str(trip["departure_date"]),
            stops=normalized_stops,
            base_price=float(trip["base_price"]),
            exclude_trip_id=trip_id,
        )

        connection.execute(
            """
            UPDATE trips
            SET departure_time = ?, arrival_time = ?
            WHERE id = ?
            """,
            (first_stop["departure_time"], last_stop["arrival_time"], trip_id),
        )

    def _validate_trip_rules(
        self,
        connection: Any,
        *,
        train_id: int,
        departure_date: str,
        stops: list[tuple[int, str | None, str | None]],
        base_price: float,
        exclude_trip_id: int | None = None,
    ) -> None:
        if base_price < 0 or not float(base_price).is_integer():
            raise ValueError("Giá vé cơ sở phải là số nguyên dương")
        if len(stops) < 2:
            raise ValueError("Hành trình phải có ít nhất 2 ga")
        if int(stops[0][0]) == int(stops[-1][0]):
            raise ValueError("Ga đi và ga đến không được trùng nhau!")

        departure_dt, arrival_dt = self._calculate_trip_window(departure_date, stops)
        if departure_dt <= datetime.now():
            raise ValueError("Thời gian đi phải là thời gian trong tương lai")
        if arrival_dt <= departure_dt:
            raise ValueError("Thời gian đến phải lớn hơn thời gian đi")

        conflict_sql = """
            SELECT id, trip_code, departure_date, departure_time, arrival_time
            FROM trips
            WHERE train_id = ?
        """
        params: list[Any] = [train_id]
        if exclude_trip_id is not None:
            conflict_sql += " AND id != ?"
            params.append(exclude_trip_id)
        existing_trips = connection.execute(conflict_sql, tuple(params)).fetchall()
        for existing_trip in existing_trips:
            existing_departure, existing_arrival = self._calculate_trip_window(
                str(existing_trip["departure_date"]),
                [
                    (0, None, str(existing_trip["departure_time"])),
                    (1, str(existing_trip["arrival_time"]), None),
                ],
            )
            if departure_dt < existing_arrival and arrival_dt > existing_departure:
                raise ValueError(
                    f"Tàu {existing_trip['trip_code']} đang bận trong khoảng thời gian bị chồng lấn"
                )

    def _calculate_trip_window(
        self,
        departure_date: str,
        stops: list[tuple[int, str | None, str | None]],
    ) -> tuple[datetime, datetime]:
        if len(stops) < 2:
            raise ValueError("Hành trình phải có ít nhất 2 ga")
        current_day = datetime.strptime(departure_date, "%Y-%m-%d")
        previous_event: datetime | None = None
        trip_departure: datetime | None = None
        trip_arrival: datetime | None = None

        for index, stop_info in enumerate(stops):
            arrival_time = stop_info[1]
            departure_time = stop_info[2]
            if index == 0:
                if not departure_time:
                    raise ValueError("Ga đầu phải có giờ đi")
                departure_dt = self._combine_time_on_or_after(current_day, departure_time, previous_event)
                trip_departure = departure_dt
                previous_event = departure_dt
                current_day = departure_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                continue

            if arrival_time:
                arrival_dt = self._combine_time_on_or_after(current_day, arrival_time, previous_event)
                previous_event = arrival_dt
                current_day = arrival_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                trip_arrival = arrival_dt
            if departure_time:
                departure_dt = self._combine_time_on_or_after(current_day, departure_time, previous_event)
                previous_event = departure_dt
                current_day = departure_dt.replace(hour=0, minute=0, second=0, microsecond=0)

        if trip_departure is None or trip_arrival is None:
            raise ValueError("Không xác định được thời gian đi hoặc đến")
        return trip_departure, trip_arrival

    def _combine_time_on_or_after(
        self,
        current_day: datetime,
        time_value: str,
        previous_event: datetime | None,
    ) -> datetime:
        parsed_time = datetime.strptime(str(time_value), "%H:%M")
        candidate = current_day.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
        if previous_event is not None and candidate < previous_event:
            candidate += timedelta(days=1)
        return candidate

    def _resolve_segment_ids(
        self,
        connection: Any,
        trip_id: int,
        boarding_station_trip_id: int | None,
        alighting_station_trip_id: int | None,
    ) -> tuple[int, int]:
        if boarding_station_trip_id and alighting_station_trip_id:
            return int(boarding_station_trip_id), int(alighting_station_trip_id)
        first_stop = connection.execute(
            """
            SELECT id
            FROM station_trips
            WHERE trip_id = ?
            ORDER BY stop_order
            LIMIT 1
            """,
            (trip_id,),
        ).fetchone()
        last_stop = connection.execute(
            """
            SELECT id
            FROM station_trips
            WHERE trip_id = ?
            ORDER BY stop_order DESC
            LIMIT 1
            """,
            (trip_id,),
        ).fetchone()
        if not first_stop or not last_stop:
            raise ValueError("Chuyến tàu chưa có hành trình ga")
        return int(first_stop["id"]), int(last_stop["id"])

    def _get_segment_orders(
        self,
        connection: Any,
        boarding_station_trip_id: int,
        alighting_station_trip_id: int,
    ) -> tuple[int, int]:
        boarding = connection.execute(
            "SELECT stop_order FROM station_trips WHERE id = ?",
            (boarding_station_trip_id,),
        ).fetchone()
        alighting = connection.execute(
            "SELECT stop_order FROM station_trips WHERE id = ?",
            (alighting_station_trip_id,),
        ).fetchone()
        if not boarding or not alighting:
            raise ValueError("Không xác định được chặng tra cứu")
        return int(boarding["stop_order"]), int(alighting["stop_order"])

    def _refresh_trip_seat_status(self, connection: Any, seat_id: int) -> None:
        active_ticket = connection.execute(
            """
            SELECT id
            FROM tickets
            WHERE trip_seat_id = ?
              AND status != 'cancelled'
            LIMIT 1
            """,
            (seat_id,),
        ).fetchone()
        connection.execute(
            "UPDATE trip_seats SET status = ? WHERE id = ?",
            ("booked" if active_ticket else "available", seat_id),
        )

    def _write_audit_log(
        self,
        connection: Any,
        *,
        user_id: int | None,
        action: str,
        target_type: str,
        target_id: str | None,
        target_label: str,
        details: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO audit_logs (
                user_id, action, target_type, target_id, target_label, details
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, action, target_type, target_id, target_label, details),
        )
