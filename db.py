from datetime import datetime, timedelta
import sqlite3
import json
import spese, entrate, errors
from typing import List
def init_db() -> None:
    """
    Inizializza il database creando le tabelle se non esistono
    Crea tabella utente, spese, entrate, spese_cc
    
    Returns:
        None: La funziona ritorna nulla
    """
    
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
    
def create (utente:str) -> None:
    """
    Crea un utente nel database
    
    Args:
        utente (str): Nome dell'utente da creare
    
    Returns:
        None: La funzione ritorna nulla
    
    Raises:
        errors.CreateUserError: Se l'utente è già presente nel database
    """
    conn = sqlite3.connect("utente.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""INSERT INTO utenti (utente) VALUES (?)""",(utente,))
    except sqlite3.IntegrityError as e:
        raise errors.CreateUserError(f"Utente {utente} già esistente")
    conn.commit()
    conn.close()

def adapt_datetime(dt:datetime) -> str:
    """
    Adatta la data per il database
    
    Args:
        dt (datetime): Data da adattare
        
    Returns:
        str: La data adattata per il database
    """
    return dt.strftime("%Y/%m/%d %H:%M:%S")
 
def convert_datetime(dt:str) -> datetime:
    """
    Converte la data dal database

    Args:
        dt (str): Data da convertire

    Returns:
        datetime: La data convertita
    """
    return datetime.strptime(dt,"%Y/%m/%d %H:%M:%S")
 
def trasferisci_json(file: str = 'Registri/registri.json') -> None:
    """
    [DEPRECATO] Trasferisce i dati dal file json al database
    
    Args:
        file (str): File json da cui trasferire i dati
    
    Returns:
        None: La funzione ritorna nulla"""
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

def salva_spesa(utente_id: str, descrizione:str, importo:float, ts:datetime) -> None:
    """
    Salva una spesa nel database
    
    Args:
        utente_id (str): ID dell'utente
        descrizione (str): Descrizione della spesa
        importo (int): Importo della spesa
        data (datetime): Data della spesa
    
    Returns:
        None: La funzione ritorna nulla
        
    Raises:
        errors.DescriptionError: Se la descrizione è "Addebito carta di credito"
    """
    if descrizione == "Addebito carta di credito":
        raise errors.DescriptionError("Descrizione non valida, utilizzare la funzione apposita per la carta di credito")
    conn = sqlite3.connect("spese.db")
    cursor = conn.cursor()
    if type(ts) == str:
        ts = datetime.strptime(ts,"%Y/%m/%d %H:%M:%S")
    ts = ts.strftime("%Y/%m/%d %H:%M:%S")
    cursor.execute("""
                    INSERT INTO spese (utente,  descrizione, importo, data) VALUES (?, ? ,?, ?)
                    """, (utente_id, descrizione, importo, ts))
    conn.commit()
    conn.close()
 
def salva_entrata(utente_id:str, descrizione:str, importo:float, data:datetime) -> None:
    """
    Salva un'entrata nel database
    
    Args:
        utente_id (str): ID dell'utente
        descrizione (str): Descrizione dell'entrata
        importo (int): Importo dell'entrata
        data (datetime): Data dell'entrata
        
    Returns:
        None: La funzione ritorna nulla
    """
    conn = sqlite3.connect("entrate.db")
    cursor = conn.cursor()
    ts = ts.strftime("%Y/%m/%d %H:%M:%S")
    cursor.execute("""
                    INSERT INTO entrate (utente,  descrizione, importo, data) VALUES (?, ? ,?, ?)
                    """, (utente_id, descrizione, importo, ts))
    conn.commit()
    conn.close()
    
