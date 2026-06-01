# Project: Phần mềm quản lý bán vé tàu

Bộ bài làm hiện tại đã có:

- **Tuần 1:** mô tả chức năng và mockup giao diện
- **Tuần 2:** frontend desktop native bằng `PySide6 Qt Widgets`
- **Tuần 3:** backend nghiệp vụ cho đăng nhập, tra cứu chuyến tàu, xem ghế trống, đặt vé, hủy vé, thống kê dashboard và tích hợp hoàn chỉnh với giao diện native

## Cấu trúc chính

- [docs/tuan1/mo-ta-chuc-nang.md](docs/tuan1/mo-ta-chuc-nang.md)
- [docs/tuan1/mockup-ui.svg](docs/tuan1/mockup-ui.svg)
- [docs/tuan2/thiet-ke-co-so-du-lieu.md](docs/tuan2/thiet-ke-co-so-du-lieu.md)
- [docs/tuan2/phan-chia-cong-viec-3-nguoi.md](docs/tuan2/phan-chia-cong-viec-3-nguoi.md)
- [docs/tuan3/phan-chia-cong-viec-3-nguoi.md](docs/tuan3/phan-chia-cong-viec-3-nguoi.md)
- `app.py`
- `src/train_ticket_app/`

## Kết quả tuần 3

- Hoàn thiện backend nghiệp vụ cho đăng nhập, tra cứu chuyến tàu, xem ghế, đặt vé, hủy vé
- Tích hợp backend với giao diện desktop native bằng `PySide6 Qt Widgets`
- Tạo dữ liệu mẫu để demo dashboard, lịch trình và danh sách vé
- Phân chia công việc tuần 3 cho 3 thành viên tại [docs/tuan3/phan-chia-cong-viec-3-nguoi.md](docs/tuan3/phan-chia-cong-viec-3-nguoi.md)

## Thư viện cần cài

Tất cả thư viện ngoài thư viện chuẩn đã được khai báo trong [requirements.txt](requirements.txt):

- `PySide6`
- `numpy`
- `PyMySQL`

## Cách chạy

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Cấu hình database MariaDB cho DBeaver

Ứng dụng hiện dùng MariaDB thay vì file SQLite cục bộ.

- Database mặc định: `dbeaver`
- User mặc định: `dbeaver`
- Password mặc định: `123456`
- Host mặc định: `127.0.0.1`
- Port mặc định: `3306`

Khi chạy app, chương trình sẽ kiểm tra database `dbeaver` đã tồn tại chưa trong MariaDB. Nếu chưa có, app sẽ tự tạo database rồi tạo schema và dữ liệu mẫu.

Có thể đổi cấu hình qua biến môi trường:

- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DB_ADMIN_NAME`

## Tài khoản demo

- `admin / admin123`
- `staff / staff123`

## Ghi chú

- CSDL MariaDB `dbeaver` được kiểm tra và tạo tự động khi khởi động app
- Giao diện được xây dựng hoàn toàn bằng `PySide6 Qt Widgets`
- Dữ liệu mẫu đã có sẵn vé demo để phục vụ phần báo cáo và thao tác hủy vé
