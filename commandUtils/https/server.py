import http.server, ssl
from pathlib import Path

def runHttpsServer(certfile: Path, keyfile: Path, port: int = 443, local: bool = True) -> None:
    httpd = http.server.HTTPServer(('127.0.0.1' if local else "0.0.0.0", port), http.server.SimpleHTTPRequestHandler)
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(certfile=str(certfile.resolve()), keyfile=str(keyfile.resolve()))
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    httpd.serve_forever()