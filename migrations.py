import sqlite3

conn = sqlite3.connect("utente.db")
cursor = conn.cursor()

cursor.execute("""
               ALTER TABLE utenti ADD COLUMN budget REAL CHECK (budget >= 0);
               """)
conn.commit()
conn.close()