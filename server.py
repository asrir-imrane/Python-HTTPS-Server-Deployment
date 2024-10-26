import http.server
import ssl

class SimpleHTTPSHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Server is up!")

if __name__ == "__main__":
    server_address = ('', 8443)
    httpd = http.server.HTTPServer(server_address, SimpleHTTPSHandler)
    httpd.socket = ssl.wrap_socket(httpd.socket, keyfile="key.pem", certfile="cert.pem", server_side=True)   
    print("Serving on port 8443...")
    httpd.serve_forever()
