"""
CalcoloStima – Servizio per il calcolo della stima min-max.

Legge i prezzi base e i moltiplicatori dal file JSON di configurazione
(data/categorie.json) e applica i moltiplicatori alle risposte dell'utente.
Questo mantiene la logica di calcolo separata e modificabile senza toccare
il codice core (RNF-05 – Scalabilità).
"""

import json
import os
from flask import current_app


def _carica_config_categoria(nome_categoria):
    """Carica la configurazione prezzi per una categoria dal file JSON."""
    data_path = os.path.join(current_app.config['DATA_DIR'], 'categorie.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        categorie = json.load(f)
    for cat in categorie:
        if cat['nome'].lower() == nome_categoria.lower():
            return cat
    return None


def calcola_stima(nome_categoria, risposte):
    """
    Calcola la stima min-max in base alla categoria e alle risposte.

    Args:
        nome_categoria (str): nome della categoria (es. "Fotovoltaico")
        risposte (list): lista di stringhe con le risposte dell'utente

    Returns:
        tuple: (stima_min, stima_max) in euro, oppure (0, 0) se errore
    """
    config = _carica_config_categoria(nome_categoria)
    if not config or 'prezzi' not in config:
        return 0, 0

    prezzi = config['prezzi']
    base_min = prezzi['base_min']
    base_max = prezzi['base_max']
    moltiplicatori = prezzi.get('moltiplicatori', {})

    # Calcola il moltiplicatore totale cercando corrispondenze nelle risposte
    mult = 1.0
    matched = False
    for risposta in risposte:
        for chiave, valore in moltiplicatori.items():
            # Controllo parziale: la risposta contiene la chiave o viceversa
            if chiave.lower() in risposta.lower() or risposta.lower() in chiave.lower():
                mult = valore
                matched = True
                break
        if matched:
            break  # usa il primo moltiplicatore trovato (quello della prima domanda)

    # Applica moltiplicatori aggiuntivi (es. batterie, vetro triplo)
    for risposta in risposte:
        for chiave, valore in moltiplicatori.items():
            if chiave.lower() in risposta.lower() and valore != mult:
                # Moltiplica solo se è un modificatore aggiuntivo (valore < 2)
                if valore < 2.0 and valore != 1.0:
                    mult = mult * valore

    stima_min = round(base_min * mult, 2)
    stima_max = round(base_max * mult, 2)

    # Arrotondamento a centinaia per sembrare più realistico
    stima_min = round(stima_min / 100) * 100
    stima_max = round(stima_max / 100) * 100

    return stima_min, stima_max
