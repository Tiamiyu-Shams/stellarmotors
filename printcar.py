import sqlite3

conn = sqlite3.connect("cars.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(cars);")
for column in cursor.fetchall():
    print(column)

conn.close()
