import sqlite3
conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT bridge_id, el_l1_start, el_l1_end, el_l2_start, el_l2_end, el_b1_start, el_b1_end, el_b2_start, el_b2_end, skew_angle FROM bgf_excavation_foundationexcavation WHERE bridge_id='P29S'")
row = cur.fetchone()
if row:
    print(f"P29S data: L1({row[1]},{row[2]}), L2({row[3]},{row[4]}), B1({row[5]},{row[6]}), B2({row[7]},{row[8]}), Skew({row[9]})")
else:
    print("Not found")
conn.close()
