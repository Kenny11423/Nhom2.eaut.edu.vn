from __future__ import annotations
import sys
import os
import random
from datetime import datetime, timedelta

# 1. Sửa lỗi Import: Thêm đường dẫn chính xác vào hệ thống
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from src.train_ticket_app.backend.database import DatabaseManager
    from src.train_ticket_app.backend.service import TicketService
except ImportError:
    print("Không tìm thấy mã nguồn tại Nhom2.eaut.edu.vn-main/src. Vui lòng kiểm tra lại thư mục.")
    sys.exit(1)

def generate_bulk_trips():
    db_path = os.path.join(project_root, "train_ticket.db")
    db = DatabaseManager(db_path)
    service = TicketService(db)
    
    catalog = service.get_catalog()
    routes = catalog.get("routes", [])
    trains = catalog.get("trains", [])
    captains = catalog.get("captains", [])
    carriages = catalog.get("carriages", [])
    
    if not routes or not trains:
        print("Dữ liệu nền (Tuyến/Tàu) chưa có. Vui lòng chạy ứng dụng để khởi tạo trước.")
        return

    print(f"Bắt đầu tạo dữ liệu mẫu cho {len(routes)} tuyến đường...")

    # Tạo chuyến tàu cho 7 ngày tới
    start_date = datetime.now()
    
    for i in range(7):
        current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        
        for route in routes:
            # Chọn ngẫu nhiên đầu máy tàu
            train = random.choice(trains)
            captain = random.choice(captains) if captains else None
            
            # Lấy danh sách ga của tuyến này
            route_stations = service.get_route_stations(route["id"])
            if len(route_stations) < 2: continue
            
            # Giả lập tham số cho Bước 1
            trip_code = f"{train['code']}-{route['id']}-{current_date.replace('-', '')[-4:]}"
            
            # Chuẩn bị danh sách ga (tự động tính giờ như Bước 2)
            stops = []
            curr_time = datetime.strptime("08:00", "%H:%M") # Giờ xuất phát mặc định
            
            for idx, rs in enumerate(route_stations):
                is_first = (idx == 0)
                is_last = (idx == len(route_stations) - 1)
                
                if not is_first:
                    dist_diff = abs(rs["distance_km"] - route_stations[idx-1]["distance_km"])
                    curr_time += timedelta(minutes=int(dist_diff * 1.2)) # 1.2 min/km
                
                arr_time = curr_time.strftime("%H:%M")
                dwell = 10 if not is_first and not is_last else 0
                
                # Giờ đi = Đến + Đỗ
                dep_time = (curr_time + timedelta(minutes=dwell)).strftime("%H:%M")
                if not is_last: curr_time += timedelta(minutes=dwell)

                stops.append({
                    "station_id": rs["id"],
                    "is_pick_up": 1,
                    "platform_code": f"Số {random.randint(1,2)}",
                    "arrival_time": arr_time if not is_first else None,
                    "stop_duration_min": dwell,
                    "departure_time": dep_time if not is_last else None,
                    "distance_km": rs["distance_km"]
                })

            # Chọn ngẫu nhiên 4-6 toa xe (Bước 3)
            c_ids = [c["id"] for c in random.choices(carriages, k=random.randint(4, 6))] if carriages else []

            try:
                service.create_trip(
                    train_id=train["id"],
                    trip_code=trip_code,
                    train_type="Tàu nhanh SE",
                    captain_id=captain["id"] if captain else None,
                    crew_code="Đội 1 (HN)",
                    departure_date=current_date,
                    base_price=400000,
                    status="open",
                    stops=stops,
                    carriage_ids=c_ids,
                    actor_user_id=1
                )
                print(f"  > Đã tạo chuyến {trip_code} ({route['route_name']}) ngày {current_date}")
            except Exception as e:
                print(f"  ! Lỗi khi tạo chuyến {trip_code}: {e}")

    print("\nHOÀN TẤT: Hệ thống đã đầy đủ dữ liệu mẫu cho cả tuần!")

if __name__ == "__main__":
    generate_bulk_trips()
