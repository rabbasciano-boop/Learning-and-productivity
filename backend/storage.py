"""Lettura e scrittura dei file JSON del progetto.

Qui stanno solo le operazioni sui file: nessuna regola del dominio.
"""

import json
import os
from pathlib import Path

from logic import normalizza_record, record_valido

# Percorsi calcolati rispetto a questo file, così il programma funziona
# anche se viene avviato da un'altra cartella.
CARTELLA_PROGETTO = Path(__file__).resolve().parent.parent   # backend/.. = radice del progetto
FILE_ATTIVITA = CARTELLA_PROGETTO / "data" / "attivita.json"
FILE_RIEPILOGO = CARTELLA_PROGETTO / "output" / "riepilogo.json"


class ErroreDati(Exception):
    """Il file delle attività esiste ma non si può usare."""


def carica_attivita(percorso=FILE_ATTIVITA):
    """Legge l'archivio e restituisce la lista delle attività.

    - File assente: restituisce una lista vuota (si parte da zero).
    - File vuoto, JSON rotto o record non validi: solleva ErroreDati,
      così il programma si ferma SENZA sovrascrivere il file.
    """
    if not percorso.exists():
        return []

    # "utf-8-sig" ignora l'eventuale BOM aggiunto da alcuni editor di Windows
    testo = percorso.read_text(encoding="utf-8-sig")
    if testo.strip() == "":
        raise ErroreDati(f"Il file {percorso.name} è vuoto.")

    try:
        dati = json.loads(testo)
    except json.JSONDecodeError as errore:
        raise ErroreDati(
            f"Il file {percorso.name} non contiene JSON valido (riga {errore.lineno})."
        )

    if not isinstance(dati, list):
        raise ErroreDati(f"Il file {percorso.name} deve contenere una lista di attività.")

    id_visti = set()
    for posizione, record in enumerate(dati, start=1):
        normalizza_record(record)   # accetta anche i file col vecchio campo "materia"
        if not record_valido(record):
            raise ErroreDati(f"L'attività n. {posizione} nel file non è valida.")
        if record["id"] in id_visti:
            raise ErroreDati(f"L'id {record['id']} compare più di una volta nel file.")
        id_visti.add(record["id"])

    return dati


def scrivi_json(dati, percorso):
    """Scrive dati in un file JSON leggibile (UTF-8, indentato).

    Scrive prima in un file temporaneo e poi lo sostituisce all'originale:
    se qualcosa va storto a metà, il file precedente resta intatto.
    """
    percorso.parent.mkdir(parents=True, exist_ok=True)
    temporaneo = percorso.with_suffix(".tmp")
    with open(temporaneo, "w", encoding="utf-8") as file:
        json.dump(dati, file, ensure_ascii=False, indent=2)
        file.write("\n")
    os.replace(temporaneo, percorso)


def salva_attivita(attivita, percorso=FILE_ATTIVITA):
    """Salva l'archivio delle attività."""
    scrivi_json(attivita, percorso)


def esporta_riepilogo(riepilogo, percorso=FILE_RIEPILOGO):
    """Salva il riepilogo da caricare nella pagina HTML. Restituisce il percorso."""
    scrivi_json(riepilogo, percorso)
    return percorso
