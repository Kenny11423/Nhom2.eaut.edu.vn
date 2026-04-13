# Tuan 2 - Thiet ke co so du lieu

## Cong nghe

- Co so du lieu: `SQLite`
- Backend truy cap du lieu: `sqlite3` cua Python
- Frontend desktop: `PySide6 + HTML/CSS/JavaScript`
- Xu ly thong ke nhanh: `numpy`

## Cac bang chinh

### users

- `id`: khoa chinh
- `username`: ten dang nhap
- `password`: mat khau
- `full_name`: ten nguoi dung
- `role`: vai tro `admin` hoac `staff`

### stations

- `id`
- `code`
- `name`
- `city`

### trains

- `id`
- `code`
- `name`
- `carriage_count`

### carriages

- `id`
- `train_id`
- `carriage_code`
- `seat_type`
- `seat_count`

### trips

- `id`
- `train_id`
- `trip_code`
- `origin_station_id`
- `destination_station_id`
- `departure_date`
- `departure_time`
- `arrival_time`
- `base_price`
- `status`

### trip_seats

- `id`
- `trip_id`
- `carriage_code`
- `seat_code`
- `seat_type`
- `seat_price`
- `status`

### passengers

- `id`
- `full_name`
- `id_number`
- `phone`

### tickets

- `id`
- `ticket_code`
- `passenger_id`
- `trip_id`
- `trip_seat_id`
- `booked_by`
- `price`
- `status`
- `booked_at`

## Quan he du lieu

- `trains` 1-n `carriages`
- `trains` 1-n `trips`
- `trips` 1-n `trip_seats`
- `passengers` 1-n `tickets`
- `trip_seats` 1-1 tuong doi voi `tickets` trong moi lan dat ve thanh cong
- `users` 1-n `tickets` qua truong `booked_by`

## Ghi chu thuc hien

- Schema va du lieu mau duoc khoi tao trong [src/train_ticket_app/backend/database.py](/home/Kennysk/Python/preparation/src/train_ticket_app/backend/database.py)
- File CSDL se duoc tao tu dong tai `data/train_ticket.db`
