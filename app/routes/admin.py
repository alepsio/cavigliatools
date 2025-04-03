# app/routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import create_user
from app.routes.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@admin_bp.route('/create_user', methods=['GET', 'POST'])
@admin_required
def create_new_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        ruolo = request.form['ruolo']
        pacchetti = request.form.getlist('pacchetti')  # checkbox multipli
        create_user(username, password, ruolo, pacchetti)
        flash("Utente creato con successo!")
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('create_user.html')
