# app.py
from flask import Flask, jsonify, request, render_template
from pymongo import MongoClient
from bson import ObjectId
from bson.decimal128 import Decimal128

# ------------------- CONFIGURAZIONE -------------------

app = Flask(__name__, template_folder="templates")

# Connessione a MongoDB
MONGO_URI = "mongodb+srv://hujun_db_user:r7GqGkibAKWBMchn@hudb.tbkyksc.mongodb.net/?appName=HUDB"
DB_NAME = "Distributori"
COLLECTION = "distributori"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
distributori = db[COLLECTION]

# Alias città
CITTA_ALIAS = {
    "milano" : "Milano",
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


# ------------------- FUNZIONE DI SUPPORTO -------------------

def mongo_to_dict(doc):
    """
    Converte ObjectId e Decimal128 in tipi JSON-compatibili.
    Gestisce ricorsivamente dizionari e liste annidati.
    """
    if doc is None:
        return None
    
    new_doc = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            # Converti ObjectId in stringa
            new_doc[key] = str(value)
        elif isinstance(value, Decimal128):
            # Converti Decimal128 in float (per prezzi va bene)
            new_doc[key] = float(value.to_decimal())
        elif isinstance(value, dict):
            # Gestione ricorsiva per dizionari annidati
            new_doc[key] = mongo_to_dict(value)
        elif isinstance(value, list):
            # Gestione liste con possibili Decimal128
            new_doc[key] = [
                float(v.to_decimal()) if isinstance(v, Decimal128)
                else mongo_to_dict(v) if isinstance(v, dict)
                else v
                for v in value
            ]
        else:
            # Altri tipi: mantieni come sono
            new_doc[key] = value
    
    return new_doc


# ------------------- API -------------------

@app.route("/distributori", methods=["GET"])
def elenco_distributori():
    """Restituisce l'elenco completo di tutti i distributori"""
    try:
        docs = distributori.find().sort("id_distributore", 1)
        return jsonify([mongo_to_dict(d) for d in docs])
    except Exception as e:
        return jsonify({"errore": f"Errore nel recupero dei distributori: {str(e)}"}), 500


@app.route("/distributori/provincia/<provincia>", methods=["GET"])
def distributori_provincia(provincia):
    """Restituisce i distributori di una specifica provincia"""
    try:
        provincia_norm = CITTA_ALIAS.get(provincia.lower(), provincia)
        print(provincia_norm)
        docs = list(distributori.find({"provincia": provincia_norm}))
        
        if not docs:
            return jsonify({"errore": f"Nessun distributore trovato per la provincia: {provincia}"}), 404
        
        return jsonify([mongo_to_dict(d) for d in docs])
    except Exception as e:
        return jsonify({"errore": f"Errore nella ricerca: {str(e)}"}), 500


@app.route("/distributori/<int:id_distributore>", methods=["GET"])
def distributore_per_id(id_distributore):
    """Restituisce un distributore specifico per ID"""
    try:
        if id_distributore <= 0:
            return jsonify({"errore": "ID distributore non valido"}), 400
        
        doc = distributori.find_one({"idDistributore": id_distributore})
        
        if not doc:
            return jsonify({"errore": f"Distributore con ID {idDistributore} non trovato"}), 404
        
        return jsonify(mongo_to_dict(doc))
    except Exception as e:
        return jsonify({"errore": f"Errore nella ricerca: {str(e)}"}), 500


@app.route("/distributori/prezzo/<provincia>", methods=["POST"])
def cambia_prezzo_provincia(provincia):
    """Aggiorna il prezzo di un carburante per tutti i distributori di una provincia"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"errore": "Nessun dato ricevuto"}), 400
        
        tipo = data.get("tipo")
        nuovo_prezzo = data.get("nuovo_prezzo")
        
        # Validazione
        if not tipo or not nuovo_prezzo:
            return jsonify({"errore": "Parametri 'tipo' e 'nuovo_prezzo' richiesti"}), 400
        
        if tipo not in ["Benzina", "Diesel"]:
            return jsonify({"errore": "Tipo carburante non valido. Utilizzare 'benzina' o 'diesel'"}), 400
        
        try:
            nuovo_prezzo = float(nuovo_prezzo)
            if nuovo_prezzo <= 0:
                return jsonify({"errore": "Il prezzo deve essere maggiore di 0"}), 400
        except (ValueError, TypeError):
            return jsonify({"errore": "Formato prezzo non valido"}), 400

        provincia_norm = CITTA_ALIAS.get(provincia.lower(), provincia)
        
        # Aggiorna i prezzi
        result = distributori.update_many(
            {"provincia": provincia_norm},
            {"$set": {f"prezzo{tipo}": nuovo_prezzo}}
        )

        if result.matched_count == 0:
            return jsonify({"errore": f"Nessun distributore trovato per la provincia: {provincia}"}), 404

        # Restituisce i distributori aggiornati
        docs = distributori.find({"provincia": provincia_norm})
        return jsonify([mongo_to_dict(d) for d in docs])
        
    except Exception as e:
        return jsonify({"errore": f"Errore nell'aggiornamento: {str(e)}"}), 500


# ------------------- FRONTEND -------------------

@app.route("/")
def pagina_home():
    """Serve la pagina HTML principale"""
    return render_template("index.html")


# ------------------- MAIN -------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)