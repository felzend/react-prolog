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
        logging.info("URL PARAMS: %s", params)
        
        if self.path.startswith("/favicon.ico"):
            return

        if '/sales' in self.path: # GET /sales
            query = "checkout(Sale, Product, Price), Sale > -1"
            sales = list(pl.query(query))
            if len(sales) == 0:
                sales = [ ]
            self._set_json_response()
            self.wfile.write(json.dumps(sales).encode('utf-8'))
            return

        if '/checkout' in self.path: # GET /checkout
            products = json.loads(params['products'][0])
            for p in products:
                sale = int(p['sale'])
                product = int(p['product'])
                price = float(p['price'])
                query = "checkout(%d, %d, %f)" % ( sale, product, price )
                
                pl.assertz(query)
                pl.retractall("cart(%d)" % (product) )
                logging.info("CHECKOUT %d - Product %d" % (sale, product))
                logging.info("CART (REMOVE) - %d", (product))

            self._set_response()
            return

        if '/cart' in self.path: # GET /cart
            query = "cart(Id, Name, Photo, Price), Id > -1"
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
            
            if action == 'dec': # Removo produto do estoque e adiciono ao carrinho de compras.
                query = "stock(%d, Price, Amount)" % (pid)
                product = list(pl.query(query))
                if len(product) > 0:
                    product = product[0]
                    logging.info("PRODUCT (ADD/CART): %s", product)
                    pl.retractall("stock(%d, _, _)" % (pid))
                    pl.assertz("stock(%d, %f, %d)" % (pid, float(product['Price']), int(product['Amount']) - 1))
                    pl.assertz("cart(%d)" % (pid))
            
            elif action == 'inc': # Removo o produto do carrinho e adiciono ao estoque.
                query = "stock(%d, Price, Amount)" % (pid)
                product = list(pl.query(query))
                if len(product) > 0:
                    product = product[0]
                    logging.info("PRODUCT (REMOVE/CART): %s", product)
                    pl.retract("cart(%d)" % (pid))
                    pl.retract("stock(%d, _, _)" % (pid))
                    pl.assertz("stock(%d, %f, %d)" % (pid, float(product['Price']), int(product['Amount']) + 1))
            
            self._set_response()
            return

        self._set_response()
        self.wfile.write("Prolog API's index.".format(self.path).encode('utf-8'))
        return

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