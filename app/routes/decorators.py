from flask import session, redirect, url_for, abort
from app.db import get_db

def admin_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT ruolo FROM utenti WHERE id = %s", (session['user_id'],))
        ruolo = cur.fetchone()[0]
        cur.close()

        if ruolo != 'admin':
            return abort(403)
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def has_package(package_name):
    def decorator(f):
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))

            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT pacchetti FROM utenti WHERE id = %s", (session['user_id'],))
            result = cur.fetchone()
            cur.close()
            if result is None:
                return abort(403)

            pacchetti = result[0]
            if package_name not in pacchetti:
                return abort(403)
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator
