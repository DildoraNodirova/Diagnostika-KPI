import sqlite3

conn = sqlite3.connect("database.db")

try:
    conn.execute("ALTER TABLE kpi_results ADD COLUMN period VARCHAR")
    print("period ustuni qo'shildi.")
except sqlite3.OperationalError as e:
    print("Xatolik yoki ustun allaqachon mavjud:", e)

try:
    conn.execute("UPDATE kpi_results SET period = substr(date, 1, 7) WHERE period IS NULL")
    conn.commit()
    print("Eski natijalar uchun period (oy) to'ldirildi.")
except sqlite3.OperationalError as e:
    print("Xatolik:", e)

conn.close()