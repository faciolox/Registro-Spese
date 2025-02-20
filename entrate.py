from datetime import datetime, timezone
import random
import pytz

rome_tz = pytz.timezone('Europe/Rome')

class Entrate:
    def __init__(self, importo: float, descrizione: str = None, timestamp:datetime = None, id:int = random.randint(0, 1000000)):
        self.id = id
        self.importo = importo
        if not(descrizione):
            self.descrizione = ''
        else:
            self.descrizione = descrizione
        if not(timestamp):
            self.timestamp = datetime.now(tz=rome_tz).strftime("%Y/%m/%d %H:%M:%S")
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
            try:
                self.timestamp = timestamp
            except:
                raise ValueError("Timestamp non valido")

    def get_datetime(self) -> datetime:
        return datetime.strptime(self.timestamp, "%Y/%m/%d %H:%M:%S")

    def __str__(self) -> str:
        return f"{self.descrizione} | {self.timestamp} | Importo: {self.importo}€"

    def to_dict(self) -> dict:
        return {"Orario": self.timestamp, "Descrizione": self.descrizione, "Importo": self.importo}



