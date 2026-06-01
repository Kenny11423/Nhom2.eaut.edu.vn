from __future__ import annotations
import sys
import os
from datetime import datetime, timedelta

# Add the project root to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, "Nhom2.eaut.edu.vn-main")
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from src.train_ticket_app.backend.database import DatabaseManager
    from src.train_ticket_app.backend.service import TicketService
except ImportError:
    print("Error: Could not import from src. Ensure Nhom2.eaut.edu.vn-main folder exists and contains src.")
    sys.exit(1)

# Master Route Data (Code, Cumulative Distance in Km)
MASTER_ROUTE_DATA = [
    ("HN", 0), ("PL", 56), ("ND", 87), ("NB", 115), ("TH", 176), 
    ("V", 319), ("DH", 522), ("DHA", 622), ("HU", 688), ("DN", 791), 
    ("TK", 865), ("QN", 928), ("DT", 1096), ("THO", 1198), ("NT", 1315), 
    ("TC", 1408), ("BT", 1551), ("BH", 1697), ("DA", 1707), ("SG", 1726)
]
ROUTE_ORDER = [item[0] for item in MASTER_ROUTE_DATA]
ROUTE_DISTANCES = {item[0]: item[1] for item in MASTER_ROUTE_DATA}

def generate_varied_trips():
    db_manager = DatabaseManager()
    service = TicketService(db_manager)
    
    # Ensure database is initialized
    db_manager.initialize()
    
    start_date = datetime(2026, 5, 31)
    end_date = datetime(2026, 6, 6)
    
    catalog = service.get_catalog()
    stations = catalog["stations"]
    trains = catalog["trains"]
    carriages = catalog["carriages"]
    station_map = {s["code"]: s["id"] for s in stations}
    
    if not trains or not carriages:
        print("Error: Need trains and carriages.")
        return

    current_date = start_date
    global_counter = 5000
    
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"Generating varied trips for {date_str}...")
        
        # 1. Express (2 stops: HN <-> SG) - 4 trips each way
        for i in range(4):
            # Forward
            generate_trip(service, trains, carriages, ["HN", "SG"], station_map, date_str, f"EXPF{global_counter}", 6 + i*2)
            global_counter += 1
            # Backward
            generate_trip(service, trains, carriages, ["SG", "HN"], station_map, date_str, f"EXPB{global_counter}", 7 + i*2)
            global_counter += 1

        # 2. Inter-city (5 stops) - 6 trips each way
        # Slice: HN -> TH -> DN -> NT -> SG
        inter_route = ["HN", "TH", "DN", "NT", "SG"]
        for i in range(6):
            generate_trip(service, trains, carriages, inter_route, station_map, date_str, f"INTF{global_counter}", 6 + i)
            global_counter += 1
            generate_trip(service, trains, carriages, list(reversed(inter_route)), station_map, date_str, f"INTB{global_counter}", 7 + i)
            global_counter += 1

        # 3. Local (15 stops) - 10 trips each way
        # Using every ~1.3 stops from master list
        local_route = [ROUTE_ORDER[j] for j in range(0, len(ROUTE_ORDER), 1)][:15]
        if "SG" not in local_route: local_route[-1] = "SG" # Ensure it reaches
        
        for i in range(10):
            generate_trip(service, trains, carriages, local_route, station_map, date_str, f"LOCF{global_counter}", 5 + i)
            global_counter += 1
            generate_trip(service, trains, carriages, list(reversed(local_route)), station_map, date_str, f"LOCB{global_counter}", 6 + i)
            global_counter += 1
                
        current_date += timedelta(days=1)
    
    print("Varied schedule generated successfully.")

def generate_trip(service, trains, carriages, route_codes, station_map, date_str, trip_code, start_hour):
    train = trains[hash(trip_code) % len(trains)]
    carriage_ids = [c["id"] for c in carriages[:5]]
    
    stops = []
    current_time = datetime.strptime(f"{start_hour:02d}:00", "%H:%M")
    
    for idx, code in enumerate(route_codes):
        dist = ROUTE_DISTANCES[code]
        arr, dep = None, None
        
        if idx > 0:
            prev_code = route_codes[idx-1]
            km = abs(dist - ROUTE_DISTANCES[prev_code])
            # Speed: 60km/h average -> 1 min per km
            current_time += timedelta(minutes=int(km * 1))
            arr = current_time.strftime("%H:%M")
        
        if idx < len(route_codes) - 1:
            if idx > 0:
                current_time += timedelta(minutes=10) # 10m stop
            dep = current_time.strftime("%H:%M")
            
        stops.append({
            "station_id": station_map[code],
            "arrival_time": arr,
            "departure_time": dep,
            "distance_km": dist
        })
        
    try:
        service.create_trip(
            train_id=train["id"],
            trip_code=trip_code,
            departure_date=date_str,
            base_price=0, 
            status="Đang bán",
            stops=stops,
            carriage_ids=carriage_ids,
            actor_user_id=1
        )
    except Exception as e:
        print(f"Error {trip_code}: {e}")

if __name__ == "__main__":
    generate_varied_trips()
