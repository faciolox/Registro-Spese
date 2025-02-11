from datetime import datetime, timedelta
import sqlite3
import json
import spese, entrate
def init_db():
    conn = sqlite3.connect("spese.db")  # Crea il file del database
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS spese (
            id_spesa INTEGER PRIMARY KEY AUTOINCREMENT,
            utente_id TEXT,
            descrizione TEXT,
            importo REAL,
            data DATETIME
        )
    """)

    conn.commit()
    conn.close()
    
    conn = sqlite3.connect("entrate.db")  # Crea il file del database
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entrate (
            id_entrata INTEGER PRIMARY KEY AUTOINCREMENT,
            utente_id TEXT,
            descrizione TEXT,
            importo REAL,
            data DATETIME
        )
    """)

    conn.commit()
    conn.close()
    

def adapt_datetime(dt):
    return dt.strftime("%d/%m/%Y %H:%M:%S")
 
def convert_datetime(dt):
    return datetime.strptime(dt,"%d/%m/%Y %H:%M:%S")
 
def trasferisci_json(file = 'Registri/registri.json'):
    with open(file, 'r') as f:
        json_reg = json.load(f)
    conn = sqlite3.connect("spese.db")
    cursor = conn.cursor()
    conn2 =  sqlite3.connect("entrate.db")
    cursor2 = conn2.cursor()
    for utente, registri in json_reg.items():
        for spese in registri["Spese"]:
            ts = datetime.strptime(spese["Orario"],"%d/%m/%Y %H:%M")
            ts = ts.strftime("%d/%m/%Y %H:%M:%S")
            cursor.execute("""
                    INSERT INTO spese (utente_id,  descrizione, importo, data) VALUES (?, ? ,?, ?)
                    """, (utente, spese["Descrizione"], spese["Importo"], ts))
        for entrate in registri["Entrate"]:
            ts = datetime.strptime(spese["Orario"],"%d/%m/%Y %H:%M")
            ts = ts.strftime("%d/%m/%Y %H:%M:%S")
            cursor2.execute("""
                    INSERT INTO entrate (utente_id,  descrizione, importo, data) VALUES (?, ? ,?, ?)
                    """, (utente, spese["Descrizione"], spese["Importo"], ts))
    conn.commit()
    conn2.commit()
    conn.close()
    conn2.close()


def salva_spesa(utente_id, descrizione, importo, data):
    conn = sqlite3.connect("spese.db")
    cursor = conn.cursor()
    ts = datetime.strptime(data,"%d/%m/%Y %H:%M")
    ts = ts.strftime("%d/%m/%Y %H:%M:%S")
    cursor.execute("""
                    INSERT INTO spese (utente_id,  descrizione, importo, data) VALUES (?, ? ,?, ?)
                    """, (utente_id, descrizione, importo, ts))
    conn.commit()
    conn.close()
 
def salva_entrata(utente_id, descrizione, importo, data):
    conn = sqlite3.connect("entrate.db")
    cursor = conn.cursor()
    ts = datetime.strptime(data,"%d/%m/%Y %H:%M")
    ts = ts.strftime("%d/%m/%Y %H:%M:%S")
    cursor.execute("""
                    INSERT INTO entrate (utente_id,  descrizione, importo, data) VALUES (?, ? ,?, ?)
                    """, (utente_id, descrizione, importo, ts))
    conn.commit()
    conn.close()
    
def get_spesa(utente_id, fine=datetime.now(),inizio=None):
    sqlite3.register_adapter(datetime,adapt_datetime)
    sqlite3.register_converter("datetime",convert_datetime)
    
    out = []
    if inizio == None:
        inizio = fine - timedelta(days=30)
    conn = sqlite3.connect("spese.db")
    cursor = conn.cursor()
    
    cursor.execute("""
                   SELECT * FROM spese WHERE data BETWEEN ? AND ? AND utente_id = ?
                   """, (inizio,fine,utente_id))
    
    risultati = cursor.fetchall()
    totale = 0
    for riga in risultati:
        spesa = spese.Spesa(riga[3],riga[2],riga[4])
        out.append(spesa)
        totale += spesa[3]
    spesa = spese.Spesa(totale, "Totale", fine)
    return out

def get_entrata(utente_id, fine=datetime.now(),inizio=None):
    sqlite3.register_adapter(datetime,adapt_datetime)
    sqlite3.register_converter("datetime",convert_datetime)
    out = []
    if inizio == None:
        inizio = fine - timedelta(days=30)
    conn = sqlite3.connect("entrate.db")
    cursor = conn.cursor()
    
    cursor.execute("""
                   SELECT * FROM entrate WHERE data BETWEEN ? AND ?
                   """, (inizio,fine))
    
    risultati = cursor.fetchall()
    totale = 0
    for riga in risultati:
        spesa = entrate.Entrate(riga[3],riga[2],riga[4])
        out.append(spesa)
        totale += spesa[3]
    spesa = entrate.Entrate(totale, "Totale", fine)
    return out


print(get_entrata("Faciolo"))
print(get_spesa("Faciolo"))
