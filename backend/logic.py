"""Regole e calcoli dello Study Planner.

Le funzioni ricevono dati e restituiscono risultati: non leggono la
tastiera, non stampano e non toccano i file. Così si provano facilmente.

Unità di misura dell'impegno: minuti stimati dall'utente (intero > 0).
Priorità: "alta", "media" o "bassa".
Data di inizio: salvata come testo "AAAA-MM-GG" (alle attività senza data viene data quella del giorno in cui si caricano).
"""

from datetime import date

PRIORITA = ("alta", "media", "bassa")   # dalla più urgente alla meno urgente
PRIORITA_PREDEFINITA = "media"


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


def converti_priorita(testo):
    """Converte il testo in una priorità valida, o None se non valido.

    Accetta il nome (anche maiuscolo) o il numero: 1 = alta, 2 = media, 3 = bassa.
    Testo vuoto -> priorità predefinita ("media").
    Esempi: "Alta" -> "alta"; "3" -> "bassa"; "" -> "media"; "urgente" -> None
    """
    testo = testo.strip().lower()
    if testo == "":
        return PRIORITA_PREDEFINITA
    if testo in ("1", "2", "3"):
        return PRIORITA[int(testo) - 1]
    if testo in PRIORITA:
        return testo
    return None


def converti_data(testo, predefinita=None):
    """Converte il testo in una data "AAAA-MM-GG", o None se non valida.

    Accetta "GG/MM/AAAA" (anche con - o . al posto di /) oppure "AAAA-MM-GG".
    Testo vuoto -> predefinita (ad es. la data di oggi).
    Esempi: "9/11/2026" -> "2026-11-09"; "2026-11-09" -> "2026-11-09";
            "31/02/2026", "ieri" -> None
    """
    testo = testo.strip()
    if testo == "":
        return predefinita
    try:
        if len(testo) == 10 and testo[4] == "-" and testo[7] == "-":
            return date.fromisoformat(testo).isoformat()
        parti = testo.replace("-", "/").replace(".", "/").split("/")
        if len(parti) != 3 or not all(p.isdigit() for p in parti) or len(parti[2]) != 4:
            return None
        giorno, mese, anno = (int(p) for p in parti)
        return date(anno, mese, giorno).isoformat()
    except ValueError:              # ad es. 31 febbraio
        return None


def formatta_data(iso):
    """Da "AAAA-MM-GG" a "GG/MM/AAAA" per mostrarla all'utente; "—" se manca."""
    if iso is None:
        return "—"
    anno, mese, giorno = iso.split("-")
    return f"{giorno}/{mese}/{anno}"


def data_valida(valore):
    """True se valore è None oppure una data reale nel formato "AAAA-MM-GG"."""
    if valore is None:
        return True
    if not isinstance(valore, str) or len(valore) != 10:
        return False
    try:
        return date.fromisoformat(valore).isoformat() == valore
    except ValueError:
        return False


def converti_stato(testo):
    """Converte il testo nello stato dell'attività: True = completata, False = aperta.

    Accetta "completata"/"c"/"si"/"s" e "aperta"/"a"/"no"/"n" (maiuscole comprese).
    Restituisce None se il testo non è riconosciuto.
    """
    testo = testo.strip().lower()
    if testo in ("completata", "c", "si", "sì", "s"):
        return True
    if testo in ("aperta", "a", "no", "n"):
        return False
    return None


def converti_id(testo):
    """Converte il testo in un id intero > 0, o None se non valido."""
    return converti_minuti(testo)    # stesse regole: intero positivo


def normalizza_record(record):
    """Aggiorna un'attività salvata con il vecchio formato.

    - "materia" diventa "categoria"
    - se manca "priorita", vale quella predefinita
    - se "data_inizio" manca o è null, vale la data di oggi
    Modifica il dizionario e lo restituisce; i valori non dict restano come sono.
    """
    if not isinstance(record, dict):
        return record
    if "categoria" not in record and "materia" in record:
        record["categoria"] = record.pop("materia")
    if "priorita" not in record:
        record["priorita"] = PRIORITA_PREDEFINITA
    if record.get("data_inizio") is None:
        record["data_inizio"] = date.today().isoformat()
    # riordina i campi come nelle attività nuove (gli eventuali campi extra restano in fondo)
    ordine = ["id", "titolo", "priorita", "categoria", "data_inizio", "impegno_minuti", "completata"]
    vecchio = dict(record)
    record.clear()
    for chiave in ordine:
        if chiave in vecchio:
            record[chiave] = vecchio.pop(chiave)
    record.update(vecchio)
    return record


