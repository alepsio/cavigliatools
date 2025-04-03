from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.db import get_db
from app.routes.decorators import has_package

manage_autisti_bp = Blueprint('manage_autisti', __name__, url_prefix='/manage_autisti')

@manage_autisti_bp.route("/", methods=["GET", "POST"])
@has_package("manage_drivers")
def index():
    conn = get_db()
    cur = conn.cursor()

    # Inserimento nuovo autista
    if request.method == "POST":
        nome = request.form.get("nome")
        targa = request.form.get("targa")
        autista_id = request.form.get("autista_id")

        if autista_id:  # Modifica
            cur.execute("UPDATE autisti SET nome = %s, targa = %s WHERE id = %s", (nome, targa, autista_id))
            flash("Autista aggiornato con successo", "success")
        else:  # Nuovo
            cur.execute("INSERT INTO autisti (nome, targa, cliente_id) VALUES (%s, %s, %s)", (nome, targa, session["user_id"]))
            flash("Autista inserito correttamente", "success")
        conn.commit()
        return redirect(url_for("manage_autisti.index"))

    # Recupero lista autisti
    cur.execute("SELECT id, nome, targa FROM autisti WHERE cliente_id = %s ORDER BY nome", (session["user_id"],))
    rows = cur.fetchall()
    autisti = [{'id': r[0], 'nome': r[1], 'targa': r[2]} for r in rows]

    # Se siamo in modifica
    id_da_modificare = request.args.get("modifica")
    autista_modifica = None
    if id_da_modificare:
        cur.execute("SELECT id, nome, targa FROM autisti WHERE id = %s AND cliente_id = %s", (id_da_modificare, session["user_id"]))
        r = cur.fetchone()
        if r:
            autista_modifica = {'id': r[0], 'nome': r[1], 'targa': r[2]}

    cur.close()
    return render_template(
        "tools/manage_autisti.html",
        autisti=autisti,
        autista_modifica=autista_modifica,
        current_tool="manage_autisti",
        current_tool_name="🧑‍✈️ Anagrafica Autisti",
        user_tools=session.get("pacchetti", []),
        tool_routes={
            "manage_drivers": "manage_drivers.index",
            "manage_autisti": "manage_autisti.index"
        }
    )
