from datetime import datetime
import random


class Spesa:
    def __init__(self, importo:float , descrizione:str = None, timestamp: datetime = None, id : int = random.randint(0,1000000) ):
        self.importo = importo
        self.id = id
        if not(descrizione):
            self.descrizione = ''
        else:
            self.descrizione = descrizione
        if not(timestamp):
            self.timestamp = datetime.now("Europe/Rome")
        
        elif type(timestamp) == str:
            
            try:
                self.timestamp = datetime.strptime(timestamp, "%Y/%m/%d %H:%M:%S")
            except:
                try:
                    data, orario = timestamp.split(" ")
                    anno, mese, giorno = data.split("/")
                    self.timestamp = datetime(int(anno), int(mese), int(giorno), int(orario.split(":")[0]), int(orario.split(":")[1]), int(orario.split(":")[2]))
                except:
                    raise ValueError("Timestamp non valido")
        else:
            self.timestamp = timestamp

    def get_datetime(self) -> datetime:
        return datetime.strptime(self.timestamp, "%Y/%m/%d %H:%M:%S")

    def __str__(self) -> str:
        return f"{self.descrizione} | {self.timestamp} | Importo: {self.importo}€"

    def to_dict(self) -> dict:
        return {"Orario": self.timestamp, "Descrizione": self.descrizione, "Importo": self.importo}

class SpesaCc(Spesa):
    def __init__(self, importo:float, descrizione:str = None, timestamp:datetime = None, mensilità:int = 1, id : int = random.randint(0,10000000)):
        super().__init__(importo, descrizione, timestamp,id)
        self.mensilità = mensilità

    def to_dict(self) -> dict:
        return {"Orario": self.timestamp, "Descrizione": self.descrizione, "Importo": self.importo, "Mensilità": self.mensilità}

    def __str__(self) -> str:
        return f"{self.descrizione} | {self.timestamp} | Importo: {self.importo}€ | Mensilità: {self.mensilità}"