def record_valido(record):
    """Controlla che un'attività letta dal file abbia tutti i campi corretti."""
    if not isinstance(record, dict):
        return False
    id_ok = type(record.get("id")) is int and record["id"] > 0
    titolo_ok = isinstance(record.get("titolo"), str) and record["titolo"].strip() != ""
    categoria_ok = isinstance(record.get("categoria"), str) and record["categoria"].strip() != ""
    priorita_ok = record.get("priorita") in PRIORITA
    data_ok = data_valida(record.get("data_inizio"))
    minuti_ok = type(record.get("impegno_minuti")) is int and record["impegno_minuti"] > 0
    stato_ok = isinstance(record.get("completata"), bool)
    return id_ok and titolo_ok and categoria_ok and priorita_ok and data_ok and minuti_ok and stato_ok


# ---------- Operazione 1: aggiungi attività ----------

def prossimo_id(attivita):
    """Restituisce l'id da dare a una nuova attività (il massimo + 1)."""
    massimo = 0
    for a in attivita:
        if a["id"] > massimo:
            massimo = a["id"]
    return massimo + 1


def aggiungi_attivita(attivita, titolo, priorita, categoria, data_inizio, minuti):
    """Crea una nuova attività aperta, la aggiunge alla lista e la restituisce."""
    nuova = {
        "id": prossimo_id(attivita),
        "titolo": titolo,
        "priorita": priorita,
        "categoria": categoria,
        "data_inizio": data_inizio,
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


# ---------- Operazione 5: modifica attività ----------

CAMPI_MODIFICABILI = ("titolo", "priorita", "categoria", "data_inizio", "impegno_minuti", "completata")


def modifica_attivita(attivita, id_cercato, modifiche):
    """Cambia uno o più campi dell'attività indicata.

    modifiche è un dizionario {campo: nuovo valore} con valori GIÀ controllati
    (ad es. da pulisci_testo, converti_priorita, converti_data, converti_minuti, converti_stato).
    Si può passare un solo campo oppure tutti quelli di CAMPI_MODIFICABILI.

    Restituisce un esito:
    - "modificata"        se almeno un campo è cambiato
    - "nessuna_modifica"  se i valori erano già quelli
    - "non_trovata"       se l'id non esiste
    """
    for campo in modifiche:
        if campo not in CAMPI_MODIFICABILI:
            raise ValueError(f"Campo non modificabile: {campo}")
    trovata = trova_attivita(attivita, id_cercato)
    if trovata is None:
        return "non_trovata"
    cambiati = [campo for campo, valore in modifiche.items() if trovata[campo] != valore]
    if len(cambiati) == 0:
        return "nessuna_modifica"
    for campo in cambiati:
        trovata[campo] = modifiche[campo]
    return "modificata"


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
            "priorita": a["priorita"],
            "categoria": a["categoria"],
            "data_inizio": a["data_inizio"],
            "impegno_minuti": a["impegno_minuti"],
        })

    return {
        "attivita_totali": totali,
        "aperte": len(aperte),
        "completate": completate,
        "minuti_residui": minuti_residui,
        "avanzamento_percentuale": avanzamento,
        "attivita_aperte": elenco_aperte,
        "per_categoria": calcola_per_categoria(attivita),
    }


def calcola_per_categoria(attivita):
    """Per ogni categoria: attività totali, completate e minuti residui (solo aperte).

    Restituisce una lista di dizionari, nell'ordine in cui le categorie compaiono.
    """
    per_categoria = {}
    for a in attivita:
        nome = a["categoria"]
        if nome not in per_categoria:
            per_categoria[nome] = {"categoria": nome, "totale": 0, "completate": 0, "minuti_residui": 0}
        voce = per_categoria[nome]
        voce["totale"] += 1
        if a["completata"]:
            voce["completate"] += 1
        else:
            voce["minuti_residui"] += a["impegno_minuti"]
    return list(per_categoria.values())
