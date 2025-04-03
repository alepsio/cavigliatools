# app/tools/gestione_magazzino
from flask import Blueprint, render_template

gestione_magazzino_bp = Blueprint('gestione_magazzino', __name__, url_prefix='/gestione_magazzino')

@gestione_magazzino_bp.route('/')
def index():
    return "<h2>Tool gestione magazzino (in costruzione)</h2>"
