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
- `carriage_code`
- `seat_type`
- `seat_count`

### trips (chuyến tàu)

- `id`
- `train_id`
- `trip_code`
- `departure_date`
- `departure_time`
- `arrival_time`
- `base_price`
- `status`

### station_trips (các ga thuộc chuyến tàu)

- `id`
- `trip_id`
- `station_id`
- `stop_order`
- `arrival_time`
- `departure_time`

### carriage_trips (phân công toa cho từng chuyến)

- `id`
- `trip_id`
- `carriage_id`
- `carriage_order`

### trip_seats (chỗ ngồi chuyến tàu)

- `id`
- `carriage_trip_id`
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

- `trains` 1-n `trips`
- `stations` n-n `trips` qua bảng trung gian `station_trips`
- `carriages` n-n `trips` qua bảng trung gian `carriage_trips`
- `carriage_trips` 1-n `trip_seats`
- `passengers` 1-n `tickets`
- `trip_seats` 1-1 tương đối với `tickets` trong mỗi lần đặt vé thành công
- `users` 1-n `tickets` qua trường `booked_by`

## Ghi chú thực hiện

- Tài liệu này mô tả ERD mục tiêu sau khi chỉnh quan hệ; schema code hiện tại trong [src/train_ticket_app/backend/database.py](/home/Kennysk/Python/preparation/src/train_ticket_app/backend/database.py) vẫn cần migrate để khớp thiết kế này.
- Bảng `station_trips` cho phép mô tả hành trình chi tiết của một chuyến từ ga A đến ga B qua nhiều ga trung gian.
- Bảng `carriage_trips` cho phép cùng một `train` ở các ngày/chuyến khác nhau có thành phần toa khác nhau, thay vì gắn cố định toa vào tàu.
- File CSDL sẽ được tạo tự động tại `data/train_ticket.db`
