"""Study Planner — avvio con: python main.py

Qui stanno il menu e il dialogo con l'utente nel terminale.
Le regole sono in logic.py, la lettura/scrittura dei file in storage.py.
"""

import logic
import storage


def mostra_menu():
    print()
    print("===== STUDY PLANNER =====")
    print("1. Mostra le attività")
    print("2. Aggiungi un'attività")
    print("3. Segna un'attività come completata")
    print("4. Genera il riepilogo ed esporta il file per la pagina web")
    print("0. Esci")


def mostra_attivita(attivita):
    """Stampa l'elenco: prima le aperte, poi le completate."""
    if len(attivita) == 0:
        print("Nessuna attività registrata.")
        return
    print(f"{'Id':>3}  {'Stato':<11} {'Minuti':>6}  Titolo (materia)")
    ordinate = sorted(attivita, key=lambda a: (a["completata"], a["id"]))
    for a in ordinate:
        stato = "completata" if a["completata"] else "aperta"
        print(f"{a['id']:>3}  {stato:<11} {a['impegno_minuti']:>6}  {a['titolo']} ({a['materia']})")


def operazione_aggiungi(attivita):
    """Operazione 1: chiede i dati, li controlla e salva la nuova attività."""
    titolo = logic.pulisci_testo(input("Titolo: "))
    if titolo is None:
        print("Errore: il titolo non può essere vuoto. Nessuna attività aggiunta.")
        return

    materia = logic.pulisci_testo(input("Materia: "))
    if materia is None:
        print("Errore: la materia non può essere vuota. Nessuna attività aggiunta.")
        return

    minuti = logic.converti_minuti(input("Impegno stimato in minuti: "))
    if minuti is None:
        print("Errore: l'impegno deve essere un numero intero di minuti maggiore di 0. "
              "Nessuna attività aggiunta.")
        return

    nuova = logic.aggiungi_attivita(attivita, titolo, materia, minuti)
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
        print(f"  {a['id']}. {a['titolo']} ({a['materia']}, {a['impegno_minuti']} min)")

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
        elif scelta == "0":
            print("Arrivederci!")
            break
        else:
            print("Scelta non valida: scrivi un numero da 0 a 4.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C o fine dell'input: si esce senza errori; i dati sono già salvati
        print("\nProgramma interrotto. Arrivederci!")
