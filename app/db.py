import psycopg2
from flask import g
from config import Config
import json

def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT
        )
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_user_by_username(username):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password, ruolo, pacchetti FROM utenti WHERE username = %s", (username,))
    result = cur.fetchone()
    cur.close()
    return result

def create_user(username, password, ruolo, pacchetti):
    conn = get_db()
    cur = conn.cursor()
    json_pacchetti = json.dumps(pacchetti) 
    cur.execute("INSERT INTO utenti (username, password, ruolo, pacchetti) VALUES (%s, %s, %s, %s)",
                (username, password, ruolo, json_pacchetti))
    conn.commit()
    cur.close()