def get_spesa(utente_id: str, fine :datetime = datetime.now(),inizio :datetime =None) -> list[spese.Spesa]:
    """
    Restituisce le spese di un utente
    
    Args:
        utente_id (str): ID dell'utente
        fine (datetime): Data di fine
        inizio (datetime): Data di inizio
        
    Returns:
        list[spese.Spesa]: Lista delle spese dell'utente
    """
    
    sqlite3.register_adapter(datetime,adapt_datetime)
    sqlite3.register_converter("datetime",convert_datetime)
    
    out = []
    if inizio == None:
        inizio = fine - timedelta(days=30)
    conn = sqlite3.connect("spese.db")
    if type(inizio) == datetime:
        inizio = adapt_datetime(inizio)
    if type(fine) == datetime:
        fine = adapt_datetime(fine)
    cursor = conn.cursor()
    
    cursor.execute("""
                   SELECT * FROM spese WHERE data BETWEEN ? AND ? AND utente = ?
                   """, (inizio,fine,utente_id))
    
    risultati = cursor.fetchall()
    totale = 0
    for riga in risultati:
        spesa = spese.Spesa(riga[3],riga[2],riga[4],riga[0])
        out.append(spesa)
        totale += spesa.importo
    spesa = spese.Spesa(totale, "Totale", fine)
    out.append(spesa)
    
    return out

def get_entrata(utente_id: str, fine: datetime =datetime.now(),inizio: datetime=None) -> list[entrate.Entrate]:
    """
    Data un inizio e una fine restituisce le entrate di un utente
    
    Args:
        utente_id (str): ID dell'utente
        fine (datetime): Data di fine
        inizio (datetime): Data di inizio
        
    Returns:
        list[entrate.Entrate]: Lista delle entrate dell'utente
    """
    
    
    out = []
    
    if inizio == None:
        inizio = fine - timedelta(days=30)
    conn = sqlite3.connect("entrate.db")
    if type(inizio) == datetime:
        inizio = adapt_datetime(inizio)
    if type(fine) == datetime:
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

def add_spesa_cc(utente: str,importo:float ,descrizione:str = '',data:datetime = datetime.now(), mensilita:int=1 ) -> None:
    """
    Aggiunge una spesa di tipo carta di credito e aggiunge le varie rate agli addebiti del relativo mese
    
    Args:
        utente (str): ID dell'utente
        importo (float): Importo della spesa
        descrizione (str): Descrizione della spesa
        data (datetime): Data della spesa
        mensilita (int): Numero di rate
    
    Returns:
        None: La funzione ritorna nulla
    """
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
                importo_rata = round(addebbiti_cc[3] + (importo/mensilita),2)
                cursor.execute("""
                    UPDATE spese SET importo = ? WHERE id_spesa = ?
                    """,(importo_rata ,addebbiti_cc[0]))
                found = True
                break
        if not found:
            cursor.execute("""
                    INSERT INTO spese (utente,  descrizione, importo, data) VALUES (?, ? ,?, ?)
                    """, (utente, "Addebito carta di credito", round(importo/mensilita,2), ts_addebito))
    conn.commit()
    conn.close()

def get_spesa_cc(utente_id, fine=datetime.now(),inizio=None) -> List[spese.SpesaCc]:
    out = []
    spesa = spese.SpesaCc
    if inizio == None:
        inizio = fine - timedelta(days=30)
    conn = sqlite3.connect("spese_cc.db")
    if type(inizio) == datetime:
        inizio = adapt_datetime(inizio)
    if type(fine) == datetime:
        fine = adapt_datetime(fine)
    cursor = conn.cursor()
    
    cursor.execute("""
                   SELECT * FROM spese_cc WHERE data BETWEEN ? AND ? AND utente = ?
                   """, (inizio,fine,utente_id))
    
    risultati = cursor.fetchall()
    totale = 0
    for riga in risultati:
        spesa = spese.SpesaCc(riga[3],riga[2],riga[4],riga[5],riga[0])
        out.append(spesa)
        totale += spesa.importo
    spesa = spese.SpesaCc(totale, "Totale", fine,0)
    out.append(spesa)
    return out
    
def get_saldo(utente:str) -> float:
    """
    Restituisce il saldo dell'utente previsto il prossimo 8 del mese
    
    Args:
        utente (str): ID dell'utente
        
    Returns:
        float: Saldo dell'utente
    """
    
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

def set_budget(utente: str, budget: float) -> None:
    """
    Imposta il budget dell'utente
    
    Args:
        utente (str): ID dell'utente
        budget (float): Budget dell'utente
        
    Returns:
        None: La funzione ritorna nulla
    """
    
    conn = sqlite3.connect("utente.db")
    cursor = conn.cursor()
    cursor.execute("""
                   UPDATE utenti SET budget = ? WHERE utente = ?
                   """, (budget, utente))
    conn.commit()
    conn.close()

