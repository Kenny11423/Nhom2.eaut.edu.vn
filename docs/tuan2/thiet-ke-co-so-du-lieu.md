# Tuần 2 - Thiết kế cơ sở dữ liệu

## Công nghệ

- Cơ sở dữ liệu: `SQLite`
- Backend truy cập dữ liệu: `sqlite3` của Python
- Frontend desktop: `PySide6 + HTML/CSS/JavaScript`
- Xử lý thống kê nhanh: `numpy`

## Các bảng chính

### users (người dùng)

- `id`: khóa chính
- `username`: tên đăng nhập
- `password`: mật khẩu
- `full_name`: tên người dùng
- `role`: vai trò `admin` hoặc `staff`

### stations (ga tàu)

- `id`
- `code`
- `name`
- `city`

### trains (tàu)

- `id`
- `code`
- `name`
- `carriage_count`

### carriages (toa tàu)

- `id`
- `train_id`
- `carriage_code`
- `seat_type`
- `seat_count`

### trips (chuyến tàu)

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

### trip_seats (chỗ ngồi chuyến tàu)

- `id`
- `trip_id`
- `carriage_code`
- `seat_code`
- `seat_type`
- `seat_price`
- `status`

### passengers (hành khách)

- `id`
- `full_name`
- `id_number`
- `phone`

### tickets (vé)

- `id`
- `ticket_code`
- `passenger_id`
- `trip_id`
- `trip_seat_id`
- `booked_by`
- `price`
- `status`
- `booked_at`

## Quan hệ dữ liệu

- `trains` 1-n `carriages`
- `trains` 1-n `trips`
- `trips` 1-n `trip_seats`
- `passengers` 1-n `tickets`
- `trip_seats` 1-1 tương đối với `tickets` trong mỗi lần đặt vé thành công
- `users` 1-n `tickets` qua trường `booked_by`

## Ghi chú thực hiện

- Schema và dữ liệu mẫu được khởi tạo trong [src/train_ticket_app/backend/database.py](/home/Kennysk/Python/preparation/src/train_ticket_app/backend/database.py)
- File CSDL sẽ được tạo tự động tại `data/train_ticket.db`
