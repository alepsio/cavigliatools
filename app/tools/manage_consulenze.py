from flask import Blueprint, render_template, session, request, flash, redirect, url_for, jsonify, send_file
from app.routes.decorators import has_package
from app.db import get_db
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
from werkzeug.utils import secure_filename
import smtplib
from email.message import EmailMessage
import os
from datetime import datetime


import os

manage_consulenze_bp = Blueprint('manage_consulenze', __name__, url_prefix='/manage_consulenze')

def parse_date(value):
    return value if value else None

def safe(value):
    return value if value else ""

def format_date(date_val):
    try:
        if isinstance(date_val, str):
            # Se è già stringa tipo '2024-04-01'
            date_val = datetime.strptime(date_val, "%Y-%m-%d")
        return date_val.strftime("%d/%m/%Y")
    except:
        return ""

def get_all_clienti():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, cognome FROM clienti_assicurativi WHERE cliente_id = %s", (session["user_id"],))
    clienti = cur.fetchall()
    cur.close()
    return [{"id": c[0], "nome": f"{c[1]} {c[2]}"} for c in clienti]

def get_all_templates():
    import os
    path = os.path.join("app", "static", "pdf_templates")
    return [{"filename": f, "nome": f.split(".")[0]} for f in os.listdir(path) if f.endswith(".pdf")]


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

@manage_consulenze_bp.route('/questionari', methods=['GET', 'POST'])
@has_package("manage_consulenze")
def questionari():
    conn = get_db()
    cur = conn.cursor()
    
    # Prendi tutti i clienti dell’utente loggato
    cur.execute("""
        SELECT id, nome, cognome, codice_fiscale
        FROM clienti_assicurativi
        WHERE cliente_id = %s
        ORDER BY cognome ASC
    """, (session["user_id"],))
    clienti = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]

    # Prendi tutti i template PDF disponibili
    cur.execute("""
        SELECT id, nome, filename FROM template_pdf WHERE cliente_id = %s OR cliente_id IS NULL
    """, (session["user_id"],))
    templates = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]
    
    cur.close()

    return render_template("tools/questionari.html",
        clienti=get_all_clienti(),
        templates=get_all_templates(),
        pdf_url=None,  # ancora nulla generato
        pdf_id=None,    # idem
        current_tool="manage_consulenze",
        current_tool_name="💼 Gestione Consulenze",
        user_tools=session.get("pacchetti", []),
        tool_routes={
            "manage_consulenze": "manage_consulenze.index",
            "manage_drivers": "manage_drivers.index",
        }
    )

