# Project: Phần mềm quản lý bán vé tàu

Bộ bài làm hiện tại đã có:

- **Tuần 1:** mô tả chức năng và mockup giao diện
- **Tuần 2:** frontend desktop bằng `PySide6 + HTML/CSS/JavaScript`, thiết kế `SQLite`, dữ liệu mẫu và bridge Python-JS

## Cấu trúc chính

- [docs/tuan1/mo-ta-chuc-nang.md](docs/tuan1/mo-ta-chuc-nang.md)
- [docs/tuan1/mockup-ui.svg](docs/tuan1/mockup-ui.svg)
- [docs/tuan2/thiet-ke-co-so-du-lieu.md](docs/tuan2/thiet-ke-co-so-du-lieu.md)
- [docs/tuan2/phan-chia-cong-viec-3-nguoi.md](docs/tuan2/phan-chia-cong-viec-3-nguoi.md)
- `app.py`
- `src/train_ticket_app/`

## Thư viện cần cài

Tất cả thư viện ngoài thư viện chuẩn đã được khai báo trong [requirements.txt](requirements.txt):

- `PySide6`
- `numpy`

## Cách chạy

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Tài khoản demo

- `admin / admin123`
- `staff / staff123`

## Ghi chú

- CSDL SQLite được tạo tự động tại `data/train_ticket.db`
- Frontend được vẽ bằng `HTML/CSS/JS` và hiển thị trong `QWebEngineView`
- `numpy` được dùng để tính tổng doanh thu và tỉ lệ lấp đầy trong dashboard
