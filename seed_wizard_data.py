import sys
import os
from PySide6.QtWidgets import QApplication

# Add project root to path
project_root = os.path.abspath("Nhom2.eaut.edu.vn-main")
sys.path.append(project_root)

from src.train_ticket_app.backend.database import DatabaseManager
from src.train_ticket_app.backend.service import TicketService

app = QApplication(sys.argv)
db_path = os.path.join(project_root, "train_ticket.db")
db = DatabaseManager(db_path)
db.initialize() # <--- QUAN TRỌNG: Tạo bảng ở đây
service = TicketService(db)

with db.connect() as conn:
    # 1. Thêm các Ga chính trên tuyến Bắc Nam
    stations = [
        ('HN', 'Hà Nội', 'Hà Nội'),
        ('PL', 'Phủ Lý', 'Hà Nam'),
        ('ND', 'Nam Định', 'Nam Định'),
        ('NB', 'Ninh Bình', 'Ninh Bình'),
        ('TH', 'Thanh Hóa', 'Thanh Hóa'),
        ('V', 'Vinh', 'Nghệ An'),
        ('HU', 'Huế', 'Thừa Thiên Huế'),
        ('DN', 'Đà Nẵng', 'Đà Nẵng'),
        ('NT', 'Nha Trang', 'Khánh Hòa'),
        ('SG', 'Sài Gòn', 'TP Hồ Chí Minh')
    ]
    conn.executemany("INSERT OR IGNORE INTO stations (code, name, city) VALUES (?, ?, ?)", stations)

    # 2. Thêm đầu máy tàu
    conn.execute("INSERT OR IGNORE INTO trains (code, name) VALUES ('SE1', 'Đoàn tàu nhanh SE1')")
    conn.execute("INSERT OR IGNORE INTO trains (code, name) VALUES ('SE3', 'Đoàn tàu nhanh SE3')")

    # 3. Thêm các loại Toa xe
    carriages = [
        ('T1-MC', 'Ghế mềm', 64),
        ('T2-MC', 'Ghế mềm', 64),
        ('T3-GN', 'Giường nằm', 28),
        ('T4-GN', 'Giường nằm', 28),
        ('T5-VIP', 'Khoang VIP', 12)
    ]
    conn.executemany("INSERT OR IGNORE INTO carriages (carriage_code, seat_type, seat_count) VALUES (?, ?, ?)", carriages)

    # 4. Đảm bảo có Trưởng tàu (Admin/Staff)
    conn.execute("INSERT OR IGNORE INTO users (username, password, full_name, role) VALUES ('admin', 'admin', 'Nguyễn Văn Quản Lý', 'admin')")
    conn.execute("INSERT OR IGNORE INTO users (username, password, full_name, role) VALUES ('staff1', '123', 'Trần Thị Tiếp Viên', 'staff')")
    
    conn.commit()

print("Đã nạp dữ liệu nền và khởi tạo bảng thành công!")
