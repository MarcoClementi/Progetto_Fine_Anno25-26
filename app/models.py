from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ─────────────────────────────────────────────
# AMMINISTRATORE  (accesso pannello admin)
# ─────────────────────────────────────────────
class Amministratore(UserMixin, db.Model):
    __tablename__ = 'amministratore'

    id             = db.Column(db.Integer, primary_key=True)
    nome           = db.Column(db.String(100), nullable=False)
    email          = db.Column(db.String(150), unique=True, nullable=False)
    password_hash  = db.Column(db.String(256), nullable=False)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Salva la password con hashing bcrypt tramite Werkzeug."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica la password confrontando l'hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Amministratore {self.email}>'


# ─────────────────────────────────────────────
# CATEGORIA_LAVORO
# ─────────────────────────────────────────────
class CategoriaLavoro(db.Model):
    __tablename__ = 'categoria_lavoro'

    id          = db.Column(db.Integer, primary_key=True)
    nome        = db.Column(db.String(100), nullable=False)
    descrizione = db.Column(db.String(255))
    icona       = db.Column(db.String(10), default='🔧')   # emoji icona
    attiva      = db.Column(db.Boolean, default=True)

    # Relazioni
    domande = db.relationship('Domanda', backref='categoria', lazy=True,
                              order_by='Domanda.ordine')
    lead    = db.relationship('Lead', backref='categoria', lazy=True)

    def __repr__(self):
        return f'<CategoriaLavoro {self.nome}>'


# ─────────────────────────────────────────────
# DOMANDA  (domande guidate per categoria)
# ─────────────────────────────────────────────
class Domanda(db.Model):
    __tablename__ = 'domanda'

    id           = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria_lavoro.id'), nullable=False)
    testo        = db.Column(db.String(500), nullable=False)
    tipo_input   = db.Column(db.String(50), default='text')  # text | number | select
    opzioni      = db.Column(db.Text)      # JSON per tipo "select"
    ordine       = db.Column(db.Integer, default=0)
    obbligatoria = db.Column(db.Boolean, default=True)

    # Relazioni
    risposte = db.relationship('RispostaDomanda', backref='domanda', lazy=True)

    def __repr__(self):
        return f'<Domanda {self.testo[:40]}>'


# ─────────────────────────────────────────────
# SESSIONE_CHAT
# ─────────────────────────────────────────────
class SessioneChat(db.Model):
    __tablename__ = 'sessione_chat'

    id            = db.Column(db.Integer, primary_key=True)
    session_token = db.Column(db.String(64), unique=True, nullable=False)
    inizio        = db.Column(db.DateTime, default=datetime.utcnow)
    fine          = db.Column(db.DateTime, nullable=True)
    stato         = db.Column(db.String(30), default='attiva')
    # stato: attiva | completata | abbandonata

    # Relazioni
    messaggi  = db.relationship('MessaggioChat', backref='sessione', lazy=True)
    risposte  = db.relationship('RispostaDomanda', backref='sessione', lazy=True)
    lead      = db.relationship('Lead', backref='sessione', uselist=False)

    def chiudi(self):
        self.fine  = datetime.utcnow()
        self.stato = 'completata'

    def __repr__(self):
        return f'<SessioneChat {self.session_token[:8]}... stato={self.stato}>'


# ─────────────────────────────────────────────
# MESSAGGIO_CHAT
# ─────────────────────────────────────────────
class MessaggioChat(db.Model):
    __tablename__ = 'messaggio_chat'

    id          = db.Column(db.Integer, primary_key=True)
    sessione_id = db.Column(db.Integer, db.ForeignKey('sessione_chat.id'), nullable=False)
    mittente    = db.Column(db.String(10), nullable=False)  # 'bot' | 'utente'
    testo       = db.Column(db.Text, nullable=False)
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MessaggioChat {self.mittente}: {self.testo[:30]}>'


# ─────────────────────────────────────────────
# LEAD  (contatto qualificato generato dalla chat)
# ─────────────────────────────────────────────
class Lead(db.Model):
    __tablename__ = 'lead'

    id                   = db.Column(db.Integer, primary_key=True)
    sessione_id          = db.Column(db.Integer, db.ForeignKey('sessione_chat.id'), nullable=False)
    categoria_id         = db.Column(db.Integer, db.ForeignKey('categoria_lavoro.id'), nullable=False)
    nome_cliente         = db.Column(db.String(150), nullable=False)
    email_cliente        = db.Column(db.String(150), nullable=False)
    telefono_cliente     = db.Column(db.String(30), nullable=False)
    stima_min            = db.Column(db.Numeric(10, 2))
    stima_max            = db.Column(db.Numeric(10, 2))
    stato_lead           = db.Column(db.String(30), default='nuovo')
    # stato_lead: nuovo | in_lavorazione | chiuso | perso
    sopralluogo_richiesto = db.Column(db.Boolean, default=False)
    data_creazione       = db.Column(db.DateTime, default=datetime.utcnow)

    def richiedi_sopralluogo(self):
        self.sopralluogo_richiesto = True
        self.stato_lead = 'in_lavorazione'

    def to_dict(self):
        return {
            'id': self.id,
            'nome_cliente': self.nome_cliente,
            'email_cliente': self.email_cliente,
            'telefono_cliente': self.telefono_cliente,
            'categoria': self.categoria.nome if self.categoria else '-',
            'stima_min': float(self.stima_min) if self.stima_min else 0,
            'stima_max': float(self.stima_max) if self.stima_max else 0,
            'stato_lead': self.stato_lead,
            'sopralluogo_richiesto': self.sopralluogo_richiesto,
            'data_creazione': self.data_creazione.strftime('%d/%m/%Y %H:%M'),
        }

    def __repr__(self):
        return f'<Lead {self.nome_cliente} - {self.stato_lead}>'


# ─────────────────────────────────────────────
# RISPOSTA_DOMANDA
# ─────────────────────────────────────────────
class RispostaDomanda(db.Model):
    __tablename__ = 'risposta_domanda'

    id          = db.Column(db.Integer, primary_key=True)
    sessione_id = db.Column(db.Integer, db.ForeignKey('sessione_chat.id'), nullable=False)
    domanda_id  = db.Column(db.Integer, db.ForeignKey('domanda.id'), nullable=False)
    valore      = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<RispostaDomanda domanda_id={self.domanda_id} valore={self.valore}>'
