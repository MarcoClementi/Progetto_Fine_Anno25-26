"""
App Factory – SmartPreventivo
Crea e configura l'applicazione Flask registrando tutti i Blueprint.
"""

import json
import os
from flask import Flask, render_template
from flask_login import LoginManager

from config import Config
from app.models import db, Amministratore
from app.services.email_service import mail


def create_app(config_class=Config):
    """Factory function: crea e restituisce l'app Flask configurata."""

    app = Flask(__name__,
                template_folder='../templates',
                static_folder='static')
    app.config.from_object(config_class)

    # ── Inizializza estensioni ──────────────────
    db.init_app(app)
    mail.init_app(app)

    # ── Flask-Login ─────────────────────────────
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'
    login_manager.login_message = 'Effettua il login per accedere al pannello.'

    @login_manager.user_loader
    def load_user(user_id):
        return Amministratore.query.get(int(user_id))

    # ── Registra Blueprint ──────────────────────
    from app.blueprints.chat import chat_bp, lead_bp
    from app.blueprints.admin import admin_bp

    app.register_blueprint(chat_bp)
    app.register_blueprint(lead_bp)
    app.register_blueprint(admin_bp)

    # ── Route principale (homepage con chatbot) ─
    @app.route('/')
    def index():
        return render_template('index.html')

    # ── Crea tabelle e dati iniziali ────────────
    with app.app_context():
        db.create_all()
        _seed_db(app)

    return app


def _seed_db(app):
    """
    Popola il database con i dati iniziali se è vuoto:
    - Admin di default
    - Categorie e domande dal file JSON
    """
    from app.models import Amministratore, CategoriaLavoro, Domanda

    # Admin di default (cambiare la password in produzione!)
    if not Amministratore.query.first():
        admin = Amministratore(nome='Admin', email='admin@smartpreventivo.it')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        app.logger.info('Admin di default creato: admin@smartpreventivo.it / admin123')

    # Categorie e domande dal JSON
    if not CategoriaLavoro.query.first():
        data_path = os.path.join(app.config['DATA_DIR'], 'categorie.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            categorie_data = json.load(f)

        for cat_data in categorie_data:
            cat = CategoriaLavoro(
                nome=cat_data['nome'],
                descrizione=cat_data.get('descrizione', ''),
                icona=cat_data.get('icona', '🔧'),
                attiva=True
            )
            db.session.add(cat)
            db.session.flush()  # ottieni l'id prima del commit

            for domanda_data in cat_data.get('domande', []):
                opzioni = domanda_data.get('opzioni', [])
                dom = Domanda(
                    categoria_id=cat.id,
                    testo=domanda_data['testo'],
                    tipo_input=domanda_data.get('tipo_input', 'text'),
                    opzioni=json.dumps(opzioni, ensure_ascii=False) if opzioni else None,
                    ordine=domanda_data.get('ordine', 0),
                    obbligatoria=domanda_data.get('obbligatoria', True)
                )
                db.session.add(dom)

        db.session.commit()
        app.logger.info(f'{len(categorie_data)} categorie caricate dal JSON.')
