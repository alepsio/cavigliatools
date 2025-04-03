from flask import Blueprint, render_template, session, redirect, url_for
from app.db import get_db
from psycopg2.extras import RealDictCursor
import json


dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, pacchetti FROM utenti WHERE id = %s", (session['user_id'],))
    result = cur.fetchone()
    cur.close()

    if result is None:
        return redirect(url_for('auth.login'))

    username, pacchetti_raw = result

    # 🔍 Controlla tipo e forza conversione se serve
    if isinstance(pacchetti_raw, str):
        try:
            pacchetti = json.loads(pacchetti_raw)
        except json.JSONDecodeError:
            pacchetti = []
    elif isinstance(pacchetti_raw, list):
        pacchetti = pacchetti_raw
    else:
        pacchetti = []


    return render_template('dashboard.html', username=username, pacchetti=pacchetti)
