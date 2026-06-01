import sqlite3
import os

db_path = "Nhom2.eaut.edu.vn-main/train_ticket.db"
if os.path.exists(db_path): os.remove(db_path)

conn = sqlite3.connect(db_path)
conn.executescript("""
CREATE TABLE IF NOT EXISTS stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS railway_routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT
);
CREATE TABLE IF NOT EXISTS route_stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL,
    station_id INTEGER NOT NULL,
    stop_order INTEGER NOT NULL,
    distance_km REAL NOT NULL,
    FOREIGN KEY (route_id) REFERENCES railway_routes(id),
    FOREIGN KEY (station_id) REFERENCES stations(id)
);
CREATE TABLE IF NOT EXISTS train_staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR(255) NOT NULL,
    staff_role VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'available'
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL
);
""")

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

# BN
bn_mapping = [('HN', 1, 0), ('PL', 2, 56), ('ND', 3, 87), ('NB', 4, 115), ('TH', 5, 176), ('V', 6, 319), ('HU', 7, 688), ('DN', 8, 791), ('NT', 9, 1315), ('SG', 10, 1726)]
rid = route_ids["Đường sắt Bắc - Nam"]
for code, order, dist in bn_mapping:
    conn.execute("INSERT INTO route_stations (route_id, station_id, stop_order, distance_km) VALUES (?, ?, ?, ?)", (rid, station_ids[code], order, dist))

# LC
lc_mapping = [('HN', 1, 0), ('GL', 2, 5), ('YV', 3, 11), ('VT', 4, 73), ('YB', 5, 155), ('LC', 6, 296)]
rid = route_ids["Hà Nội - Lào Cai"]
for code, order, dist in lc_mapping:
    conn.execute("INSERT INTO route_stations (route_id, station_id, stop_order, distance_km) VALUES (?, ?, ?, ?)", (rid, station_ids[code], order, dist))

# HP
hp_mapping = [('HN', 1, 0), ('GL', 2, 5), ('HD', 3, 57), ('HP', 4, 102)]
rid = route_ids["Hà Nội - Hải Phòng"]
for code, order, dist in hp_mapping:
    conn.execute("INSERT INTO route_stations (route_id, station_id, stop_order, distance_km) VALUES (?, ?, ?, ?)", (rid, station_ids[code], order, dist))

# HL
hl_mapping = [('YV', 1, 0), ('UP', 2, 120), ('HL', 3, 160)]
rid = route_ids["Yên Viên - Hạ Long"]
for code, order, dist in hl_mapping:
    conn.execute("INSERT INTO route_stations (route_id, station_id, stop_order, distance_km) VALUES (?, ?, ?, ?)", (rid, station_ids[code], order, dist))

for name in ["Nguyễn Văn Mạnh", "Trần Đức Thắng", "Lê Hồng Anh", "Phạm Minh Hoàng", "Vũ Quang Huy", "Đặng Quốc Bảo"]:
    conn.execute("INSERT INTO train_staff (full_name, staff_role) VALUES (?, 'captain')", (name,))

conn.execute("INSERT INTO users (username, password, full_name, role) VALUES ('admin', 'admin', 'Quản trị viên', 'admin')")
conn.commit()
conn.close()
print("Dữ liệu 7 tuyến đường đã sẵn sàng!")