@manage_consulenze_bp.route('/upload_template', methods=['POST'])
@has_package("manage_consulenze")
def upload_template():
    nome = request.form.get("nome_template")
    file = request.files.get("file_template")

    if not file or not nome:
        flash("Compila tutti i campi", "danger")
        return redirect(url_for("manage_consulenze.questionari"))

    filename = secure_filename(file.filename)
    path = os.path.join("static", "pdf_templates", filename)
    file.save(path)

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO template_pdf (nome, filename, cliente_id)
        VALUES (%s, %s, %s)
    """, (nome, filename, session["user_id"]))
    conn.commit()
    cur.close()

    flash("✅ Template caricato con successo!", "success")
    return redirect(url_for("manage_consulenze.questionari"))

@manage_consulenze_bp.route('/genera_questionario', methods=['POST'])
@has_package("manage_consulenze")
def genera_questionario():


    cliente_id = request.form.get("cliente_id")
    template_file = request.form.get("template_pdf")

    flags = {
        "flag_1": "✔" if request.form.get("flag_1") else "",
        "flag_2": "✔" if request.form.get("flag_2") else "",
        "flag_3": "✔" if request.form.get("flag_3") else "",
        "flag_4": "✔" if request.form.get("flag_4") else "",
        "flag_5": "✔" if request.form.get("flag_5") else "",
    }

    # Prendi dati cliente
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clienti_assicurativi WHERE id = %s", (cliente_id,))
    cliente = cur.fetchone()
    cur.close()

    if not cliente:
        flash("Cliente non trovato", "danger")
        return redirect(url_for("manage_consulenze.questionari"))

    # Percorsi
    template_path = os.path.join("app", "static", "pdf_templates", template_file)
    output_path = os.path.join("app", "static", "pdf_generati", f"questionario_{cliente_id}.pdf")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    reader = PdfReader(template_path)
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)

    # Acrofield da compilare
    dati = {
        "cognome": safe(cliente[3]),
        "nome": safe(cliente[2]),
        "cf": safe(cliente[6]),
        "sesso": "",  # non presente nell'anagrafica
        "data_nascita": format_date(cliente[4]),
        "luogo_nascita": safe(cliente[5]),
        "prov_nascita": "",  # non presente
        "nazione": "ITALIA",

        "comune_domicilio": safe(cliente[12]),  # domicilio
        "cap_domicilio": "",
        "prov_domicilio": "",
        "indirizzo_domicilio": safe(cliente[11]),  # residenza

        "telefono": "",  # non usato
        "cellulare": safe(cliente[10]),
        "email": safe(cliente[15]),
        "pec": safe(cliente[9]),

        "att_prof": safe(cliente[7]),
        "ambito_prof": "",
        "univoco": safe(cliente[22]),

        # Azienda
        "denominazione": "",
        "piva_azienda": safe(cliente[7]),
        "cita_azienda": "",
        "cap_azienda": "",
        "prov_azienda": "",
        "indirizzo_azienda": safe(cliente[13]),
        "telefono_azienda": "",
        "cellulare_azienda": "",
        "email__azienda": "",
        "pec_azienda": "",
        "attivita_azienda": "",
        "ambito_azienda": "",
        "univoco_azienda": "",

        # Data odierna
        "data": datetime.now().strftime("%d/%m/%Y"),

        # Flag dal form
        **flags
    }

    writer.update_page_form_field_values(writer.pages[0], dati)

    with open(output_path, "wb") as f:
        writer.write(f)

    session["last_questionario_template"] = template_file


    # Mostra anteprima
    pdf_url = f"/static/pdf_generati/questionario_{cliente_id}.pdf"
    return render_template("tools/questionari.html",
        clienti=get_all_clienti(),
        templates=get_all_templates(),
        pdf_url=pdf_url,
        current_tool="manage_consulenze",
        current_tool_name="💼 Gestione Consulenze",
        user_tools=session.get("pacchetti", []),
        tool_routes={
            "manage_consulenze": "manage_consulenze.index",
            "manage_drivers": "manage_drivers.index",
        }
    )

@manage_consulenze_bp.route('/salva_cliente', methods=['POST'])
@has_package("manage_consulenze")
def salva_cliente():
    form = request.form
    files = request.files
    conn = get_db()
    cur = conn.cursor()

    # Salvataggio documenti
    uploads_folder = "static/uploads/documenti"
    os.makedirs(uploads_folder, exist_ok=True)

    def salva_file(file_obj):
        if file_obj and file_obj.filename:
            filename = secure_filename(file_obj.filename)
            path = os.path.join(uploads_folder, filename)
            file_obj.save(path)
            return path
        return None

    doc_fronte = salva_file(files.get('doc_fronte'))
    doc_retro = salva_file(files.get('doc_retro'))
    polizza_precedente = salva_file(files.get('polizza_precedente'))

    # Inserimento dati nel DB
    cur.execute("""
        INSERT INTO clienti_assicurativi (
            cliente_id, nome, cognome, data_nascita, luogo_nascita,
            codice_fiscale, partita_iva, attivita, inizio_attivita,
            data_albo, num_albo, residenza, domicilio, ubicazione,
            email, pec, codice_univoco, cellulare,
            doc_fronte, doc_retro, polizza_precedente,
            fatturato_2024, fatturato_2025,
            dipendenti, addetti, subappaltatori,
            sedi_estere, clienti_estero, fornitori_estero
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        session['user_id'],
        form['nome'],
        form['cognome'],
        parse_date(form['data_nascita']),
        form['luogo_nascita'],
        form['codice_fiscale'],
        form['partita_iva'],
        form['attivita'],
        parse_date(form['inizio_attivita']),
        parse_date(form['data_albo']),
        form['num_albo'],
        form['residenza'],
        form['domicilio'],
        form['ubicazione'],
        form['email'],
        form['pec'],
        form['codice_univoco'],
        form['cellulare'],
        doc_fronte,
        doc_retro,
        polizza_precedente,
        form['fatturato_2024'] or None,
        form['fatturato_2025'] or None,
        form['dipendenti'],
        form['addetti'],
        form['subappaltatori'],
        form.get('sedi_estere', 'No'),
        form.get('clienti_estero', 'No'),
        form.get('fornitori_estero', 'No')
    ))

    conn.commit()
    cur.close()

    flash("✅ Cliente salvato correttamente!")
    return redirect(url_for("manage_consulenze.index"))