def get_budget(utente:str) -> float:
    """
    Restituisce il budget dell'utente
    
    Args:
        utente (str): ID dell'utente
        
    Returns:
        float: Budget dell'utente
    """
    conn = sqlite3.connect("utente.db")
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT budget FROM utenti WHERE utente = ?
                   """, (utente,))
    risultato = cursor.fetchone()
    conn.close()
    if risultato == None:
        return None
    else:
        return risultato[0]

def get_addebito(utente:str, mese: int) -> spese.Spesa:
    """Dato un utente restituisce il prossimo addebito relativo alla carta di credito

    Args:
        utente (str): username dell'utente

    Returns:
        spese.Spesa: Prossimo addebito
    
    Raises:
        errors.NoAddebitoError: Se non è presente nessun addebito per l'utente
    """
    data_addebito = datetime(datetime.now().year, mese, 4, 23, 59, 59)
    
    conn = sqlite3.connect("spese.db")
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT * FROM spese WHERE utente = ? AND descrizione = "Addebito carta di credito" AND data = ? ORDER BY data ASC LIMIT 1
                   """, (utente,data_addebito.strftime("%Y/%m/%d %H:%M:%S")))
    risultato = cursor.fetchone()
    conn.close()
    
    if risultato == None:
        raise errors.NoAddebitoError("Nessun addebito trovato")
    else:
        return spese.Spesa(risultato[3], risultato[2], risultato[4], risultato[0])
        
def delete_budget(utente:str) -> None:
    """
    Elimina il budget dell'utente
    
    Args:
        utente (str): ID dell'utente
        
    Returns:
        None: La funzione ritorna nulla
    """
    conn = sqlite3.connect("utente.db")
    cursor = conn.cursor()
    cursor.execute("""
                   UPDATE utenti SET budget = NULL WHERE utente = ?
                   """, (utente,))
    conn.commit()
    conn.close()
    
def delete_spesa(utente:str, id_spesa:int) -> None:
    """
    Elimina una spesa
    
    Args:
        utente (str): ID dell'utente
        id_spesa (int): ID della spesa
        
    Returns:
        None: La funzione ritorna nulla
    
    Raises:
        errors.DeleteError: Se si verifica un errore durante l'eliminazione della spesa
    """
    conn = sqlite3.connect("spese.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
                    DELETE FROM spese WHERE utente = ? AND id_spesa = ?
                    """, (utente,id_spesa))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError as e:
        raise errors.DeleteError(f"Errore durante l'eliminazione della spesa {id_spesa}")

def delete_entrata(utente:str, id_entrata: int) -> None:
    """
    Elimina un'entrata
    
    Args:
        utente (str): ID dell'utente
        id_entrata (int): ID dell'entrata
        
    Returns:
        None: La funzione ritorna nulla
    
    Raises:
        errors.DeleteError: Se si verifica un errore durante l'eliminazione dell'entrata
    """
    conn = sqlite3.connect("entrate.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
                    DELETE FROM entrate WHERE utente = ? AND id_entrata = ?
                    """, (utente,id_entrata))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError as e:
        raise errors.DeleteError(f"Errore durante l'eliminazione dell'entrata {id_entrata}")
