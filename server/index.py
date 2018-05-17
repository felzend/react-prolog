import json
from pyswip import Prolog
from flask import Flask, jsonify

prolog = Prolog()
app = Flask(__name__)

@app.route("/stores")
def stores():
    global prolog
    stores = list(prolog.query("store(ID, NOME)"))
    return jsonify(stores)

def generate_stores(pl):
    if isinstance(pl, Prolog):
        stores = list ( json.load(open("stores.json")) )
        for i in range(0, len(stores)):
            rules = {
                "store": "store(%d, '%s')" % ( stores[i]['id'], stores[i]['name'] ),
                "rating": "rating(%d, %.2f)" % ( stores[i]['id'], float(stores[i]['rating']) ),
                "location": "location(%d, %f, %f)" % ( stores[i]['id'], float(stores[i]['lat']), float(stores[i]['lng']) ),
            }
            
            pl.assertz( rules["store"] )
            pl.assertz( rules["rating"] )
            pl.assertz( rules["location"] )
        return True
    return False

def load_stores(pl):
    if isinstance(pl, Prolog):
        file = open("./assets/database.pl", "r") 
        lines = file.read().split("\n")
        for i in range(0, len(lines)):
            assertion = lines[i].replace(".", "")
            if len(assertion) == 0:
                continue
            pl.assertz(assertion)
        return True
    return False

load_stores(prolog)
app.run(threaded=True)