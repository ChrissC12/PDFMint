# --- FINAL DEPLOYABLE app.py ---

import os
import uuid
import zipfile
import subprocess
import shutil
from flask import Flask, request, render_template, send_from_directory, url_for, jsonify
from flask_cors import CORS
from pypdf import PdfWriter, PdfReader
from PIL import Image
from pdf2image import convert_from_path

# --- Basic Setup ---
app = Flask(__name__)
CORS(app) # Enable CORS for the entire application
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'a-much-better-secret-key-is-needed-for-production'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# --- Helper Function for Splitting ---
def parse_page_ranges(range_string, max_pages):
    pages_to_extract = set()
    parts = range_string.replace(" ", "").split(',')
    for part in parts:
        if not part: continue
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if start > end or start < 1 or end > max_pages: raise ValueError
                pages_to_extract.update(range(start - 1, end))
            except (ValueError, TypeError): raise ValueError(f"Invalid range '{part}'.")
        else:
            try:
                page_num = int(part)
                if page_num < 1 or page_num > max_pages: raise ValueError
                pages_to_extract.add(page_num - 1)
            except (ValueError, TypeError): raise ValueError(f"Invalid page number '{part}'.")
    return sorted(list(pages_to_extract))

# --- Route Definitions ---






# run.py

from app import create_app

app = create_app()

#if __name__ == '__main__':
    # Use host='0.0.0.0' to be accessible on your network
 #   app.run(host='0.0.0.0', port=5001, debug=True)