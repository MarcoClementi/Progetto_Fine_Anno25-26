import os

class Config:
    # Chiave segreta per le sessioni Flask (cambiare in produzione!)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smartpreventivo-dev-key-2026')

    # Database SQLite
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(BASE_DIR, 'smartpreventivo.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email SMTP (Gmail)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'tuoemail@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'tuapassword')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', 'tuoemail@gmail.com')

    # Email destinatario aziendale
    MAIL_AZIENDA = os.environ.get('MAIL_AZIENDA', 'admin@azienda.it')

    # Percorso dati configurazione categorie
    DATA_DIR = os.path.join(BASE_DIR, 'data')
