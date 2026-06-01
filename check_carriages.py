import sqlite3
import os

db_path = "Nhom2.eaut.edu.vn-main/train_ticket.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='carriages'")
print(cursor.fetchone()[0])
conn.close()
