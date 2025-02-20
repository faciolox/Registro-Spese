import sqlite3
def main():
    conn = sqlite3.connect("utente.db")
    cursor = conn.cursor()
    # Controlla se la colonna "budget" esiste
    cursor.execute("PRAGMA table_info(utenti);")
    columns = [row[1] for row in cursor.fetchall()]

    if "budget" not in columns:
        cursor.execute("""
            ALTER TABLE utenti ADD COLUMN budget REAL CHECK (budget >= 0);
        """)
        print("Column added successfully")
        conn.commit()
    conn.close()
    