@manage_consulenze_bp.route('/panoramica', methods=['GET'])
@has_package("manage_consulenze")
def panoramica():
    conn = get_db()
    cur = conn.cursor()

    campo = request.args.get("campo")
    valore = request.args.get("valore")

    base_query = """
        SELECT id, nome, cognome, data_nascita, luogo_nascita, codice_fiscale,
               partita_iva, attivita, email, pec, cellulare, residenza,
               domicilio, ubicazione, inizio_attivita, data_albo, num_albo,
               fatturato_2024, fatturato_2025, dipendenti, addetti,
               subappaltatori, codice_univoco, questionario_inviato, nome_questionario_inviato
        FROM clienti_assicurativi
        WHERE cliente_id = %s
    """
    params = [session["user_id"]]

    questionario_inviato = request.args.get("questionario_inviato")

    if questionario_inviato in ("0", "1"):
        base_query += " AND questionario_inviato = %s"
        params.append(bool(int(questionario_inviato)))

    if campo and valore:
        if campo in ['fatturato_2024', 'fatturato_2025']:
            base_query += f" AND {campo}::text ILIKE %s"
        else:
            base_query += f" AND {campo} ILIKE %s"
        params.append(f"%{valore}%")

    base_query += " ORDER BY cognome, nome"

    cur.execute(base_query, tuple(params))
    clienti = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]
    cur.close()

    return render_template("tools/manage_panoramica.html",
        clienti=clienti,
        current_tool="manage_consulenze",
        current_tool_name="💼 Gestione Consulenze",
        user_tools=session.get("pacchetti", []),
        tool_routes={
            "manage_consulenze": "manage_consulenze.index",
            "manage_drivers": "manage_drivers.index",
        }
    )

@manage_consulenze_bp.route('/modifica_campo', methods=['POST'])
@has_package("manage_consulenze")
def modifica_campo():
    data = request.get_json()
    id_cliente = data.get("id")
    campo = data.get("campo")
    valore = data.get("valore")

    if campo not in ["nome", "cognome", "data_nascita", "email", "pec", "cellulare", "attivita", "codice_fiscale", "partita_iva"]:
        return jsonify({"success": False, "message": "Campo non modificabile"})

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(f"UPDATE clienti_assicurativi SET {campo} = %s WHERE id = %s AND cliente_id = %s",
                    (valore, id_cliente, session["user_id"]))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        cur.close()

