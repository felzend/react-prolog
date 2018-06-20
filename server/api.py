import logging
import json
import cgi

from urllib.parse import urlparse, parse_qs
from pyswip import Prolog
from http.server import BaseHTTPRequestHandler, HTTPServer

pl = Prolog()

# HTTP Server Handler Class.
class HttpServerHandler(BaseHTTPRequestHandler):

    def _set_response(self): # função para ajustar os headers a retornarem conteúdo em formato HTML.
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _set_json_response(self): # função para ajustar os headers a retornarem conteúdo em formato JSON.
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        global pl
        params = parse_qs(urlparse(self.path).query)
        logging.info("URL PARAMS (GET): %s", params)

        if self.path.startswith("/favicon.ico"):
            return

        if '/sales' in self.path: # GET /sales
            query = "checkouts(Sale, Product, Name, Price), Sale > -1"
            sales = list(pl.query(query))
            if len(sales) == 0:
                sales = [ ]
            self._set_json_response()
            self.wfile.write(json.dumps(sales).encode('utf-8'))
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

        self._set_response()
        self.wfile.write("Prolog API's index.".format(self.path).encode('utf-8'))
        return

    def do_POST(self):
        global pl

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
            'CONTENT_TYPE':'application/json',#self.headers['Content-Type'],
        })

        if self.path.startswith("/favicon.ico"):
            return

        if '/checkout' in self.path: # POST /checkout
            products = json.loads(form.getvalue('products')) # uma lista em formato JSON é recebida através do parâmetro 'products'.
            for p in products:

                sale = int(p['sale']) # recebe o ID único da venda gerado aleatoriamente.

                product = int(p['product']) # recebe o ID do produto

                price = float(p['price']) # recebe o preço do produto

                query = "checkout(%d, %d, %f)" % ( sale, product, price ) # estrutura a regra em prolog.

                pl.assertz(query) # executa a regra.

                pl.retractall("cart(%d)" % (product) ) # remove todos os produtos do carrinho com os IDs recebidos.

                logging.info("CHECKOUT %d - Product %d" % (sale, product))

                logging.info("CART (REMOVE) - %d", (product))

            self._set_response()
            return

        if '/stock' in self.path: # POST /stock - Params: product (id), method (inc | dec).

            pid = int(form.getvalue('product'))
            action = form.getvalue('action')

            if action == 'dec': # ADICIONA O PRODUTO AO CARRINHO e remove do estoque.

                query = "stock(%d, Price, Amount)" % (pid) # monta-se a query com o ID do produto recebido.

                product = list(pl.query(query)) # obtem-se o produto pelo ID.

                if len(product) > 0:

                    product = product[0] # atribui-se 'product[0]' a 'product', pois o resultado é um array.

                    logging.info("PRODUCT (ADD/CART): %s", product)

                    pl.retractall("stock(%d, _, _)" % (pid)) # remove o produto do "stock".

                    # re-adiciona o produto ao "stock" com UM A MENOS de quantidade.
                    pl.assertz("stock(%d, %f, %d)" % (pid, float(product['Price']), int(product['Amount']) - 1))

                    pl.assertz("cart(%d)" % (pid)) # adiciona o ID do produto ao carrinho de compras.

            elif action == 'inc': # REMOVE O PRODUTO DO CARRINHO e adiciono ao estoque.

                query = "stock(%d, Price, Amount)" % (pid) # monta-se a query com o ID do produto recebido.

                product = list(pl.query(query)) # obtem-se o produto pelo ID.

                if len(product) > 0:

                    product = product[0] # atribui-se 'product[0]' a 'product', pois o resultado é um array.

                    logging.info("PRODUCT (REMOVE/CART): %s", product)

                    pl.retract("cart(%d)" % (pid)) # remove o produto com o ID recebido do carrinho.

                    # re-adiciona o produto ao "stock" com UM A MAIS de quantidade.
                    pl.assertz("stock(%d, %f, %d)" % (pid, float(product['Price']), int(product['Amount']) + 1))

                    pl.retract("stock(%d, _, _)" % (pid)) # remove o produto do "stock".

            self._set_json_response()
            #self.wfile.write("{}")
            return

    def do_OPTIONS(self):
        self.send_response(202)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'x-http-method-override, POST')
        self.end_headers()
        return

# Initialization function for loading Prolog database into server memory.
def initialization():
    global pl # referenciando a instância global do objeto Prolog
    if isinstance(pl, Prolog):
        file = open("./assets/database.pl", "r") # abre o arquivo "database.pl".
        lines = file.read().split("\n") # lê linha a linha do arquivo...

        for i in range(0, len(lines)):
            assertion = lines[i].replace(").", ")")
            if len(assertion) == 0: # pula as linhas em branco.
                continue
            pl.assertz(assertion) # executa uma regra lógica
        return True
    return False

# Function for starting the HTTP server.
def run(server_class = HTTPServer, handler_class = HttpServerHandler, port = 4000):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port) # localhost:port.
    httpd = server_class(server_address, handler_class) # cria a instância do servidor utilizando a classe HttpServerHandler
    logging.info("Starting HTTP server in port %d" % port)
    try:
        httpd.serve_forever() # coloca o servidor em loop, à espera de requisições.
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping HTTP server...\n')

initialization()
run()