"""
Blueprint: chat
Gestisce le API REST del chatbot.

Route:
  POST /api/chat/start           → avvia sessione
  POST /api/chat/categoria       → sceglie categoria e restituisce domande
  POST /api/chat/risposta        → salva risposta e restituisce prossima domanda
  POST /api/chat/contatti        → salva contatti, calcola stima, crea lead
  POST /api/lead/sopralluogo     → richiede sopralluogo
"""

import re
from flask import Blueprint, request, jsonify, current_app

from app.repositories.sessione_repo import SessioneRepository
from app.repositories.lead_repo import LeadRepository
from app.repositories.categoria_repo import CategoriaRepository
from app.services.calcolo_stima import calcola_stima
from app.services.email_service import invia_email_utente, invia_email_azienda

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')
lead_bp = Blueprint('lead', __name__, url_prefix='/api/lead')

# ─────────────────────────────────────────────
# RF-01 – Avvio sessione
# ─────────────────────────────────────────────
@chat_bp.route('/start', methods=['POST'])
def start():
    """Crea una nuova sessione chat e restituisce il token."""
    sessione = SessioneRepository.crea_sessione()
    SessioneRepository.aggiungi_messaggio(sessione.id, 'bot',
        'Ciao! Sono SmartPreventivo 👋\nSeleziona la categoria di lavoro per ricevere una stima gratuita.')

    categorie = CategoriaRepository.get_all_attive()
    return jsonify({
        'session_token': sessione.session_token,
        'messaggio': 'Ciao! Sono SmartPreventivo 👋\nSeleziona la categoria di lavoro per ricevere una stima gratuita.',
        'categorie': [{'id': c.id, 'nome': c.nome, 'icona': c.icona} for c in categorie]
    })


# ─────────────────────────────────────────────
# RF-02 – Selezione categoria
# ─────────────────────────────────────────────
@chat_bp.route('/categoria', methods=['POST'])
def seleziona_categoria():
    """
    L'utente ha scelto una categoria.
    Salva il messaggio e restituisce la prima domanda.
    """
    data = request.get_json()
    token = data.get('session_token')
    categoria_id = data.get('categoria_id')

    sessione = SessioneRepository.get_by_token(token)
    if not sessione:
        return jsonify({'errore': 'Sessione non trovata'}), 404

    categoria = CategoriaRepository.get_by_id(categoria_id)
    if not categoria:
        return jsonify({'errore': 'Categoria non trovata'}), 404

    # Salva in sessione la categoria scelta (tramite risposta virtuale)
    # Usiamo la sessione Flask per tenere traccia dello stato della chat
    SessioneRepository.aggiungi_messaggio(sessione.id, 'utente', categoria.nome)
    SessioneRepository.aggiungi_messaggio(sessione.id, 'bot',
        f'Ottima scelta! Rispondo per la categoria: {categoria.nome} {categoria.icona}')

    domande = CategoriaRepository.get_domande(categoria_id)
    prima_domanda = domande[0] if domande else None

    return jsonify({
        'categoria': {'id': categoria.id, 'nome': categoria.nome, 'icona': categoria.icona},
        'domande_totali': len(domande),
        'prima_domanda': _domanda_to_dict(prima_domanda) if prima_domanda else None,
        'messaggio': f'Perfetto! Ho bisogno di alcune informazioni per calcolare la stima.'
    })


# ─────────────────────────────────────────────
# RF-03 – Salva risposta  (<<include>> Salva risposta in sessione)
# ─────────────────────────────────────────────
@chat_bp.route('/risposta', methods=['POST'])
def salva_risposta():
    """
    Salva la risposta alla domanda corrente.
    Restituisce la domanda successiva, o il form contatti se finita.
    """
    data = request.get_json()
    token = data.get('session_token')
    domanda_id = data.get('domanda_id')
    valore = data.get('valore', '').strip()

    sessione = SessioneRepository.get_by_token(token)
    if not sessione:
        return jsonify({'errore': 'Sessione non trovata'}), 404

    domanda = CategoriaRepository.get_domanda_by_id(domanda_id)
    if not domanda:
        return jsonify({'errore': 'Domanda non trovata'}), 404

    # <<include>> Salva risposta in sessione
    LeadRepository.salva_risposta(sessione.id, domanda_id, valore)
    SessioneRepository.aggiungi_messaggio(sessione.id, 'utente', valore)

    # Trova la prossima domanda della stessa categoria
    domande = CategoriaRepository.get_domande(domanda.categoria_id)
    prossima = None
    for i, d in enumerate(domande):
        if d.id == domanda_id and i + 1 < len(domande):
            prossima = domande[i + 1]
            break

    if prossima:
        SessioneRepository.aggiungi_messaggio(sessione.id, 'bot', prossima.testo)
        return jsonify({
            'prossima_domanda': _domanda_to_dict(prossima),
            'completato': False
        })
    else:
        # Tutte le domande completate → chiedi i contatti
        SessioneRepository.aggiungi_messaggio(sessione.id, 'bot',
            'Perfetto! Ora ho bisogno dei tuoi dati per inviarti la stima.')
        return jsonify({
            'prossima_domanda': None,
            'completato': True,
            'messaggio': 'Perfetto! Ora ho bisogno dei tuoi dati per inviarti la stima.'
        })


