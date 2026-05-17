"""
Blueprint: admin
Gestisce il pannello amministrativo (RF-09 – Pannello amministrativo).

Route:
  GET/POST /admin/login       → login admin
  GET      /admin/logout      → logout
  GET      /admin/dashboard   → lista lead con filtri
  GET      /admin/lead/<id>   → dettaglio lead
  GET      /admin/export-csv  → <<extend>> esporta lead in CSV
"""

import csv
import io
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, Response)
from flask_login import login_user, logout_user, login_required, current_user

from app.models import Amministratore
from app.repositories.lead_repo import LeadRepository
from app.repositories.categoria_repo import CategoriaRepository

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ─────────────────────────────────────────────
# RF-09 – Login  (<<include>> Verifica autenticazione admin)
# ─────────────────────────────────────────────
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        admin = Amministratore.query.filter_by(email=email).first()

        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Email o password non corretti.', 'errore')

    return render_template('admin/login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))


# ─────────────────────────────────────────────
# RF-09 – Dashboard lead con filtri
# ─────────────────────────────────────────────
@admin_bp.route('/dashboard')
@login_required   # <<include>> Verifica autenticazione admin
def dashboard():
    # Leggi i filtri dalla query string
    categoria_id = request.args.get('categoria_id', type=int)
    stato        = request.args.get('stato')

    lead = LeadRepository.get_all(categoria_id=categoria_id, stato=stato)
    categorie = CategoriaRepository.get_all_attive()

    # Statistiche rapide
    totale       = len(lead)
    nuovi        = sum(1 for l in lead if l.stato_lead == 'nuovo')
    sopralluoghi = sum(1 for l in lead if l.sopralluogo_richiesto)

    return render_template('admin/dashboard.html',
        lead=lead,
        categorie=categorie,
        totale=totale,
        nuovi=nuovi,
        sopralluoghi=sopralluoghi,
        filtro_cat=categoria_id,
        filtro_stato=stato
    )


# ─────────────────────────────────────────────
# Dettaglio lead
# ─────────────────────────────────────────────
@admin_bp.route('/lead/<int:lead_id>')
@login_required
def dettaglio_lead(lead_id):
    lead = LeadRepository.get_by_id(lead_id)
    if not lead:
        flash('Lead non trovato.', 'errore')
        return redirect(url_for('admin.dashboard'))

    risposte = LeadRepository.get_risposte_sessione(lead.sessione_id)
    return render_template('admin/dettaglio_lead.html', lead=lead, risposte=risposte)


# ─────────────────────────────────────────────
# <<extend>> Esporta lead in CSV
# ─────────────────────────────────────────────
@admin_bp.route('/export-csv')
@login_required
def export_csv():
    """
    <<extend>> Gestisci lead → Esporta lead in CSV.
    Funzione opzionale aggiuntiva del pannello admin.
    """
    categoria_id = request.args.get('categoria_id', type=int)
    stato        = request.args.get('stato')

    lead = LeadRepository.get_all(categoria_id=categoria_id, stato=stato)

    output = io.StringIO()
    writer = csv.writer(output)

    # Intestazione CSV
    writer.writerow(['ID', 'Nome', 'Email', 'Telefono', 'Categoria',
                     'Stima Min (€)', 'Stima Max (€)', 'Stato',
                     'Sopralluogo', 'Data'])

    for l in lead:
        writer.writerow([
            l.id,
            l.nome_cliente,
            l.email_cliente,
            l.telefono_cliente,
            l.categoria.nome if l.categoria else '-',
            l.stima_min,
            l.stima_max,
            l.stato_lead,
            'Sì' if l.sopralluogo_richiesto else 'No',
            l.data_creazione.strftime('%d/%m/%Y %H:%M')
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=lead_smartpreventivo.csv'}
    )
