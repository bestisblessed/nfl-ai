import sqlite3

db_path = 'data/nfl.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
total_rows_before = cursor.execute("SELECT COUNT(*) FROM Rosters").fetchone()[0]
sanitize_query = "UPDATE Rosters SET smart_id = NULL"
cursor.execute(sanitize_query)
conn.commit()
total_rows_after = cursor.execute("SELECT COUNT(*) FROM Rosters").fetchone()[0]
result = cursor.execute("SELECT smart_id FROM Rosters LIMIT 10").fetchall()
print(f"Total rows before sanitization: {total_rows_before}")
print(f"Total rows after sanitization: {total_rows_after}")
print("Sanitized rows:", result)
cursor.close()
conn.close()
print("Sanitization complete! The `smart_id` column has been cleared.")

