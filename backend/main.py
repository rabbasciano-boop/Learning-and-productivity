"""Study Planner — avvio con: python backend/main.py

Qui stanno il menu e il dialogo con l'utente nel terminale.
Le regole sono in logic.py, la lettura/scrittura dei file in storage.py.
"""

from datetime import date

import logic
import storage


def mostra_menu():
    print()
    print("===== STUDY PLANNER =====")
    print("1. Mostra le attività")
    print("2. Aggiungi un'attività")
    print("3. Segna un'attività come completata")
    print("4. Genera il riepilogo ed esporta il file per la pagina web")
    print("5. Modifica un'attività")
    print("0. Esci")


def mostra_attivita(attivita):
    """Stampa l'elenco: prima le aperte, poi le completate."""
    if len(attivita) == 0:
        print("Nessuna attività registrata.")
        return
    print(f"{'Id':>3}  {'Stato':<11} {'Priorità':<8} {'Inizio':<10} {'Minuti':>6}  Titolo (categoria)")
    ordinate = sorted(attivita, key=lambda a: (a["completata"], a["id"]))
    for a in ordinate:
        stato = "completata" if a["completata"] else "aperta"
        print(f"{a['id']:>3}  {stato:<11} {a['priorita']:<8} {logic.formatta_data(a['data_inizio']):<10} "
              f"{a['impegno_minuti']:>6}  "
              f"{a['titolo']} ({a['categoria']})")


def operazione_aggiungi(attivita):
    """Operazione 1: chiede i dati, li controlla e salva la nuova attività."""
    titolo = logic.pulisci_testo(input("Titolo: "))
    if titolo is None:
        print("Errore: il titolo non può essere vuoto. Nessuna attività aggiunta.")
        return

    priorita = logic.converti_priorita(input("Priorità (alta/media/bassa o 1/2/3, invio = media): "))
    if priorita is None:
        print("Errore: la priorità deve essere alta, media o bassa (oppure 1, 2, 3). "
              "Nessuna attività aggiunta.")
        return

    categoria = logic.pulisci_testo(input("Categoria: "))
    if categoria is None:
        print("Errore: la categoria non può essere vuota. Nessuna attività aggiunta.")
        return

    oggi = date.today().isoformat()
    data_inizio = logic.converti_data(
        input(f"Data di inizio (GG/MM/AAAA, invio = oggi {logic.formatta_data(oggi)}): "), oggi)
    if data_inizio is None:
        print("Errore: la data deve essere una data reale nel formato GG/MM/AAAA. "
              "Nessuna attività aggiunta.")
        return

    minuti = logic.converti_minuti(input("Impegno stimato in minuti: "))
    if minuti is None:
        print("Errore: l'impegno deve essere un numero intero di minuti maggiore di 0. "
              "Nessuna attività aggiunta.")
        return

    nuova = logic.aggiungi_attivita(attivita, titolo, priorita, categoria, data_inizio, minuti)
    storage.salva_attivita(attivita)
    print(f"Attività aggiunta con id {nuova['id']}.")


def operazione_completa(attivita):
    """Operazione 2: segna come completata l'attività scelta e salva."""
    aperte = logic.attivita_aperte(attivita)
    if len(aperte) == 0:
        print("Non ci sono attività aperte.")
        return

    print("Attività aperte:")
    for a in aperte:
        print(f"  {a['id']}. {a['titolo']} ({a['categoria']}, priorità {a['priorita']}, "
              f"inizio {logic.formatta_data(a['data_inizio'])}, {a['impegno_minuti']} min)")

    id_scelto = logic.converti_id(input("Id dell'attività completata: "))
    if id_scelto is None:
        print("Errore: l'id deve essere un numero intero maggiore di 0.")
        return

    esito = logic.segna_completata(attivita, id_scelto)
    if esito == "non_trovata":
        print("Attività non trovata.")
    elif esito == "gia_completata":
        print("L'attività era già completata.")
    else:
        storage.salva_attivita(attivita)
        print("Attività segnata come completata.")


# Per ogni campo modificabile: (etichetta, funzione di conversione, messaggio d'errore)
CAMPI = {
    "titolo": ("Titolo", logic.pulisci_testo, "il titolo non può essere vuoto."),
    "priorita": ("Priorità (alta/media/bassa o 1/2/3)", logic.converti_priorita,
                 "la priorità deve essere alta, media o bassa (oppure 1, 2, 3)."),
    "categoria": ("Categoria", logic.pulisci_testo, "la categoria non può essere vuota."),
    "data_inizio": ("Data di inizio (GG/MM/AAAA)", logic.converti_data,
                    "la data deve essere una data reale nel formato GG/MM/AAAA."),
    "impegno_minuti": ("Impegno in minuti", logic.converti_minuti,
                       "l'impegno deve essere un numero intero di minuti maggiore di 0."),
    "completata": ("Stato (aperta/completata)", logic.converti_stato,
                   "lo stato deve essere «aperta» o «completata»."),
}


