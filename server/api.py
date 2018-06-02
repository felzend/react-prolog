import logging
import time
import json

from urllib.parse import urlparse, parse_qs
from pyswip import Prolog, Query
from http.server import BaseHTTPRequestHandler, HTTPServer

pl = Prolog()

# HTTP Server Handler Class.
class HttpServerHandler(BaseHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _set_json_response(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        global pl
        params = parse_qs(urlparse(self.path).query)
        logging.info("URL: %s", params)

        if self.path.startswith("/favicon.ico"): 
            return

        if '/cart' in self.path: # GET /cart
            query = "cart(Id, Name, Photo), Id > -1"
            products = list(pl.query(query))
            if len(products) == 0:
                products = [ ]
            self._set_json_response()
            self.wfile.write(json.dumps(products).encode('utf-8'))
            return

        if '/products' in self.path: # GET /products
            query = "products(Id, Name, Price, Stock, Photo)"
            products = list(pl.query(query))
            self._set_json_response()
            self.wfile.write(json.dumps(products).encode('utf-8'))
            return

        if '/rating' in self.path: # GET /rating
            query = "rating(Value)"
            rating = list(pl.query(query))
            self._set_json_response()
            self.wfile.write(json.dumps(rating).encode('utf-8'))
            return

        if '/stock' in self.path: # GET /stock - Params: product (id), method (inc | dec).
            pid = int(params['product'][0])
            action = params['action'][0]
            if action == 'dec':
                query = "stock(%d, Price, Amount)" % (pid)
                product = list(pl.query(query))
                if len(product) > 0:
                    product = product[0]
                    logging.info("PRODUCT: %s", product)
                    pl.retractall("stock(%d, _, _)" % (pid))
                    pl.assertz("stock(%d, %f, %d)" % (pid, float(product['Price']), int(product['Amount']) - 1))
                    pl.assertz("cart(%d)" % (pid))
            self._set_response()
            return
        '''
        if '/store' in self.path and 'id' in params: # GET store/{id}
            query = "store(StoreId, StoreName, StoreRating, ProductId, ProductName, ProductPhoto, ProductPrice, ProductAmount), StoreId = %d." % int(params['id'][0])
            obj = list(pl.query(query))
            self._set_json_response()
            self.wfile.write(json.dumps(obj).encode('utf-8'))
            return
        if '/stores' in self.path: # GET Stores
            obj = list(pl.query("stores(Id, Name, Lat, Lng, Rating)"))
            self._set_json_response()
            self.wfile.write(json.dumps(obj).encode('utf-8'))
            return
        if self.path == '/ratings': # GET Ratings
            obj = list(pl.query("rating(ID, VALUE)"))
            self._set_json_response()
            self.wfile.write(json.dumps(obj).encode('utf-8'))
            return
        if self.path == '/locations': # GET Locations
            obj = list(pl.query("location(ID, LAT, LNG)"))
            self._set_json_response()
            self.wfile.write(json.dumps(obj).encode())
            return
        '''
        self._set_response()
        self.wfile.write("Prolog API's index.".format(self.path).encode('utf-8'))
        

    def do_POST(self): # TODO
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))

        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

# Initialization function for loading Prolog database into server memory.
def initialization():
    global pl
    if isinstance(pl, Prolog):
        file = open("./assets/database.pl", "r")
        lines = file.read().split("\n")

        for i in range(0, len(lines)):
            assertion = lines[i].replace(").", ")")
            if len(assertion) == 0:
                continue
            pl.assertz(assertion)
        return True
    return False

# Function for starting the HTTP server.
def run(server_class = HTTPServer, handler_class = HttpServerHandler, port = 4000):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info("Starting HTTP server in port %d" % port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping HTTP server...\n')

initialization()
run()