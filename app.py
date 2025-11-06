# main.py
from fastapi import FastAPI, Request, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from bson import ObjectId

# ------------------- CONFIGURAZIONE -------------------

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Connessione a MongoDB (locale o Atlas)
MONGO_URI = "mongodb+srv://hujun_db_user:r7GqGkibAKWBMchn@hudb.tbkyksc.mongodb.net/?appName=HUDB"
DB_NAME = "Distributori"
COLLECTION = "distributori"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
distributori = db[COLLECTION]

# Dizionario alias città
CITTA_ALIAS = {
    "monaco": "Monaco di Baviera",
    "monaco di baviera": "Monaco di Baviera",
    "mosca": "Mosca",
    "san pietroburgo": "San Pietroburgo",
    "pietrogrado": "San Pietroburgo",
    "pietroburgo": "San Pietroburgo",
    "volgograd": "Volgograd",
    "varsavia": "Varsavia",
    "parigi": "Parigi",
    "londra": "Londra",
    "stalingrado": "Volgograd",
    "krakau": "Cracovia",
    "krakow": "Cracovia"
}

# Funzione di utilità per convertire ObjectId in stringa
def mongo_to_dict(doc):
    doc["_id"] = str(doc["_id"])
    return doc


# ------------------- API -------------------

@app.get("/distributori")
def elenco_distributori():
    docs = distributori.find().sort("id_distributore", 1)
    return [mongo_to_dict(d) for d in docs]


@app.get("/distributori/provincia/{provincia}")
def distributori_provincia(provincia: str):
    provincia_norm = CITTA_ALIAS.get(provincia.lower(), provincia)
    docs = distributori.find({"provincia": provincia_norm})
    return [mongo_to_dict(d) for d in docs]


@app.get("/distributori/{id_distributore}")
def distributore_per_id(id_distributore: int):
    doc = distributori.find_one({"id_distributore": id_distributore})
    if doc:
        return mongo_to_dict(doc)
    return {"errore": "Distributore non trovato"}


@app.post("/distributori/prezzo/{provincia}")
def cambia_prezzo_provincia(provincia: str, tipo: str = Body(...), nuovo_prezzo: float = Body(...)):
    if tipo not in ["benzina", "diesel"]:
        return {"errore": "Tipo carburante non valido"}

    provincia_norm = CITTA_ALIAS.get(provincia.lower(), provincia)
    result = distributori.update_many(
        {"provincia": provincia_norm},
        {"$set": {f"prezzo_{tipo}": nuovo_prezzo}}
    )

    if result.modified_count == 0:
        return {"messaggio": "Nessun distributore aggiornato"}

    docs = distributori.find({"provincia": provincia_norm})
    return [mongo_to_dict(d) for d in docs]


# ------------------- PAGINA HTML -------------------

@app.get("/", response_class=HTMLResponse)
def pagina_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
