from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session
from app.db import get_db
from app.routes.decorators import has_package
import openpyxl
from io import BytesIO
from xhtml2pdf import pisa

manage_drivers_bp = Blueprint('manage_drivers', __name__, url_prefix='/manage_drivers')

@manage_drivers_bp.route('/', methods=['GET', 'POST'])
@has_package("manage_drivers")
def index():
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST' and 'export_excel' not in request.form and 'export_pdf' not in request.form:
        # inserimento dati
        data = request.form['data']
        nome_autista = request.form['nome_autista']
        targa = request.form['targa']
        zona = request.form['zona']
        qt_materiale = request.form['qt_materiale']
        lt_gasolio = request.form['lt_gasolio']
        km_effettuati = request.form['km_effettuati']

        cur.execute("""
            INSERT INTO dati_autisti (data, nome_autista, targa, zona, qt_materiale, lt_gasolio, km_effettuati)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (data, nome_autista, targa, zona, qt_materiale, lt_gasolio, km_effettuati))
        conn.commit()
        flash("Dati inseriti correttamente!")

    cur.execute("SELECT * FROM dati_autisti ORDER BY data DESC")
    records = cur.fetchall()

    cur.execute("SELECT nome, targa FROM autisti")
    autisti = cur.fetchall()  # list of tuples
    autisti_dict = {nome: targa for nome, targa in autisti}


    cur.close()

    return render_template(
        'tools/manage_drivers.html',
        records=records,
        current_tool="manage_drivers",
        current_tool_name="🚚 Gestione Autisti",
        user_tools=session.get("pacchetti", []),
        autisti=list(autisti_dict.keys()),
        autisti_targhe=autisti_dict,
        tool_routes={
            "manage_drivers": "manage_drivers.index",
            "fatture": "fatture.index" 
        }
    )


@manage_drivers_bp.route('/export_excel')
@has_package("manage_drivers")
def export_excel():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT data, nome_autista, targa, zona, qt_materiale, lt_gasolio, km_effettuati FROM dati_autisti ORDER BY data DESC")
    rows = cur.fetchall()
    cur.close()

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Dati Autisti"

    headers = ["Data", "Autista", "Targa", "Zona", "Qt. Materiale", "Lt Gasolio", "Km"]
    sheet.append(headers)

    for row in rows:
        sheet.append(row)

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return send_file(output, download_name="dati_autisti.xlsx", as_attachment=True)

@manage_drivers_bp.route('/export_pdf')
@has_package("manage_drivers")
def export_pdf():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT data, nome_autista, targa, zona, qt_materiale, lt_gasolio, km_effettuati FROM dati_autisti ORDER BY data DESC")
    records = cur.fetchall()
    cur.close()

    html = render_template('tools/pdf_template.html', records=records)
    pdf_output = BytesIO()
    pisa.CreatePDF(html, dest=pdf_output)
    pdf_output.seek(0)

    return send_file(pdf_output, download_name="dati_autisti.pdf", as_attachment=True)

@manage_drivers_bp.route('/report', methods=['GET'])
@has_package("manage_drivers")
def report():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT nome_autista FROM dati_autisti")
    autisti = [row[0] for row in cur.fetchall()]

    filtro_autista = request.args.get('autista')
    filtro_zona = request.args.get('zona')

    query = "SELECT * FROM dati_autisti"
    params = []
    conditions = []

    if filtro_autista:
        conditions.append("nome_autista = %s")
        params.append(filtro_autista)

    if filtro_zona:
        conditions.append("zona = %s")
        params.append(filtro_zona)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cur.execute(query, tuple(params))
    dati = cur.fetchall()

    cur.execute("""
        SELECT nome_autista,
               COUNT(*) AS giorni,
               SUM(qt_materiale) AS totale_materiale,
               SUM(km_effettuati) AS totale_km,
               SUM(lt_gasolio) AS totale_gasolio,
               ROUND(SUM(qt_materiale)/NULLIF(SUM(km_effettuati),0), 2) AS eff_materiale_per_km,
               ROUND(SUM(km_effettuati)/NULLIF(SUM(lt_gasolio),0), 2) AS eff_km_per_litro
        FROM dati_autisti
        GROUP BY nome_autista
        ORDER BY totale_materiale DESC
    """)
    stats = cur.fetchall()
    cur.close()

    return render_template("tools/manage_report.html",
        autisti=autisti,
        dati=dati,
        stats=stats,
        current_tool="manage_drivers",
        current_tool_name="🚚 Gestione Autisti",
        user_tools=session.get("pacchetti", []),
        tool_routes={
            "manage_drivers": "manage_drivers.index",
            "fatture": "fatture.index"
        }
    )

@manage_drivers_bp.route('/statistiche', methods=['GET', 'POST'])
@has_package("manage_drivers")
def statistiche():
    conn = get_db()
    cur = conn.cursor()

    filtro_mese = request.args.get("mese")
    filtro_tipo = request.args.get("tipo", "qt_materiale")  # può essere anche 'lt_gasolio', 'km_effettuati'

    # Lista mesi per filtro dropdown
    mesi = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]

    # QUERY mese selezionato
    stats_mese = []
    if filtro_mese:
        cur.execute(f"""
            SELECT nome_autista,
                   SUM(qt_materiale),
                   SUM(km_effettuati),
                   SUM(lt_gasolio)
            FROM dati_autisti
            WHERE DATE_PART('month', data::date) = %s
              AND DATE_PART('year', data::date) = DATE_PART('year', CURRENT_DATE)
            GROUP BY nome_autista
            ORDER BY SUM({filtro_tipo}) DESC
        """, (int(filtro_mese),))
        stats_mese = cur.fetchall()

    # Query annuale pivotata
    cur.execute(f"""
        SELECT nome_autista,
               DATE_PART('month', data::date) AS mese,
               SUM({filtro_tipo}) AS valore
        FROM dati_autisti
        WHERE DATE_PART('year', data::date) = DATE_PART('year', CURRENT_DATE)
        GROUP BY nome_autista, mese
    """)
    rows = cur.fetchall()

    # Trasforma in dict pivotato: { autista: [val_mese1, val_mese2, ...] }
    from collections import defaultdict
    autisti = defaultdict(lambda: [0]*12)
    for nome, mese, valore in rows:
        autisti[nome][int(mese)-1] = round(valore, 2)

    cur.close()
    return render_template("tools/manage_stats.html",
        stats_mese=stats_mese,
        stats_annuali=autisti,
        mesi=mesi,
        filtro_mese=filtro_mese,
        filtro_tipo=filtro_tipo,
        current_tool="manage_drivers",
        current_tool_name="🚚 Gestione Autisti",
        user_tools=session.get("pacchetti", []),
        tool_routes={
            "manage_drivers": "manage_drivers.index",
            "fatture": "fatture.index"
        }
    )

@manage_drivers_bp.route('/grafici')
@has_package("manage_drivers")
def grafici():
    conn = get_db()
    cur = conn.cursor()

    filtro_tipo = request.args.get("tipo", "qt_materiale")
    tipi_disponibili = {
        "qt_materiale": "Materiale Trasportato (Kg)",
        "km_effettuati": "Km Effettuati",
        "lt_gasolio": "Gasolio Consumato (Lt)"
    }

    # Dati annuali per linea
    cur.execute(f"""
        SELECT nome_autista,
               DATE_PART('month', data::date) AS mese,
               SUM({filtro_tipo})
        FROM dati_autisti
        WHERE DATE_PART('year', data::date) = DATE_PART('year', CURRENT_DATE)
        GROUP BY nome_autista, mese
        ORDER BY nome_autista, mese
    """)
    annuali = cur.fetchall()

    # Dati mensili per barre
    cur.execute(f"""
        SELECT nome_autista, SUM({filtro_tipo})
        FROM dati_autisti
        WHERE DATE_PART('month', data::date) = DATE_PART('month', CURRENT_DATE)
          AND DATE_PART('year', data::date) = DATE_PART('year', CURRENT_DATE)
        GROUP BY nome_autista
        ORDER BY SUM({filtro_tipo}) DESC
    """)
    mensili = cur.fetchall()

    cur.close()
    return render_template("tools/manage_charts.html",
        annuali=annuali,
        mensili=mensili,
        tipo=filtro_tipo,
        tipo_label=tipi_disponibili[filtro_tipo],
        tipi_disponibili=tipi_disponibili,
        current_tool="manage_drivers",
        current_tool_name="🚚 Gestione Autisti",
        user_tools=session.get("pacchetti", []),
        tool_routes={
            "manage_drivers": "manage_drivers.index",
            "fatture": "fatture.index"
        }
    )
