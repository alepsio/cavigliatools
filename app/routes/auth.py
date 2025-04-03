# app/routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.db import get_db
import json
from datetime import timedelta  # opzionale per durata sessione

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password, ruolo, pacchetti FROM utenti WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session.permanent = True  # opzionale
            session['user_id'] = user[0]
            session["username"] = user[1]
            try:
                session["pacchetti"] = user[4] if isinstance(user[4], list) else json.loads(user[4])
            except Exception:
                session["pacchetti"] = []

            return redirect(url_for('dashboard.dashboard'))
        else:
            return render_template('login.html', error="Credenziali non valide")

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Logout effettuato con successo.")
    return redirect(url_for('auth.login'))

