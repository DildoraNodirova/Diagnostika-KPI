import sqlite3

conn = sqlite3.connect("database.db")

try:
    conn.execute("ALTER TABLE departments ADD COLUMN status VARCHAR DEFAULT 'Active'")
    conn.execute("UPDATE departments SET status = 'Active' WHERE status IS NULL")
    conn.commit()
    print("status ustuni qo'shildi.")
except sqlite3.OperationalError as e:
    print("Xatolik yoki ustun allaqachon mavjud:", e)

conn.close()