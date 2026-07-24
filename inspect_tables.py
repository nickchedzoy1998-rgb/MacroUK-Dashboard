import sqlite3

conn = sqlite3.connect('data/economic_warehouse.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'chart_%' ORDER BY name")
for row in cur.fetchall():
    print(row[0])
conn.close()
