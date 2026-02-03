import sqlite3

def check_structure():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Get DDL for UserProfile table
    try:
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='EngineerRPG_userprofile';")
        result = cursor.fetchone()
        if result:
            print("UserProfile Table Schema:")
            print(result[0])
        else:
            print("Table EngineerRPG_userprofile not found.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_structure()
