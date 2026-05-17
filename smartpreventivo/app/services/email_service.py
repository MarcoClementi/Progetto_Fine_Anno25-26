"""
EmailService – Gestisce l'invio delle email tramite Flask-Mail.
RF-08: Notifica email all'utente e all'azienda.
"""

from flask import current_app
from flask_mail import Mail, Message

mail = Mail()


def invia_email_utente(lead):
    """Invia all'utente un riepilogo della stima ricevuta."""
    try:
        msg = Message(
            subject="Il tuo preventivo SmartPreventivo",
            recipients=[lead.email_cliente]
        )
        msg.body = f"""Ciao {lead.nome_cliente},

grazie per aver utilizzato SmartPreventivo!

Ecco il riepilogo della tua richiesta:
- Categoria: {lead.categoria.nome}
- Stima indicativa: da {lead.stima_min:.0f}€ a {lead.stima_max:.0f}€

Questa è una stima indicativa. Un nostro tecnico ti contatterà per un preventivo definitivo.

{"⭐ Hai richiesto un sopralluogo: sarai contattato entro 24 ore." if lead.sopralluogo_richiesto else "Puoi richiedere un sopralluogo gratuito rispondendo a questa email."}

Cordiali saluti,
Il team SmartPreventivo
"""
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Errore invio email utente: {e}")
        return False


def invia_email_azienda(lead):
    """Invia all'azienda la notifica di un nuovo lead."""
    try:
        destinatario = current_app.config.get('MAIL_AZIENDA', 'admin@azienda.it')
        msg = Message(
            subject=f"[SmartPreventivo] Nuovo lead: {lead.nome_cliente}",
            recipients=[destinatario]
        )
        msg.body = f"""Nuovo lead ricevuto!

Nome: {lead.nome_cliente}
Email: {lead.email_cliente}
Telefono: {lead.telefono_cliente}
Categoria: {lead.categoria.nome}
Stima: {lead.stima_min:.0f}€ – {lead.stima_max:.0f}€
Sopralluogo richiesto: {"SÌ ⚠️" if lead.sopralluogo_richiesto else "No"}
Data: {lead.data_creazione.strftime('%d/%m/%Y %H:%M')}

Accedi al pannello admin per gestire il lead.
"""
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Errore invio email azienda: {e}")
        return False
