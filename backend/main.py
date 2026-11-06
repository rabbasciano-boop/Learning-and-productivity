import logic
import storage
from enum import Enum


class Priorita(Enum):
    ALTA = "alta"
    MEDIA = "media"
    BASSA = "bassa"

def main():
    attivita = []

    titolo = input("Titolo dell'attività: ").strip()
    attivita.append({"titolo": titolo, "completata": False})
    
    argomento = input("Inserisci l'argomento: ").strip()
    attivita.append({"argomento": titolo, "completata": False})











    if __name__ == "__main__":
    main()