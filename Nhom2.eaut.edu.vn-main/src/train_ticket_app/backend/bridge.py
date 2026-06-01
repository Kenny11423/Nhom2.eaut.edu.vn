from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import QObject, Slot

from src.train_ticket_app.backend.service import TicketService


class AppBridge(QObject):
    def __init__(self, service: TicketService) -> None:
        super().__init__()
        self.service = service
        self.current_user: dict[str, Any] | None = None

    @Slot(str, result=str)
    def login(self, payload: str) -> str:
        data = json.loads(payload or "{}")
        user = self.service.login(data.get("username", ""), data.get("password", ""))
        if not user:
            return self._response(False, "Sai tài khoản hoặc mật khẩu")
        self.current_user = user
        return self._response(True, "Đăng nhập thành công", {"user": user, **self.service.bootstrap_payload()})

    @Slot(result=str)
    def bootstrap(self) -> str:
        return self._response(True, "Khởi tạo dữ liệu thành công", self.service.bootstrap_payload())

    @Slot(str, result=str)
    def searchTrips(self, payload: str) -> str:
        data = json.loads(payload or "{}")
        trips = self.service.search_trips(
            data.get("origin", ""),
            data.get("destination", ""),
            data.get("travel_date", ""),
        )
        return self._response(True, "Tìm thấy kết quả", {"trips": trips})

    @Slot(str, result=str)
    def getTripCarriages(self, payload: str) -> str:
        data = json.loads(payload or "{}")
        try:
            trip_data = self.service.get_trip_carriages(
                int(data.get("trip_id")),
                int(data["boarding_station_trip_id"]) if data.get("boarding_station_trip_id") else None,
                int(data["alighting_station_trip_id"]) if data.get("alighting_station_trip_id") else None,
            )
        except (TypeError, ValueError) as exc:
            return self._response(False, str(exc))
        return self._response(True, "Lấy danh sách toa thành công", trip_data)

    @Slot(str, result=str)
    def getCarriageSeats(self, payload: str) -> str:
        data = json.loads(payload or "{}")
        try:
            seats = self.service.get_carriage_seats(
                int(data.get("carriage_trip_id")),
                int(data["boarding_station_trip_id"]) if data.get("boarding_station_trip_id") else None,
                int(data["alighting_station_trip_id"]) if data.get("alighting_station_trip_id") else None,
            )
        except (TypeError, ValueError) as exc:
            return self._response(False, str(exc))
        return self._response(True, "Lấy danh sách ghế thành công", {"seats": seats})

    @Slot(str, result=str)
    def createBooking(self, payload: str) -> str:
        if not self.current_user:
            return self._response(False, "Cần đăng nhập trước khi đặt vé")
        data = json.loads(payload or "{}")
        try:
            ticket = self.service.create_booking(
                int(self.current_user["id"]),
                int(data.get("trip_id")),
                int(data.get("seat_id")),
                int(data.get("boarding_station_trip_id")),
                int(data.get("alighting_station_trip_id")),
                data.get("full_name", ""),
                data.get("id_number", ""),
                data.get("phone", ""),
            )
        except (TypeError, ValueError) as exc:
            return self._response(False, str(exc))
        return self._response(
            True,
            "Đặt vé thành công",
            {
                **ticket,
                "dashboard": self.service.get_dashboard(),
                "tickets": self.service.search_tickets(""),
            },
        )

    @Slot(str, result=str)
    def searchTickets(self, payload: str) -> str:
        data = json.loads(payload or "{}")
        return self._response(True, "Lấy danh sách vé thành công", {"tickets": self.service.search_tickets(data.get("query", ""))})

    @Slot(str, result=str)
    def cancelTicket(self, payload: str) -> str:
        if not self.current_user:
            return self._response(False, "Cần đăng nhập trước khi hủy vé")
        data = json.loads(payload or "{}")
        try:
            self.service.cancel_ticket(data.get("ticket_code", ""), int(self.current_user["id"]))
        except ValueError as exc:
            return self._response(False, str(exc))
        return self._response(
            True,
            "Hủy vé thành công",
            {
                "dashboard": self.service.get_dashboard(),
                "tickets": self.service.search_tickets(""),
            },
        )

    @Slot(result=str)
    def getSchedules(self) -> str:
        return self._response(True, "Lấy lịch trình thành công", {"schedules": self.service.get_schedules()})

    @Slot(str, result=str)
    def addStation(self, payload: str) -> str:
        data = json.loads(payload or "{}")
        try:
            self.service.add_station(
                data.get("code", ""),
                data.get("name", ""),
                data.get("city", ""),
                int(self.current_user["id"]) if self.current_user else None,
            )
        except ValueError as exc:
            return self._response(False, str(exc))
        return self._response(True, "Đã thêm ga", {"catalog": self.service.get_catalog()})

    @Slot(str, result=str)
    def addTrain(self, payload: str) -> str:
        data = json.loads(payload or "{}")
        try:
            self.service.add_train(
                data.get("code", ""),
                data.get("name", ""),
                int(self.current_user["id"]) if self.current_user else None,
            )
        except ValueError as exc:
            return self._response(False, str(exc))
        return self._response(True, "Đã thêm tàu", {"catalog": self.service.get_catalog()})

    @Slot(str, result=str)
    def addCarriage(self, payload: str) -> str:
        data = json.loads(payload or "{}")
        try:
            self.service.add_carriage(
                data.get("carriage_code", ""),
                data.get("seat_type", ""),
                int(data.get("seat_count", 0)),
                int(self.current_user["id"]) if self.current_user else None,
            )
        except (TypeError, ValueError) as exc:
            return self._response(False, str(exc))
        return self._response(True, "Đã thêm toa", {"catalog": self.service.get_catalog()})

    @Slot(str, result=str)
    def createTrip(self, payload: str) -> str:
        data = json.loads(payload or "{}")
        try:
            self.service.create_trip(
                train_id=int(data.get("train_id")),
                trip_code=data.get("trip_code", ""),
                departure_date=data.get("departure_date", ""),
                base_price=float(data.get("base_price", 0)),
                status=data.get("status", "open"),
                stops=data.get("stops", []),
                carriage_ids=[int(value) for value in data.get("carriage_ids", [])],
                actor_user_id=int(self.current_user["id"]) if self.current_user else None,
            )
        except (TypeError, ValueError) as exc:
            return self._response(False, str(exc))
        return self._response(True, "Đã lập hành trình", self.service.bootstrap_payload())

    def _response(self, ok: bool, message: str, data: dict[str, Any] | None = None) -> str:
        return json.dumps({"ok": ok, "message": message, "data": data or {}}, ensure_ascii=False)
