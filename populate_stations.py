import sys
import os
sys.path.append(os.getcwd() + "/Nhom2.eaut.edu.vn-main")

from src.train_ticket_app.backend.database import DatabaseManager
from src.train_ticket_app.backend.service import TicketService

def populate_stations():
    db = DatabaseManager()
    service = TicketService(db)
    
    stations_data = [
        # Miền Bắc
        ("HN", "Ga Hà Nội", "Hà Nội"),
        ("LB", "Ga Long Biên", "Hà Nội"),
        ("GL", "Ga Gia Lâm", "Hà Nội"),
        ("HP", "Ga Hải Phòng", "Hải Phòng"),
        ("LC", "Ga Lào Cai", "Lào Cai"),
        ("DD", "Ga Đồng Đăng", "Lạng Sơn"),
        ("PL", "Ga Phủ Lý", "Hà Nam"),
        ("ND", "Ga Nam Định", "Nam Định"),
        ("NB", "Ga Ninh Bình", "Ninh Bình"),
        
        # Miền Trung
        ("TH", "Ga Thanh Hóa", "Thanh Hóa"),
        ("V", "Ga Vinh", "Nghệ An"),
        ("DH", "Ga Đồng Hới", "Quảng Bình"),
        ("DHA", "Ga Đông Hà", "Quảng Trị"),
        ("HU", "Ga Huế", "Thừa Thiên Huế"),
        ("DN", "Ga Đà Nẵng", "Đà Nẵng"),
        ("TK", "Ga Tam Kỳ", "Quảng Nam"),
        ("QN", "Ga Quảng Ngãi", "Quảng Ngãi"),
        ("DT", "Ga Diêu Trì", "Bình Định"),
        ("THO", "Ga Tuy Hòa", "Phú Yên"),
        ("NT", "Ga Nha Trang", "Khánh Hòa"),
        ("TC", "Ga Tháp Chàm", "Ninh Thuận"),
        
        # Miền Nam
        ("BT", "Ga Bình Thuận", "Bình Thuận"),
        ("PT", "Ga Phan Thiết", "Bình Thuận"),
        ("BH", "Ga Biên Hòa", "Đồng Nai"),
        ("DA", "Ga Dĩ An", "Bình Dương"),
        ("SG", "Ga Sài Gòn", "TP.HCM"),
    ]
    
    count = 0
    for code, name, city in stations_data:
        try:
            service.add_station(code, name, city, actor_user_id=1)
            count += 1
        except Exception as e:
            print(f"Bỏ qua {name} (có thể đã tồn tại): {e}")
            
    print(f"Đã thêm thành công {count} ga tàu mới.")

if __name__ == "__main__":
    populate_stations()
