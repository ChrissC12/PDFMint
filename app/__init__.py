# app/__init__.py

import os
from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app) # Enable CORS for the entire application

    # --- Configuration ---
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'uploads')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['SECRET_KEY'] = 'a-super-secret-key-that-you-will-change'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # --- Register Routes ---
    with app.app_context():
        from . import routes

    return app