def testo_valore(campo, valore):
    """Come mostrare all'utente il valore attuale di un campo."""
    if campo == "completata":
        return "completata" if valore else "aperta"
    if campo == "data_inizio":
        return logic.formatta_data(valore)
    return str(valore)


def chiedi_valore(campo, attuale):
    """Chiede il nuovo valore di un campo; Invio lascia quello attuale.

    Restituisce il valore convertito, oppure None se l'input non è valido.
    """
    etichetta, converti, errore = CAMPI[campo]
    testo = input(f"{etichetta} [{testo_valore(campo, attuale)}] (Invio = invariato): ")
    if testo.strip() == "":
        return attuale
    valore = converti(testo)
    if valore is None:
        print(f"Errore: {errore} Nessuna modifica salvata.")
    return valore


def operazione_modifica(attivita):
    """Operazione 5: modifica un solo campo o tutta l'attività scelta, poi salva."""
    if len(attivita) == 0:
        print("Nessuna attività registrata.")
        return
    mostra_attivita(attivita)

    id_scelto = logic.converti_id(input("Id dell'attività da modificare: "))
    if id_scelto is None:
        print("Errore: l'id deve essere un numero intero maggiore di 0.")
        return
    attuale = logic.trova_attivita(attivita, id_scelto)
    if attuale is None:
        print("Attività non trovata.")
        return

    campi = list(CAMPI)
    tutta = len(campi) + 1
    print("Cosa vuoi modificare?")
    for numero, campo in enumerate(campi, start=1):
        nome = CAMPI[campo][0].split(" (")[0]
        print(f"  {numero}. {nome}: {testo_valore(campo, attuale[campo])}")
    print(f"  {tutta}. Tutta l'attività")
    print("  0. Annulla")
    scelta = input("Scelta: ").strip()

    if scelta == "0":
        print("Modifica annullata.")
        return
    if scelta == str(tutta):
        da_chiedere = campi
    elif scelta.isdigit() and 1 <= int(scelta) < tutta:
        da_chiedere = [campi[int(scelta) - 1]]
    else:
        print(f"Scelta non valida: scrivi un numero da 0 a {tutta}.")
        return

    modifiche = {}
    for campo in da_chiedere:
        valore = chiedi_valore(campo, attuale[campo])
        if valore is None:          # input non valido: non si salva niente
            return
        modifiche[campo] = valore

    esito = logic.modifica_attivita(attivita, id_scelto, modifiche)
    if esito == "nessuna_modifica":
        print("Nessun valore cambiato.")
    else:
        storage.salva_attivita(attivita)
        print("Attività modificata.")


def operazione_riepilogo(attivita):
    """Operazione 3: calcola il riepilogo, lo stampa e lo esporta in JSON."""
    riepilogo = logic.calcola_riepilogo(attivita)
    if riepilogo["attivita_totali"] == 0:
        print("Attenzione: non ci sono attività, il riepilogo è vuoto.")

    print(f"Attività totali:   {riepilogo['attivita_totali']}")
    print(f"Aperte:            {riepilogo['aperte']}")
    print(f"Completate:        {riepilogo['completate']}")
    print(f"Minuti residui:    {riepilogo['minuti_residui']}")
    print(f"Avanzamento:       {riepilogo['avanzamento_percentuale']}%")
    for voce in riepilogo["per_categoria"]:
        print(f"  - {voce['categoria']}: {voce['completate']}/{voce['totale']} completate, "
              f"{voce['minuti_residui']} min residui")

    percorso = storage.esporta_riepilogo(riepilogo)
    print(f"Riepilogo esportato in: {percorso.parent.name}/{percorso.name}")
    print("Caricalo nella pagina frontend/index.html con «Scegli file JSON».")


def main():
    try:
        attivita = storage.carica_attivita()
    except storage.ErroreDati as errore:
        print(f"Errore nei dati: {errore}")
        print("Il file non è stato modificato. Correggilo (o ripristina una copia) e riavvia.")
        return

    if not storage.FILE_ATTIVITA.exists():
        print("Archivio non trovato: si parte con un elenco vuoto.")

    while True:
        mostra_menu()
        scelta = input("Scelta: ").strip()

        if scelta == "1":
            mostra_attivita(attivita)
        elif scelta == "2":
            operazione_aggiungi(attivita)
        elif scelta == "3":
            operazione_completa(attivita)
        elif scelta == "4":
            operazione_riepilogo(attivita)
        elif scelta == "5":
            operazione_modifica(attivita)
        elif scelta == "0":
            print("Arrivederci!")
            break
        else:
            print("Scelta non valida: scrivi un numero da 0 a 5.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C o fine dell'input: si esce senza errori; i dati sono già salvati
        print("\nProgramma interrotto. Arrivederci!")
