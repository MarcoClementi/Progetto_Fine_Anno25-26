"""
LeadRepository
Gestisce tutte le operazioni DB relative a Lead e RispostaDomanda.
"""

from app.models import db, Lead, RispostaDomanda


class LeadRepository:

    @staticmethod
    def crea_lead(sessione_id, categoria_id, nome, email, telefono, stima_min, stima_max):
        """Crea e salva un nuovo lead nel database."""
        lead = Lead(
            sessione_id=sessione_id,
            categoria_id=categoria_id,
            nome_cliente=nome,
            email_cliente=email,
            telefono_cliente=telefono,
            stima_min=stima_min,
            stima_max=stima_max,
            stato_lead='nuovo'
        )
        db.session.add(lead)
        db.session.commit()
        return lead

    @staticmethod
    def get_by_id(lead_id):
        """Recupera un lead tramite ID."""
        return Lead.query.get(lead_id)

    @staticmethod
    def get_all(categoria_id=None, stato=None):
        """Restituisce tutti i lead, con filtri opzionali per categoria e stato."""
        query = Lead.query
        if categoria_id:
            query = query.filter_by(categoria_id=categoria_id)
        if stato:
            query = query.filter_by(stato_lead=stato)
        return query.order_by(Lead.data_creazione.desc()).all()

    @staticmethod
    def richiedi_sopralluogo(lead_id):
        """Aggiorna il lead impostando sopralluogo_richiesto = True."""
        lead = Lead.query.get(lead_id)
        if lead:
            lead.richiedi_sopralluogo()
            db.session.commit()
        return lead

    @staticmethod
    def salva_risposta(sessione_id, domanda_id, valore):
        """Salva la risposta a una domanda guidata."""
        risposta = RispostaDomanda(
            sessione_id=sessione_id,
            domanda_id=domanda_id,
            valore=valore
        )
        db.session.add(risposta)
        db.session.commit()
        return risposta

    @staticmethod
    def get_risposte_sessione(sessione_id):
        """Recupera tutte le risposte di una sessione."""
        return RispostaDomanda.query.filter_by(sessione_id=sessione_id).all()
