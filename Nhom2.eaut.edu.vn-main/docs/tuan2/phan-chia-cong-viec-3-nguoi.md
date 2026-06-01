# Phân chia công việc tuần 2 cho 3 người

Mục tiêu: mỗi người làm một nhóm file riêng để **tự commit thủ công** lên Github, hạn chế conflict.

## Phạm Đức Huy - Giao diện HTML/CSS/JavaScript

**Phạm vi chịu trách nhiệm**

- Thiết kế và chỉnh sửa giao diện trang đăng nhập
- Giao diện dashboard
- Giao diện tra cứu chuyến tàu và đặt vé
- Tương tác JavaScript với bridge

**File nên phụ trách**

- `src/train_ticket_app/assets/index.html`
- `src/train_ticket_app/assets/styles.css`
- `src/train_ticket_app/assets/app.js`

**Commit gợi ý**

- `feat(ui): xay dung giao dien desktop html/js cho man hinh chinh`

## Phạm Quang Huy - Backend Python và cầu nối PySide6

**Phạm vi chịu trách nhiệm**

- Tạo cửa sổ desktop bằng `PySide6`
- Cấu hình `QWebEngineView`, `QWebChannel`
- Xử lý đăng nhập
- Xử lý tra cứu chuyến tàu, đặt vé, hủy vé
- Kết nối frontend với backend

**File nên phụ trách**

- `app.py`
- `src/train_ticket_app/main_window.py`
- `src/train_ticket_app/backend/bridge.py`

**Commit gợi ý**

- `feat(app): ket noi pyside6 voi frontend js qua qwebchannel`

## Trần Long Vũ - Cơ sở dữ liệu và dữ liệu mẫu

**Phạm vi chịu trách nhiệm**

- Thiết kế bảng dữ liệu
- Tạo schema SQLite
- Khởi tạo dữ liệu mẫu
- Tối ưu thống kê cơ bản bằng `numpy`
- Hoàn thiện tài liệu thiết kế CSDL và `requirements.txt`

**File nên phụ trách**

- `src/train_ticket_app/backend/database.py`
- `docs/tuan2/thiet-ke-co-so-du-lieu.md`
- `requirements.txt`
- `README.md`

V
