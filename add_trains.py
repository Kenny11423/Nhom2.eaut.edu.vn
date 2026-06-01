import sys
import os
sys.path.append(os.getcwd() + "/Nhom2.eaut.edu.vn-main")

from src.train_ticket_app.backend.database import DatabaseManager
from src.train_ticket_app.backend.service import TicketService

def add_trains():
    db = DatabaseManager()
    service = TicketService(db)
    for i in range(1, 51):
        try:
            service.add_train(f"T{i:02d}", f"Tàu Thống Nhất {i:02d}", actor_user_id=1)
        except:
            pass
    print("Added 50 trains.")

if __name__ == "__main__":
    add_trains()
