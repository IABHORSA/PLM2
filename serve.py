#!/usr/bin/env python3
"""Server di prova per il simulatore PLM.

Serve la pagina e i file della cartella assets con le intestazioni HTTP
scelte dalla pagina (Content-Type e Content-Disposition), per riprodurre
un server che etichetta male un file.

Uso:   python serve.py [porta]        (porta predefinita 8000)
Poi apri dal tablet:  http://INDIRIZZO-DEL-PC:PORTA/
Serve solo Python 3, nessun pacchetto aggiuntivo. Termina con Ctrl+C.
"""
import http.server
import os
import socket
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

MIMES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".dxf": "image/vnd.dxf",
}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def _dl(self, send_body):
        parsed = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(parsed.query)
        name = os.path.basename(urllib.parse.unquote(parsed.path[len("/dl/"):]))
        path = os.path.join(ASSETS, name)
        if not name or not os.path.isfile(path):
            self.send_error(404, "File non trovato")
            return
        ct = q.get("ct", ["ok"])[0]
        cd = q.get("cd", ["attachment"])[0]
        real = MIMES.get(os.path.splitext(name)[1].lower(), "application/octet-stream")
        ctype = {"ok": real, "octet": "application/octet-stream", "html": "text/html; charset=utf-8", "empty": None}.get(ct, real)
        size = os.path.getsize(path)
        self.send_response(200)
        if ctype:
            self.send_header("Content-Type", ctype)
        if cd in ("attachment", "inline"):
            self.send_header("Content-Disposition", '%s; filename="%s"' % (cd, name))
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if send_body:
            with open(path, "rb") as f:
                self.wfile.write(f.read())

    def do_GET(self):
        if self.path.startswith("/dl/"):
            return self._dl(True)
        if self.path in ("/", ""):
            self.path = "/plm-simulazione.html"
        return super().do_GET()

    def do_HEAD(self):
        if self.path.startswith("/dl/"):
            return self._dl(False)
        if self.path in ("/", ""):
            self.path = "/plm-simulazione.html"
        return super().do_HEAD()

    def log_message(self, fmt, *args):
        sys.stdout.write("%s  %s\n" % (self.address_string(), fmt % args))


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    srv = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("Simulatore PLM attivo.")
    print("  Da questo PC:   http://localhost:%d/" % PORT)
    print("  Dal tablet:     http://%s:%d/" % (lan_ip(), PORT))
    print("Se il tablet non si collega, controlla il firewall di Windows. Ctrl+C per fermare.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nFermato.")
