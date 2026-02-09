
import sqlite3
import os

db_path = 'EngineerRPG/eng.sqlite3db'
output_file = 'db_schema_utf8.txt'

if not os.path.exists(db_path):
    print(f"Database file not found at {db_path}")
    exit(1)

try:
    with open(output_file, 'w', encoding='utf-8') as f:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        f.write(f"Tables found: {tables}\n")
        
        for table_name in tables:
            t = table_name[0]
            f.write(f"\n--- Schema for table: {t} ---\n")
            cursor.execute(f"PRAGMA table_info({t})")
            columns = cursor.fetchall()
            for col in columns:
                f.write(f"{col}\n")
                
            # Preview data
            f.write(f"\n--- Preview data for table: {t} (first 1 row) ---\n")
            cursor.execute(f"SELECT * FROM {t} LIMIT 1")
            rows = cursor.fetchall()
            for row in rows:
                f.write(f"{row}\n")

        conn.close()
    print(f"Schema written to {output_file}")
except Exception as e:
    print(f"Error: {e}")
