# assertz -> Adiciona Regra
# retract -> Remove Regra

import json
from pyswip import Prolog

prolog = Prolog()

def load_stores(pl):
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

load_stores(prolog)
print(list(prolog.query("store(ID, N), ID < 10")))