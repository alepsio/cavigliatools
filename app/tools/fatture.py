# app/tools/fatture.py
from flask import Blueprint, render_template

fatture_bp = Blueprint('fatture', __name__, url_prefix='/fatture')

@fatture_bp.route('/')
def index():
    return "<h2>Tool Fatture (in costruzione)</h2>"
