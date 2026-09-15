"""SQLite logging helper (optional)."""
import os, sqlite3
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(BASE, "traffic.db")

def conn():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS predictions
        (ts TEXT, location TEXT, horizon INTEGER, available REAL, vehicles REAL, congestion REAL)""")
    return c
