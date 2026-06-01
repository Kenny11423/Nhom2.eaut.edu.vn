import sys
import os
from PySide6.QtWidgets import QApplication

project_root = os.path.abspath("Nhom2.eaut.edu.vn-main")
sys.path.append(project_root)

from src.train_ticket_app.backend.database import DatabaseManager

app = QApplication(sys.argv)
db_path = os.path.join(project_root, "train_ticket.db")
if os.path.exists(db_path): os.remove(db_path)

db = DatabaseManager(db_path)
db.initialize()

def seed():
    with db.connect() as conn:
        # 1. Thêm các Ga Master
        stations_data = [
            ('HN', 'Hà Nội', 'Hà Nội'), ('PL', 'Phủ Lý', 'Hà Nam'), ('ND', 'Nam Định', 'Nam Định'),
            ('NB', 'Ninh Bình', 'Ninh Bình'), ('TH', 'Thanh Hóa', 'Thanh Hóa'), ('V', 'Vinh', 'Nghệ An'),
            ('HU', 'Huế', 'Huế'), ('DN', 'Đà Nẵng', 'Đà Nẵng'), ('NT', 'Nha Trang', 'Khánh Hòa'), ('SG', 'Sài Gòn', 'TP.HCM'),
            ('GL', 'Gia Lâm', 'Hà Nội'), ('YV', 'Yên Viên', 'Hà Nội'), ('VT', 'Việt Trì', 'Phú Thọ'), 
            ('YB', 'Yên Bái', 'Yên Bái'), ('LC', 'Lào Cai', 'Lào Cai'),
            ('HD', 'Hải Dương', 'Hải Dương'), ('HP', 'Hải Phòng', 'Hải Phòng'),
            ('UP', 'Uông Bí', 'Quảng Ninh'), ('HL', 'Hạ Long', 'Quảng Ninh')
        ]
        station_ids = {}
        for code, name, city in stations_data:
            cur = conn.execute("INSERT INTO stations (code, name, city) VALUES (?, ?, ?)", (code, name, city))
            station_ids[code] = cur.lastrowid

        # 2. Định nghĩa 7 Tuyến
        routes = [
            ("Đường sắt Bắc - Nam", "Hà Nội - Sài Gòn"),
            ("Hà Nội - Lào Cai", "Tuyến Tây Bắc"),
            ("Hà Nội - Hải Phòng", "Tuyến phía Đông"),
            ("Hà Nội - Đồng Đăng", "Tuyến Lạng Sơn"),
            ("Hà Nội - Quán Triều", "Tuyến Thái Nguyên"),
            ("Yên Viên - Hạ Long", "Tuyến Quảng Ninh"),
            ("Sài Gòn - Phan Thiết", "Tuyến du lịch")
        ]
        route_ids = {}
        for name, desc in routes:
            cur = conn.execute("INSERT INTO railway_routes (route_name, description) VALUES (?, ?)", (name, desc))
            route_ids[name] = cur.lastrowid

        # 3. Ánh xạ Ga vào từng Tuyến
        rid_bn = route_ids["Đường sắt Bắc - Nam"]
        bn_mapping = [
            ('HN', 1, 0), ('PL', 2, 56), ('ND', 3, 87), ('NB', 4, 115), ('TH', 5, 176),
            ('V', 6, 319), ('HU', 7, 688), ('DN', 8, 791), ('NT', 9, 1315), ('SG', 10, 1726)
        ]
        for code, order, dist in bn_mapping:
            conn.execute("INSERT INTO route_stations (route_id, station_id, stop_order, distance_km) VALUES (?, ?, ?, ?)", 
                         (rid_bn, station_ids[code], order, dist))

        rid_lc = route_ids["Hà Nội - Lào Cai"]
        lc_mapping = [
            ('HN', 1, 0), ('GL', 2, 5), ('YV', 3, 11), ('VT', 4, 73), ('YB', 5, 155), ('LC', 6, 296)
        ]
        for code, order, dist in lc_mapping:
            conn.execute("INSERT INTO route_stations (route_id, station_id, stop_order, distance_km) VALUES (?, ?, ?, ?)", 
                         (rid_lc, station_ids[code], order, dist))

        rid_hp = route_ids["Hà Nội - Hải Phòng"]
        hp_mapping = [
            ('HN', 1, 0), ('GL', 2, 5), ('HD', 3, 57), ('HP', 4, 102)
        ]
        for code, order, dist in hp_mapping:
            conn.execute("INSERT INTO route_stations (route_id, station_id, stop_order, distance_km) VALUES (?, ?, ?, ?)", 
                         (rid_hp, station_ids[code], order, dist))

        rid_hl = route_ids["Yên Viên - Hạ Long"]
        hl_mapping = [
            ('YV', 1, 0), ('UP', 2, 120), ('HL', 3, 160)
        ]
        for code, order, dist in hl_mapping:
            conn.execute("INSERT INTO route_stations (route_id, station_id, stop_order, distance_km) VALUES (?, ?, ?, ?)", 
                         (rid_hl, station_ids[code], order, dist))

        # 4. Trưởng tàu
        for name in ["Nguyễn Văn Mạnh", "Trần Đức Thắng", "Lê Hồng Anh", "Phạm Minh Hoàng", "Vũ Quang Huy", "Đặng Quốc Bảo"]:
            conn.execute("INSERT INTO train_staff (full_name, staff_role) VALUES (?, 'captain')", (name,))

        # 5. Tàu & Toa & Admin
        conn.execute("INSERT INTO trains (code, name) VALUES ('SE1', 'SE1 Express')")
        conn.execute("INSERT INTO trains (code, name) VALUES ('LC1', 'Lào Cai Express')")
        conn.executemany("INSERT INTO carriages (carriage_code, seat_type, seat_count) VALUES (?, ?, ?)", [
            ('T1', 'Ghế mềm', 64), ('T2', 'Giường nằm', 28), ('T3', 'Khoang VIP', 12)
        ])
        conn.execute("INSERT INTO users (username, password, full_name, role) VALUES ('admin', 'admin', 'Quản trị viên', 'admin')")

        conn.commit()
    print("Đã khởi tạo Database và nạp 7 tuyến đường sắt thành công!")

if __name__ == "__main__":
    seed()
