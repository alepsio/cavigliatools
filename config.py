# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'caviglia_secret')
    DB_NAME = 'cavigliatools'
    DB_USER = 'postgres'
    DB_PASSWORD = 'postgres'
    DB_HOST = 'localhost'
    DB_PORT = '5432'
