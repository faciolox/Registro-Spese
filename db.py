from datetime import datetime, timedelta
import sqlite3
import json
import spese, entrate, errors
def init_db():
    
    conn = sqlite3.connect("utente.db")
    cursor = conn.cursor()
    
    cursor.execute( """
                   CREATE TABLE IF NOT EXISTS utenti(
                     utente TEXT PRIMARY KEY)
                   """)
    
    conn.commit()
    conn.close()
    
    conn = sqlite3.connect("spese.db")  # Crea il file del database
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS spese (
            id_spesa INTEGER PRIMARY KEY AUTOINCREMENT,
            utente TEXT,
            descrizione TEXT,
            importo REAL,
            data text,
            FOREIGN KEY (utente) REFERENCES utenti(utente)
        )
    """)

    conn.commit()
    conn.close()
    
    conn = sqlite3.connect("spese_cc.db")  # Crea il file del database
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS spese_cc (
            id_spesa INTEGER PRIMARY KEY autoincrement,
            utente TEXT,
            descrizione TEXT,
            importo REAL,
            data text,
            mensilita INTEGER CHECK (mensilita > 0),
            FOREIGN KEY (utente) REFERENCES utenti(utente)
        )
    """)

    conn.commit()
    conn.close()
    
    
    
    conn = sqlite3.connect("entrate.db")  # Crea il file del database
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entrate (
            id_entrata INTEGER PRIMARY KEY AUTOINCREMENT,
            utente TEXT,
            descrizione TEXT,
            importo REAL,
            data text,
            FOREIGN KEY (utente) REFERENCES utenti(utente)
        )
    """)

    conn.commit()
    conn.close()
    
def create (utente):
    conn = sqlite3.connect("utente.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""INSERT INTO utenti (utente) VALUES (?)""",(utente,))
    except sqlite3.IntegrityError as e:
        print(f"{e}\nUtente già esistente")
    conn.commit()
    conn.close()





def adapt_datetime(dt):
    return dt.strftime("%Y/%m/%d %H:%M:%S")
 
def convert_datetime(dt):
    return datetime.strptime(dt,"%Y/%m/%d %H:%M:%S")
 
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
            ts = ts.strftime("%Y/%m/%d %H:%M:%S")
            cursor.execute("""
                    INSERT INTO spese (utente,  descrizione, importo, data) VALUES (?, ? ,?, ?)
                    """, (utente, spese["Descrizione"], spese["Importo"], ts))
        for entrate in registri["Entrate"]:
            ts = datetime.strptime(spese["Orario"],"%d/%m/%Y %H:%M")
            ts = ts.strftime("%Y/%m/%d %H:%M:%S")
            cursor2.execute("""
                    INSERT INTO entrate (utente,  descrizione, importo, data) VALUES (?, ? ,?, ?)
                    """, (utente, entrate["Descrizione"], entrate["Importo"], ts))
    conn.commit()
    conn2.commit()
    conn.close()
    conn2.close()


def salva_spesa(utente_id, descrizione, importo, data):
    if descrizione == "Addebito carta di credito":
        raise errors.DescriptionError("Descrizione non valida, utilizzare la funzione apposita per la carta di credito")
    conn = sqlite3.connect("spese.db")
    cursor = conn.cursor()
    ts = datetime.strptime(data,"%Y/%m/%d %H:%M:%S")
    ts = ts.strftime("%Y/%m/%d %H:%M:%S")
    cursor.execute("""
                    INSERT INTO spese (utente,  descrizione, importo, data) VALUES (?, ? ,?, ?)
                    """, (utente_id, descrizione, importo, ts))
    conn.commit()
    conn.close()
 
