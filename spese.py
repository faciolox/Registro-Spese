from datetime import datetime


class Spesa:
    def __init__(self, importo, descrizione = None, timestamp = None ):
        self.importo = importo
        if not(descrizione):
            self.descrizione = ''
        else:
            self.descrizione = descrizione
        if not(timestamp):
            self.timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        else:

            self.timestamp = timestamp.strftime("%d/%m/%Y %H:%M")

    def get_datetime(self):
        return datetime.strptime(self.timestamp, "%d/%m/%Y %H:%M")

    def __str__(self):
        return f"Spesa: {self.descrizione} | {self.timestamp} | Importo: {self.importo}€"

    def to_dict(self):
        return {"Orario": self.timestamp, "Descrizione": self.descrizione, "Importo": self.importo}



def get_spesa_mensile(json_spese: [Spesa], mese = None):
    # Definizione range
    out = []
    totale = 0
    if not (mese):
        now = datetime.today()
        anno = now.year
        mese = now.month
        giorno = now.day
        if giorno < 8:
            if mese == 1:
                mese = 12
                anno = anno -1
            else:
                mese -= 1
    inizio, fine = datetime(anno, mese, 8), datetime(anno if mese < 12 else anno + 1, (mese % 12) + 1, 8)
    for v in json_spese:
        if inizio <= datetime.strptime(v["Orario"], "%d/%m/%Y %H:%M") < fine:
            sp = Spesa(v["Importo"], v["Descrizione"], v["Orario"])
            out.append(sp.to_dict())
            totale += v["Importo"]
    tot = Spesa(totale, 'Totale:')
    out.append(tot)
    return out

def add_spesa(json_spese: [Spesa], spesa, descrizione = None):
    spesa = Spesa(spesa, descrizione)
    json_spese.append(spesa.to_dict())
    return spesa

def get_spesa_intervallo(json_spese: [Spesa], inizio, fine = datetime.now()):
    totale = 0
    for v in json_spese:
        if inizio <= datetime.strptime(v["Orario"], "%d/%m/%Y %H:%M") < fine:
            totale += v["Importo"]
    tot = Spesa(totale, 'Totale:')
    return tot