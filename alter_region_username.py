import sqlite3

conn = sqlite3.connect("database.db")

try:
    conn.execute("ALTER TABLE regions ADD COLUMN username VARCHAR")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_regions_username ON regions(username)")
    conn.commit()
    print("username ustuni muvaffaqiyatli qo'shildi.")
except sqlite3.OperationalError as e:
    print("Xatolik yoki ustun allaqachon mavjud:", e)
finally:
    conn.close()