def salva_entrata(utente_id, descrizione, importo, data):
    conn = sqlite3.connect("entrate.db")
    cursor = conn.cursor()
    ts = datetime.strptime(data,"%Y/%m/%d %H:%M:%S")
    ts = ts.strftime("%Y/%m/%d %H:%M:%S")
    cursor.execute("""
                    INSERT INTO entrate (utente,  descrizione, importo, data) VALUES (?, ? ,?, ?)
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
    inizio = adapt_datetime(inizio)
    fine = adapt_datetime(fine)
    cursor = conn.cursor()
    
    cursor.execute("""
                   SELECT * FROM spese WHERE data BETWEEN ? AND ? AND utente = ?
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
    out = []
    
    if inizio == None:
        inizio = fine - timedelta(days=30)
    conn = sqlite3.connect("entrate.db")
    inizio = adapt_datetime(inizio)
    fine = adapt_datetime(fine)
    cursor = conn.cursor()
    
    cursor.execute("""
                   SELECT * FROM entrate WHERE data BETWEEN ? AND ? AND utente = ?
                   """, (inizio,fine,utente_id))
    
    risultati = cursor.fetchall()
    totale = 0
    for riga in risultati:
        spesa = entrate.Entrate(riga[3],riga[2],riga[4])
        out.append(spesa)
        totale += spesa.importo
    spesa = entrate.Entrate(totale, "Totale", fine)
    out.append(spesa)
    return out

def add_spesa_cc(utente,importo,descrizione = '',data = datetime.now(), mensilita=1 ):
    conn = sqlite3.connect("spese_cc.db")
    cursor = conn.cursor()
    if type(data) == str:
        ts = datetime.strptime(data,"%Y/%m/%d %H:%M:%S")
        ts = ts.strftime("%Y/%m/%d %H:%M:%S")
    else:
        ts = data.strftime("%Y/%m/%d %H:%M:%S")

    cursor.execute("""
                    INSERT INTO spese_cc (utente,  descrizione, importo, data, mensilita) VALUES (?, ? ,?, ?, ?)
                    """, (utente, descrizione, importo, ts, mensilita))
    conn.commit()
    conn.close()
    
    conn = sqlite3.connect("spese.db")
    cursor = conn.cursor()
    ts_dt = datetime.strptime(ts,"%Y/%m/%d %H:%M:%S")
    if ts_dt.day < 8:
        ts_dt.day = 9
        ts = ts_dt.strftime("%Y/%m/%d %H:%M:%S")
    cursor.execute("""
                   SELECT * FROM spese WHERE utente  = ? AND data > ? and descrizione = ? ORDER BY data ASC """
                   ,(utente,ts,"Addebito carta di credito"))
    risultati = cursor.fetchall()
    for i in range(1,mensilita+1):
        found = False
        if ts_dt.month + i > 12:
            ts_dt.month = 1
            ts_dt.year += 1
            ts_addebito = datetime(ts_dt.year+1,1,4,23,59,59).strftime("%Y/%m/%d %H:%M:%S")
        else:
            ts_addebito = datetime(ts_dt.year,ts_dt.month+i,4,23,59,59).strftime("%Y/%m/%d %H:%M:%S")
        for addebbiti_cc in risultati:
            if addebbiti_cc[4] == ts_addebito:
                importo = round(addebbiti_cc[3] + (importo/mensilita),2)
                cursor.execute("""
                    UPDATE spese SET importo = ? WHERE id_spesa = ?
                    """,(importo ,addebbiti_cc[0]))
                found = True
                break
        if not found:
            cursor.execute("""
                    INSERT INTO spese (utente,  descrizione, importo, data) VALUES (?, ? ,?, ?)
                    """, (utente, "Addebito carta di credito", round(importo/mensilita,2), ts_addebito))
    conn.commit()
    conn.close()
    
def get_saldo(utente):
    fine = datetime.now()
    if fine.day >= 8:
        if fine.month == 12:

            fine = datetime(fine.year + 1, 1,fine.day,fine.hour,fine.minute,fine.second)
        else:
            fine = datetime(fine.year, fine.month+1,fine.day,fine.hour,fine.minute,fine.second)
    else:
        fine = datetime(fine.year, fine.month, 8, fine.hour, fine.minute, fine.second)
    fine = fine.strftime("%Y/%m/%d %H:%M:%S")
    inizio = datetime(1900, 1,1,0,0,0).strftime("%Y/%m/%d %H:%M:%S")
    
    conn = sqlite3.connect("spese.db")
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT * FROM spese WHERE utente = ? AND data BETWEEN ? AND ?
                   """, (utente,inizio,fine))
    risultati = cursor.fetchall()
    totale_spese = 0
    for spesa in risultati:
        totale_spese += spesa[3]
    conn.close()
    conn = sqlite3.connect("entrate.db")
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT * FROM entrate WHERE utente = ?AND data BETWEEN ? AND ?
                   """, (utente,inizio,fine))
    risultati = cursor.fetchall()
    totale_entrate = 0
    for entrata in risultati:
        totale_entrate += entrata[3]
    conn.close()
    return totale_entrate - totale_spese

  
init_db()       
create("Faciolo")
salva_entrata("Faciolo","Stipendio", 1300, "2025/02/13 14:59:00")
add_spesa_cc("Faciolo",1000,"tv","2025/02/13 14:59:00",6)
add_spesa_cc("Faciolo",100, "cena")
print(get_saldo("Faciolo"))