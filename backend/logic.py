"""Regole e calcoli dello Study Planner.

Le funzioni ricevono dati e restituiscono risultati: non leggono la
tastiera, non stampano e non toccano i file. Così si provano facilmente.

Unità di misura dell'impegno: minuti stimati dall'utente (intero > 0).
"""


# ---------- Validazione ----------

def pulisci_testo(testo):
    """Restituisce il testo senza spazi iniziali/finali, o None se è vuoto."""
    testo = testo.strip()
    if testo == "":
        return None
    return testo


def converti_minuti(testo):
    """Converte il testo in minuti. Restituisce un intero > 0, o None se non valido.

    Esempi: "45" -> 45; "abc", "-10", "0", "4.5" -> None
    """
    testo = testo.strip()
    if not testo.isdigit():          # accetta solo cifre: niente segno, virgola o lettere
        return None
    minuti = int(testo)
    if minuti <= 0:
        return None
    return minuti


def converti_id(testo):
    """Converte il testo in un id intero > 0, o None se non valido."""
    return converti_minuti(testo)    # stesse regole: intero positivo


def record_valido(record):
    """Controlla che un'attività letta dal file abbia tutti i campi corretti."""
    if not isinstance(record, dict):
        return False
    id_ok = type(record.get("id")) is int and record["id"] > 0
    titolo_ok = isinstance(record.get("titolo"), str) and record["titolo"].strip() != ""
    materia_ok = isinstance(record.get("materia"), str) and record["materia"].strip() != ""
    minuti_ok = type(record.get("impegno_minuti")) is int and record["impegno_minuti"] > 0
    stato_ok = isinstance(record.get("completata"), bool)
    return id_ok and titolo_ok and materia_ok and minuti_ok and stato_ok


# ---------- Operazione 1: aggiungi attività ----------

def prossimo_id(attivita):
    """Restituisce l'id da dare a una nuova attività (il massimo + 1)."""
    massimo = 0
    for a in attivita:
        if a["id"] > massimo:
            massimo = a["id"]
    return massimo + 1


def aggiungi_attivita(attivita, titolo, materia, minuti):
    """Crea una nuova attività aperta, la aggiunge alla lista e la restituisce."""
    nuova = {
        "id": prossimo_id(attivita),
        "titolo": titolo,
        "materia": materia,
        "impegno_minuti": minuti,
        "completata": False,
    }
    attivita.append(nuova)
    return nuova


# ---------- Operazione 2: segna completata ----------

def trova_attivita(attivita, id_cercato):
    """Restituisce l'attività con quell'id, o None se non esiste."""
    for a in attivita:
        if a["id"] == id_cercato:
            return a
    return None


def segna_completata(attivita, id_cercato):
    """Segna come completata l'attività indicata.

    Restituisce un esito:
    - "completata"      se l'operazione è riuscita
    - "non_trovata"     se l'id non esiste
    - "gia_completata"  se era già completata (nessuna modifica)
    """
    trovata = trova_attivita(attivita, id_cercato)
    if trovata is None:
        return "non_trovata"
    if trovata["completata"]:
        return "gia_completata"
    trovata["completata"] = True
    return "completata"


# ---------- Operazione 3: riepilogo ----------

def attivita_aperte(attivita):
    """Restituisce solo le attività non completate."""
    aperte = []
    for a in attivita:
        if not a["completata"]:
            aperte.append(a)
    return aperte


def calcola_riepilogo(attivita):
    """Calcola il riepilogo da esportare per la pagina HTML.

    - minuti_residui: SOMMA dei minuti delle sole attività aperte
    - avanzamento_percentuale: completate / totali * 100, una cifra decimale;
      con zero attività vale 0.0
    """
    aperte = attivita_aperte(attivita)
    totali = len(attivita)
    completate = totali - len(aperte)

    minuti_residui = 0
    for a in aperte:
        minuti_residui += a["impegno_minuti"]

    if totali == 0:
        avanzamento = 0.0
    else:
        avanzamento = round(completate / totali * 100, 1)

    elenco_aperte = []
    for a in aperte:
        elenco_aperte.append({
            "id": a["id"],
            "titolo": a["titolo"],
            "materia": a["materia"],
            "impegno_minuti": a["impegno_minuti"],
        })

    return {
        "attivita_totali": totali,
        "aperte": len(aperte),
        "completate": completate,
        "minuti_residui": minuti_residui,
        "avanzamento_percentuale": avanzamento,
        "attivita_aperte": elenco_aperte,
        "per_materia": calcola_per_materia(attivita),
    }


def calcola_per_materia(attivita):
    """Per ogni materia: attività totali, completate e minuti residui (solo aperte).

    Restituisce una lista di dizionari, nell'ordine in cui le materie compaiono.
    """
    per_materia = {}
    for a in attivita:
        nome = a["materia"]
        if nome not in per_materia:
            per_materia[nome] = {"materia": nome, "totale": 0, "completate": 0, "minuti_residui": 0}
        voce = per_materia[nome]
        voce["totale"] += 1
        if a["completata"]:
            voce["completate"] += 1
        else:
            voce["minuti_residui"] += a["impegno_minuti"]
    return list(per_materia.values())