def get_spesa_with_id(id_spesa:int) -> spese.Spesa:
    """
    Restituisce una spesa dato il suo ID
    
    Args:
        id_spesa (int): ID della spesa
        
    Returns:
        spese.Spesa: Spesa con l'ID specificato
    """
    conn = sqlite3.connect("spese.db")
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT * FROM spese WHERE id_spesa = ?
                   """, (id_spesa,))
    risultato = cursor.fetchone()
    conn.close()
    return spese.Spesa(risultato[3], risultato[2], risultato[4], risultato[0])
  
def modifica_spesa(utente:str, id_spesa:int, nuovo_importo: float) -> spese.Spesa:
    """
    Modifica l'importo di una spesa
    
    Args:
        utente (str): ID dell'utente
        id_spesa (int): ID della spesa
        nuovo_importo (float): Nuovo importo della spesa
    
    Returns:
        spese.Spesa: Spesa modificata
    """
    conn = sqlite3.connect("spese.db")
    cursor = conn.cursor()
    cursor.execute("""
                   UPDATE spese SET importo = ? WHERE utente = ? AND id_spesa = ?
                   """, (nuovo_importo, utente, id_spesa))
    conn.commit()
    conn.close()
    return get_spesa_with_id(id_spesa)

def modifica_spesa_cc(utente:str, id_spesa:int, nuovo_importo: float) -> spese.SpesaCc:
    """
    Modifica l'importo di una spesa di carta di credito
    
    Args:
        utente (str): ID dell'utente
        id_spesa (int): ID della spesa
        nuovo_importo (float): Nuovo importo della spesa
    
    Returns:
        spese.SpesaCc: Spesa di carta di credito modificata
    """
    spesa_cc = get_spesa_cc(id_spesa,utente)
    vecchio_importo = spesa_cc.importo
    conn = sqlite3.connect("spese_cc.db")
    cursor = conn.cursor()
    cursor.execute("""
                   UPDATE spese_cc SET importo = ? WHERE utente = ? AND id_spesa = ?
                   """, (nuovo_importo, utente, id_spesa))
    conn.commit()
    conn.close()
    spesa_cc.importo = nuovo_importo
    differenza = vecchio_importo - nuovo_importo
    
    for i in range(1, spesa_cc.mensilità+1):
        addebito = get_addebito(utente, (spesa_cc.timestamp.month+i)%12)
        addebito.importo = round( addebito.importo - (vecchio_importo/spesa_cc.mensilità) + (nuovo_importo/spesa_cc.mensilità),2)
        if addebito.importo < 0:
            addebito.importo = 0
        addebito = modifica_spesa(utente, addebito.id, addebito.importo)
    return spesa_cc  
    
def get_spesa_cc(id_spesa: int, utente: str) -> spese.SpesaCc:
    """
    Restituisce una spesa di carta di credito dato il suo ID
    
    Args:
        id_spesa (int): ID della spesa
        utente (str): ID dell'utente
    
    Returns:
        spese.SpesaCc: Spesa di carta di credito con l'ID specificato
    
    Raises:
        errors.NoSpesaError: Se la spesa non è presente
    """  
    conn = sqlite3.connect("spese_cc.db")
    cursor = conn.cursor()
    cursor.execute("""
                    SELECT * FROM spese_cc WHERE id_spesa = ? AND utente = ?
                    """, (id_spesa,utente))
    risultato = cursor.fetchone()
    conn.close()
    if risultato == None:
        raise errors.NoSpesaError(f"Spesa {id_spesa} non trovata")
    else:
        return spese.SpesaCc(risultato[3], risultato[2], risultato[4], risultato[5], risultato[0])

        
def delete_spesa_cc(utente:str, id_spesa:int) -> None:
    """
    Elimina una spesa di carta di credito
    
    Args:
        utente (str): ID dell'utente
        id_spesa (int): ID della spesa
        
    Returns:
        None: La funzione ritorna nulla
    
    Raises:
        errors.DeleteError: Se si verifica un errore durante l'eliminazione della spesa
        errors.NoSpesaError: Se la spesa non è presente
    """
    try:
        spesa_cc = get_spesa_cc(id_spesa,utente)
        for i in range(1, spesa_cc.mensilità+1):
            addebito = get_addebito(utente, (spesa_cc.timestamp.month+i)%12)
            addebito.importo -= round(spesa_cc.importo/spesa_cc.mensilità,2)
            if addebito.importo < 0:
                addebito.importo = 0
            addebito = modifica_spesa(utente, addebito.id, addebito.importo)
        conn = sqlite3.connect("spese_cc.db")
        cursor = conn.cursor()
        try:
            cursor.execute("""
                        DELETE FROM spese_cc WHERE utente = ? AND id_spesa = ?
                        """, (utente,id_spesa))
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError as e:
            raise errors.DeleteError(f"Errore durante l'eliminazione della spesa {id_spesa}")   
    
    except errors.NoSpesaError:
        raise errors.NoSpesaError(f"Spesa {id_spesa} non trovata")


ora = datetime.now().strftime("%Y/%m/%d %H:%M:%S")