# ─────────────────────────────────────────────
# RF-04/05 – Contatti + Calcolo stima + Crea lead
# ─────────────────────────────────────────────
@chat_bp.route('/contatti', methods=['POST'])
def salva_contatti():
    """
    RF-05: Raccoglie i dati di contatto.
    <<include>> Verifica formato email/telefono.
    RF-04: Calcola stima e crea il lead.
    RF-07: Salva il lead nel DB.
    RF-08: Invia email.
    """
    data = request.get_json()
    token       = data.get('session_token')
    categoria_id = data.get('categoria_id')
    nome        = data.get('nome', '').strip()
    email       = data.get('email', '').strip()
    telefono    = data.get('telefono', '').strip()

    # Validazione sessione
    sessione = SessioneRepository.get_by_token(token)
    if not sessione:
        return jsonify({'errore': 'Sessione non trovata'}), 404

    # <<include>> Verifica formato email/telefono
    errori = _valida_contatti(nome, email, telefono)
    if errori:
        return jsonify({'errori': errori}), 400

    # Recupera le risposte della sessione per il calcolo
    risposte_obj = LeadRepository.get_risposte_sessione(sessione.id)
    risposte_valori = [r.valore for r in risposte_obj]

    categoria = CategoriaRepository.get_by_id(categoria_id)
    if not categoria:
        return jsonify({'errore': 'Categoria non trovata'}), 404

    # RF-04 – Calcolo stima
    stima_min, stima_max = calcola_stima(categoria.nome, risposte_valori)

    # RF-07 – Salva lead
    lead = LeadRepository.crea_lead(
        sessione_id=sessione.id,
        categoria_id=categoria_id,
        nome=nome,
        email=email,
        telefono=telefono,
        stima_min=stima_min,
        stima_max=stima_max
    )

    # Chiudi la sessione
    SessioneRepository.chiudi_sessione(sessione)
    SessioneRepository.aggiungi_messaggio(sessione.id, 'bot',
        f'Stima calcolata: da {stima_min:.0f}€ a {stima_max:.0f}€')

    # RF-08 – Invia email (non blocca la risposta se fallisce)
    invia_email_utente(lead)
    invia_email_azienda(lead)

    return jsonify({
        'lead_id': lead.id,
        'stima_min': float(stima_min),
        'stima_max': float(stima_max),
        'messaggio': f'Ecco la tua stima indicativa per {categoria.nome}!',
        'riepilogo': {
            'categoria': categoria.nome,
            'nome': nome,
            'email': email,
            'risposte': risposte_valori
        }
    })


# ─────────────────────────────────────────────
# RF-06 – Richiedi sopralluogo  (<<extend>> Visualizza stima)
# ─────────────────────────────────────────────
@lead_bp.route('/sopralluogo', methods=['POST'])
def richiedi_sopralluogo():
    """
    <<extend>> Richiedi sopralluogo: azione opzionale dopo la stima.
    """
    data = request.get_json()
    lead_id = data.get('lead_id')

    lead = LeadRepository.richiedi_sopralluogo(lead_id)
    if not lead:
        return jsonify({'errore': 'Lead non trovato'}), 404

    # Invia email aggiornata
    invia_email_azienda(lead)

    return jsonify({
        'successo': True,
        'messaggio': 'Sopralluogo richiesto! Ti contatteremo entro 24 ore. 🏗️'
    })


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────
def _domanda_to_dict(domanda):
    """Converte una Domanda in dict serializzabile per JSON."""
    import json as _json
    opzioni = []
    if domanda.opzioni:
        try:
            opzioni = _json.loads(domanda.opzioni)
        except Exception:
            opzioni = []
    return {
        'id': domanda.id,
        'testo': domanda.testo,
        'tipo_input': domanda.tipo_input,
        'opzioni': opzioni,
        'ordine': domanda.ordine,
        'obbligatoria': domanda.obbligatoria
    }


def _valida_contatti(nome, email, telefono):
    """
    <<include>> Verifica formato email/telefono.
    Restituisce una lista di errori (vuota se tutto ok).
    """
    errori = []
    if not nome or len(nome) < 2:
        errori.append('Il nome deve avere almeno 2 caratteri.')
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        errori.append('Formato email non valido.')
    # Accetta numeri italiani con o senza prefisso internazionale
    if not re.match(r'^(\+39)?[\s\-]?3\d{8,9}$|^0\d{5,10}$', telefono.replace(' ', '')):
        errori.append('Formato telefono non valido (es. 3391234567 o +39 339 1234567).')
    return errori
