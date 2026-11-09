import json
import webbrowser
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock

import logic
import storage

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "output" / "riepilogo.json"
ARCHIVIO = ROOT / "data" / "attivita.json"
lock = Lock()


def salva_nuova(titolo, materia, minuti, scadenza):
    with lock:
        archivio = storage.carica_attivita(ARCHIVIO)
        precedente = archivio.copy()
        nuova = logic.aggiungi_attivita(archivio, titolo, materia, minuti)
        if scadenza:
            nuova["scadenza"] = scadenza

        riepilogo = logic.calcola_riepilogo(archivio)
        scadenze = {a["id"]: a["scadenza"] for a in archivio if a.get("scadenza")}
        for a in riepilogo["attivita_aperte"]:
            if a["id"] in scadenze:
                a["scadenza"] = scadenze[a["id"]]

        storage.salva_attivita(archivio, ARCHIVIO)
        try:
            storage.esporta_riepilogo(riepilogo, FILE)
        except OSError:
            storage.salva_attivita(precedente, ARCHIVIO)
            raise
        return riepilogo


class Planner(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "frontend"), **kwargs)

    def rispondi(self, stato, dati):
        corpo = json.dumps(dati, ensure_ascii=False).encode("utf-8")
        self.send_response(stato)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def do_POST(self):
        if self.path != "/api/riepilogo":
            return self.rispondi(404, {"errore": "Percorso sconosciuto."})
        origine = "http://127.0.0.1:" + str(self.server.server_port)
        if self.headers.get("Origin", origine) != origine or self.headers.get("Host") != origine[7:]:
            return self.rispondi(403, {"errore": "Apri il planner dal suo indirizzo locale."})
        try:
            n = int(self.headers.get("Content-Length", 0))
            if not 0 < n <= 65536 or self.headers.get_content_type() != "application/json":
                raise ValueError
            dati = json.loads(self.rfile.read(n))
            titolo = dati["titolo"].strip()
            materia = dati["materia"].strip()
            minuti = dati["impegno_minuti"]
            scadenza = dati.get("scadenza", "")
            if not titolo or not materia or type(minuti) is not int or minuti <= 0:
                raise ValueError
            if scadenza:
                date.fromisoformat(scadenza)
        except (TypeError, ValueError, AttributeError, KeyError):
            return self.rispondi(400, {"errore": "Controlla titolo, categoria, minuti e scadenza."})
        try:
            r = salva_nuova(titolo, materia, minuti, scadenza)
        except (storage.ErroreDati, OSError, KeyError, TypeError, ValueError, ArithmeticError):
            return self.rispondi(500, {"errore": "Controlla data/attivita.json e i permessi di scrittura dei due file."})
        self.rispondi(201, r)


if __name__ == "__main__":
    with ThreadingHTTPServer(("127.0.0.1", 8765), Planner) as server:
        url = f"http://127.0.0.1:{server.server_port}/"
        print("Apri il planner nel tuo browser:", url, flush=True)
        webbrowser.open(url)
        server.serve_forever()
