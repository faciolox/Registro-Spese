from datetime import datetime


class Spesa:
    def __init__(self, importo, descrizione = None, timestamp = None ):
        self.importo = importo
        if not(descrizione):
            self.descrizione = ''
        else:
            self.descrizione = descrizione
        if not(timestamp):
            self.timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        
        elif type(timestamp) == str:
            
            try:
                datetime.strptime(timestamp, "%Y/%m/%d %H:%M:%S")
                self.timestamp = timestamp
            except:
                try:
                    data, orario = timestamp.split(" ")
                    anno, mese, giorno = data.split("/")
                    self.timestamp = f"{giorno}/{mese}/{anno} {orario}"
                except:
                    raise ValueError("Timestamp non valido")
        else:

            self.timestamp = timestamp.strftime("%Y/%m/%d %H:%M:%S")

    def get_datetime(self):
        return datetime.strptime(self.timestamp, "%Y/%m/%d %H:%M:%S")

    def __str__(self):
        return f"{self.descrizione} | {self.timestamp} | Importo: {self.importo}€"

    def to_dict(self):
        return {"Orario": self.timestamp, "Descrizione": self.descrizione, "Importo": self.importo}



def get_spesa_mensile(json_spese: [Spesa], mese = None, anno = datetime.now().year):
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
    for v in json_spese:
        if inizio <= datetime.strptime(v["Orario"], "%Y/%m/%d %H:%M:%S") < fine:
            sp = Spesa(v["Importo"], v["Descrizione"], datetime.strptime(v["Orario"], "%Y/%m/%d %H:%M:%S"))
            out.append(sp)
            totale += v["Importo"]
    tot = Spesa(totale, 'Totale spese:')
    out.append(tot)
    return out

def add_addebito_cc(json_spese:[Spesa],spesa,mensilità):
    rata = spesa / mensilità
    out = 0
    month = datetime.today().month
    year = datetime.today().year
    for i in range(0, mensilità):
        found = False
        m = i + month
        if i + month > 12:
            m -= 12
            for j in json_spese:
                if datetime.strptime(j["Orario"], "%Y/%m/%d %H:%M:%S").month + 1== m and j["Descrizione"]== "Addebito c/c" and datetime.strptime(j["Orario"], "%Y/%m/%d %H:%M:%S").year == year:
                    j["Importo"] += spesa
                    found = True
                    break
            if not found:
                sp = Spesa(rata,"Addebito c/c",datetime(year,m + 1,4,23,59))
                json_spese.append(sp) 
        else:
            for j in json_spese:
                if datetime.strptime(j["Orario"], "%Y/%m/%d %H:%M:%S").month + 1 == m and j["Descrizione"] == "Addebito c/c" and datetime.strptime(j["Orario"], "%Y/%m/%d %H:%M:%S").year == year:
                    j["Importo"] += spesa
                    found = True
                    break
            if not found:
                if m + 1 == 13:
                    sp = Spesa(rata,"Addebito c/c",datetime(year,1,4,23,59))
                else:
                    sp = Spesa(rata,"Addebito c/c",datetime(year,m +1,4,23,59))
                json_spese.append(sp.to_dict()) 

def add_spesa(json_spese: [Spesa], spesa,descrizione = None):
    spesa = Spesa(spesa, descrizione)
    json_spese.append(spesa.to_dict())
    return spesa

def get_spesa_intervallo(json_spese: [Spesa], inizio, fine = datetime.now()):
    totale = 0
    for v in json_spese:
        if inizio <= datetime.strptime(v["Orario"], "%Y/%m/%d %H:%M:%S") < fine:
            totale += v["Importo"]
    tot = Spesa(totale, 'Totale:')
    return tot