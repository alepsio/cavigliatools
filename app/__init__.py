from flask import Flask
from config import Config
from .db import get_db, close_db
from .routes.auth import auth_bp
from .routes.admin import admin_bp
from .routes.dashboard import dashboard_bp
from .tools.manage_drivers import manage_drivers_bp
from .tools.fatture import fatture_bp
from datetime import timedelta
from .tools.manage_autisti import manage_autisti_bp
from .tools.gestione_magazzino import gestione_magazzino_bp
from app.tools.manage_consulenze import manage_consulenze_bp




def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.teardown_appcontext(close_db)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(manage_drivers_bp)
    app.register_blueprint(fatture_bp)
    app.permanent_session_lifetime = timedelta(days=7)
    app.register_blueprint(manage_autisti_bp)
    app.register_blueprint(gestione_magazzino_bp)
    app.register_blueprint(manage_consulenze_bp)



    return app
