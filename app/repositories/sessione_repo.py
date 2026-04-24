"""
SessioneRepository
Gestisce tutte le operazioni DB relative a SessioneChat e MessaggioChat.
Il Repository Pattern separa la logica di accesso al database dal resto del codice.
"""

import uuid
from app.models import db, SessioneChat, MessaggioChat


class SessioneRepository:

    @staticmethod
    def crea_sessione():
        """Crea una nuova sessione chat con un token univoco."""
        token = uuid.uuid4().hex  # stringa esadecimale di 32 caratteri
        sessione = SessioneChat(session_token=token)
        db.session.add(sessione)
        db.session.commit()
        return sessione

    @staticmethod
    def get_by_token(token):
        """Recupera una sessione dal suo token."""
        return SessioneChat.query.filter_by(session_token=token).first()

    @staticmethod
    def aggiungi_messaggio(sessione_id, mittente, testo):
        """Salva un messaggio nella sessione."""
        msg = MessaggioChat(
            sessione_id=sessione_id,
            mittente=mittente,
            testo=testo
        )
        db.session.add(msg)
        db.session.commit()
        return msg

    @staticmethod
    def chiudi_sessione(sessione):
        """Imposta la sessione come completata."""
        sessione.chiudi()
        db.session.commit()
