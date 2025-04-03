# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'caviglia_secret')
    DB_NAME = 'cavigliatools'
    DB_USER = 'cavigliatools_user'
    DB_PASSWORD = 'f3acV3vj9oydrXAtQXRknJmshArSIA9W'
    DB_HOST = 'dpg-cvngo8qdbo4c73a1m93g-a.frankfurt-postgres.render.com'
    DB_PORT = '5432'
