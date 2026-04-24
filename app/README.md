# SmartPreventivo

Piattaforma web con chatbot conversazionale per la generazione di preventivi nel settore edilizio.

**Progetto didattico – Informatica Classe 5ª**
Collegamento: Informatica · Sistemi e Reti · TPSIT · GPOI

---

## Struttura del progetto

```
smartpreventivo/
├── run.py                      ← Punto di ingresso (avvia Flask)
├── config.py                   ← Configurazione (DB, email, chiave)
├── requirements.txt
├── data/
│   └── categorie.json          ← Categorie e domande (configurabile senza toccare il codice)
├── app/
│   ├── __init__.py             ← App factory (crea e configura Flask)
│   ├── models.py               ← Modelli SQLAlchemy (ER → codice)
│   ├── blueprints/
│   │   ├── chat.py             ← API REST chatbot
│   │   └── admin.py            ← Pannello amministrativo
│   ├── repositories/           ← Repository Pattern (accesso al DB)
│   │   ├── sessione_repo.py
│   │   ├── lead_repo.py
│   │   └── categoria_repo.py
│   ├── services/
│   │   ├── calcolo_stima.py    ← Motore di calcolo preventivi
│   │   └── email_service.py    ← Invio email SMTP
│   └── static/
│       ├── css/style.css       ← Stile homepage + chatbot
│       └── js/chatbot.js       ← Logica frontend chatbot (Fetch API)
└── templates/
    ├── index.html              ← Homepage con widget chatbot
    └── admin/
        ├── login.html
        ├── dashboard.html
        └── dettaglio_lead.html
```

---

## Installazione e avvio

```bash
# 1. Crea e attiva l'ambiente virtuale
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 2. Installa le dipendenze
pip install -r requirements.txt

# 3. Avvia il server Flask
python run.py
```

Apri il browser su: **http://localhost:5000**

### Credenziali admin di default
- Email: `admin@smartpreventivo.it`
- Password: `admin123`

> ⚠️ Cambia la password in produzione!

---

## Configurazione email (opzionale)

Nel file `.env` o direttamente in `config.py`:

```
MAIL_USERNAME=tuoemail@gmail.com
MAIL_PASSWORD=tua-app-password-gmail
MAIL_AZIENDA=destinatario@azienda.it
```

> Per Gmail è necessario usare una **App Password** (non la password normale).

---

## API REST – Riferimento

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| POST | `/api/chat/start` | Avvia sessione chat |
| POST | `/api/chat/categoria` | Seleziona categoria |
| POST | `/api/chat/risposta` | Salva risposta a domanda |
| POST | `/api/chat/contatti` | Salva contatti, calcola stima, crea lead |
| POST | `/api/lead/sopralluogo` | Richiede sopralluogo |
| GET  | `/admin/dashboard` | Pannello admin (protetto) |
| GET  | `/admin/export-csv` | Esporta lead in CSV |

---

## Collegamento ai requisiti

| Requisito | Dove è implementato |
|-----------|---------------------|
| RF-01 Avvio chat | `chat.py → /api/chat/start` |
| RF-02 Selezione categoria | `chat.py → /api/chat/categoria` |
| RF-03 Domande guidate | `chat.py → /api/chat/risposta` |
| RF-04 Calcolo stima | `services/calcolo_stima.py` |
| RF-05 Raccolta contatti | `chat.py → /api/chat/contatti` |
| RF-06 Richiesta sopralluogo | `chat.py → /api/lead/sopralluogo` |
| RF-07 Salvataggio lead | `repositories/lead_repo.py` |
| RF-08 Invio email | `services/email_service.py` |
| RF-09 Pannello admin | `blueprints/admin.py` |
| RNF-03 Hashing bcrypt | `models.py → Amministratore.set_password()` |
| RNF-05 Scalabilità | `data/categorie.json` |
| RNF-06 Repository Pattern | `repositories/` |