@manage_consulenze_bp.route('/elimina_cliente/<int:id>', methods=['POST'])
@has_package("manage_consulenze")
def elimina_cliente(id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM clienti_assicurativi WHERE id = %s AND cliente_id = %s", (id, session["user_id"]))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        cur.close()

@manage_consulenze_bp.route('/gestione_email', methods=['GET', 'POST'])
@has_package("manage_consulenze")
def gestione_email():
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        smtp_server = request.form.get("smtp_server")
        smtp_port = request.form.get("smtp_port")
        email_mittente = request.form.get("email_mittente")
        password_mittente = request.form.get("password_mittente")
        testo = request.form.get("testo_predefinito")

        # Controlla se esiste già la config per il cliente
        cur.execute("SELECT id FROM config_email WHERE cliente_id = %s", (session["user_id"],))
        esiste = cur.fetchone()

        if esiste:
            cur.execute("""
                UPDATE config_email
                SET smtp_server=%s, smtp_port=%s, email_mittente=%s, password_mittente=%s, testo_predefinito=%s
                WHERE cliente_id=%s
            """, (smtp_server, smtp_port, email_mittente, password_mittente, testo, session["user_id"]))
        else:
            cur.execute("""
                INSERT INTO config_email (cliente_id, smtp_server, smtp_port, email_mittente, password_mittente, testo_predefinito)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (session["user_id"], smtp_server, smtp_port, email_mittente, password_mittente, testo))

        conn.commit()
        flash("✅ Configurazione email salvata con successo", "success")

    # Carica valori esistenti
    cur.execute("SELECT * FROM config_email WHERE cliente_id = %s", (session["user_id"],))
    config = cur.fetchone()
    cur.close()

    return render_template("tools/config_email.html",
        config=config,
        current_tool="manage_consulenze",
        current_tool_name="💼 Gestione Consulenze",
        user_tools=session.get("pacchetti", []),
        tool_routes={
            "manage_consulenze": "manage_consulenze.index",
            "manage_drivers": "manage_drivers.index",
        }
    )

@manage_consulenze_bp.route('/invia_questionario/<int:cliente_id>', methods=['POST'])
@has_package("manage_consulenze")
def invia_questionario(cliente_id):

    template_file = session.get("last_questionario_template")


    conn = get_db()
    cur = conn.cursor()

    # Carica configurazione SMTP personalizzata
    cur.execute("SELECT smtp_server, smtp_port, email_mittente, password_mittente, testo_predefinito FROM config_email WHERE cliente_id = %s", (session["user_id"],))
    config = cur.fetchone()

    if not config:
        flash("⚠️ Nessuna configurazione email trovata", "danger")
        return redirect(url_for("manage_consulenze.questionari"))

    smtp_server, smtp_port, email_mittente, password_mittente, testo = config

    # Prendi info del destinatario (cliente assicurativo)
    cur.execute("SELECT email, nome, cognome FROM clienti_assicurativi WHERE id = %s AND cliente_id = %s", (cliente_id, session["user_id"]))
    cliente = cur.fetchone()
    if not cliente:
        flash("Cliente non trovato", "danger")
        return redirect(url_for("manage_consulenze.questionari"))

    email_destinatario, nome, cognome = cliente

    # Percorso al PDF
    filename = f"questionario_{cliente_id}.pdf"
    filepath = os.path.join("app", "static", "pdf_generati", filename)

    if not os.path.exists(filepath):
        flash("❌ PDF non generato, impossibile inviare", "danger")
        return redirect(url_for("manage_consulenze.questionari"))

    try:
        # Prepara l’email
        msg = EmailMessage()
        msg["Subject"] = f"📄 Questionario Assicurativo - {nome} {cognome}"
        msg["From"] = email_mittente
        msg["To"] = email_destinatario
        msg.set_content(testo or "In allegato trova il questionario assicurativo.")

        with open(filepath, "rb") as f:
            msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=filename)

        # Invia tramite SMTP
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(email_mittente, password_mittente)
            server.send_message(msg)

        # Dopo aver inviato correttamente l'email
        cur = conn.cursor()
        cur.execute("""
            UPDATE clienti_assicurativi
            SET questionario_inviato = TRUE,
                nome_questionario_inviato = %s
            WHERE id = %s
        """, (template_file, cliente_id))
        conn.commit()
        cur.close()



        # Aggiorna DB (puoi aggiungere colonna "questionario_inviato" se vuoi)
        flash("✅ Questionario inviato correttamente", "success")

    except Exception as e:
        print("Errore invio email:", e)  # AGGIUNGI QUESTO
        flash(f"❌ Errore durante l'invio: {str(e)}", "danger")


    cur.close()
    return redirect(url_for("manage_consulenze.questionari"))



