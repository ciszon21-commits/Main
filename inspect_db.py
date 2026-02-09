
import sqlite3
import os

db_path = 'EngineerRPG/eng.sqlite3db'

if not os.path.exists(db_path):
    print(f"Database file not found at {db_path}")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables found: {tables}")
    
    for table_name in tables:
        t = table_name[0]
        print(f"\n--- Schema for table: {t} ---")
        cursor.execute(f"PRAGMA table_info({t})")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
            
        # Preview data
        print(f"\n--- Preview data for table: {t} (first 1 row) ---")
        cursor.execute(f"SELECT * FROM {t} LIMIT 1")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

    conn.close()
except Exception as e:
    print(f"Error: {e}")
