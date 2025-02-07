from datetime import datetime


class Entrate:
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
        return f"{self.descrizione} | {self.timestamp} | Importo: {self.importo}€"

    def to_dict(self):
        return {"Orario": self.timestamp, "Descrizione": self.descrizione, "Importo": self.importo}



def add_entrata(json_entrate: [Entrate], entrata ,descrizione = None):
    entr= Entrate(entrata, descrizione)
    json_entrate.append(entr.to_dict())
    return entr

def get_entrate_mensile(json_entrate: [Entrate], mese = None, anno = datetime.now().year):
    # Definizione range
    out = []
    totale = 0
    now = datetime.today()

    if not (mese):

        mese = now.month

    elif mese == 0:
        mese = 12
        anno = anno - 1
    giorno = now.day
    if giorno < 8:
        if mese == 1:
            mese = 12
            anno = anno - 1
        else:
            mese -= 1
    inizio, fine = datetime(anno, mese, 8), datetime(anno if mese < 12 else anno + 1, (mese % 12) + 1, 8)
    for v in json_entrate:
        if inizio <= datetime.strptime(v["Orario"], "%d/%m/%Y %H:%M") < fine:
            sp = Entrate(v["Importo"], v["Descrizione"], datetime.strptime(v["Orario"], "%d/%m/%Y %H:%M"))
            out.append(sp)
            totale += v["Importo"]
    tot = Entrate(totale, 'Totale entrate:')
    out.append(tot)
    return out