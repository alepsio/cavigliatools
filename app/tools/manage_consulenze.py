from flask import Blueprint, render_template, session, request, flash, redirect, url_for
from app.routes.decorators import has_package
from app.db import get_db
import os

manage_consulenze_bp = Blueprint('manage_consulenze', __name__, url_prefix='/manage_consulenze')

@manage_consulenze_bp.route('/')
@has_package("manage_consulenze")
def index():
    return render_template(
        'tools/manage_consulenze.html',
        current_tool="manage_consulenze",
        current_tool_name="🛡️ Gestione Consulenze",
        user_tools=session.get("pacchetti", []),
        tool_routes={
            "manage_consulenze": "manage_consulenze.index",
            "manage_drivers": "manage_drivers.index",
            "fatture": "fatture.index"
        }
    )


@manage_consulenze_bp.route('/inserisci_cliente', methods=['POST'])
@has_package("manage_consulenze")
def inserisci_cliente():
    conn = get_db()
    cur = conn.cursor()

    # Ottieni dati dal form
    data = request.form
    files = request.files


    doc_fronte = files['doc_fronte'].filename
    doc_retro = files['doc_retro'].filename
    polizza_precedente = files['polizza_precedente'].filename

    # Salva i file se presenti
    upload_folder = os.path.join("static", "upload_clienti")
    os.makedirs(upload_folder, exist_ok=True)

    if doc_fronte:
        files['doc_fronte'].save(os.path.join(upload_folder, doc_fronte))
    if doc_retro:
        files['doc_retro'].save(os.path.join(upload_folder, doc_retro))
    if polizza_precedente:
        files['polizza_precedente'].save(os.path.join(upload_folder, polizza_precedente))

    cur.execute("""
        INSERT INTO clienti_assicurativi (
            cliente_id, nome, data_nascita, luogo_nascita, codice_fiscale, partita_iva,
            attivita, inizio_attivita, num_albo, data_albo, residenza, domicilio,
            ubicazione, email, pec, codice_univoco, cellulare,
            doc_fronte, doc_retro, polizza_precedente,
            fatturato_2024, fatturato_2025, dipendenti, addetti, subappaltatori
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        session["user_id"],
        data['nome'], data['data_nascita'], data['luogo_nascita'], data['codice_fiscale'],
        data['partita_iva'], data['attivita'], data['inizio_attivita'],
        data['num_albo'], data['data_albo'], data['residenza'], data['domicilio'],
        data['ubicazione'], data['email'], data['pec'], data['codice_univoco'], data['cellulare'],
        doc_fronte, doc_retro, polizza_precedente,
        data['fatturato_2024'], data['fatturato_2025'],
        data['dipendenti'], data['addetti'], data['subappaltatori']
        
    ))

    conn.commit()
    cur.close()
    flash("Cliente registrato correttamente.")
    return redirect(url_for("manage_consulenze.index"))

@manage_consulenze_bp.route('/questionari')
@has_package("manage_consulenze")
def questionari():
    return render_template("tools/questionari.html",
        current_tool="manage_consulenze",
        current_tool_name="📋 Gestione Consulenze",
        user_tools=session.get("pacchetti", []),
        tool_routes={
            "manage_consulenze": "manage_consulenze.index",
            "fatture": "fatture.index",
            "questionari": "manage_consulenze.questionari"
        }
    )
