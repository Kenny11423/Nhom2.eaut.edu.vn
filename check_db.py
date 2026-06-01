import sqlite3
from pathlib import Path

db_path = Path("train_ticket.db")
if not db_path.exists():
    print(f"Database file not found at {db_path.absolute()}")
else:
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        print("--- Meta ---")
        meta = conn.execute("SELECT * FROM app_meta").fetchall()
        for row in meta:
            print(dict(row))
            
        print("\n--- Users ---")
        users = conn.execute("SELECT id, username, role FROM users").fetchall()
        for row in users:
            print(dict(row))
            
        print("\n--- Stations (first 5) ---")
        stations = conn.execute("SELECT id, code, name, city FROM stations LIMIT 5").fetchall()
        for row in stations:
            print(dict(row))
            
        conn.close()
    except Exception as e:
        print(f"Error reading database: {e}")
