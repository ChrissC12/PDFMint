# --- FINAL DEPLOYABLE app.py with JSON Endpoints ---

from flask_cors import CORS
import os
import uuid
import zipfile
import subprocess
import shutil
from flask import Flask, request, render_template, send_from_directory, url_for, jsonify
from pypdf import PdfWriter, PdfReader
from PIL import Image
from pdf2image import convert_from_path

# --- Basic Setup ---
app = Flask(__name__)
CORS(app)
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

@app.route('/')
def home():
    return render_template('home.html')

# NEW: Dedicated route for downloading files
@app.route('/download/<filename>')
def download_file(filename):
    if ".." in filename or filename.startswith("/"):
        return jsonify({'success': False, 'message': 'Invalid filename.', 'category': 'danger'}), 400
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/merge', methods=['GET', 'POST'])
def merge_tool():
    if request.method == 'POST':
        try:
            if 'pdf_files' not in request.files:
                raise ValueError('No file part in the request.')
            files = request.files.getlist('pdf_files')
            if len(files) < 2:
                raise ValueError('Please select at least two PDF files to merge.')

            merger = PdfWriter()
            for file in files:
                if file and file.filename.lower().endswith('.pdf'):
                    merger.append(file)
                else:
                    raise ValueError(f"Invalid file type: '{file.filename}'.")

            output_filename = f"merged_{uuid.uuid4().hex}.pdf"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            merger.write(output_path)
            merger.close()
            
            return jsonify({
                'success': True, 'message': 'PDFs successfully merged!', 'category': 'success',
                'download_url': url_for('download_file', filename=output_filename)
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e), 'category': 'danger'})
    return render_template('index.html')

@app.route('/split', methods=['GET', 'POST'])
def split_tool():
    if request.method == 'POST':
        output_dir = None
        try:
            if 'pdf_file' not in request.files: raise ValueError('No file part in the request.')
            file = request.files['pdf_file']
            if not file or file.filename == '': raise ValueError('No file selected.')
            
            split_mode = request.form.get('split_mode')

            if not file.filename.lower().endswith('.pdf'):
                raise ValueError('Invalid file type. Please upload a PDF.')

            reader = PdfReader(file)
            max_pages = len(reader.pages)

            # --- MODE 1: Custom Range to a SINGLE PDF ---
            if split_mode == 'custom':
                ranges = request.form.get('ranges')
                if not ranges: raise ValueError('Please specify pages or ranges to extract.')
                
                pages_to_extract = parse_page_ranges(ranges, max_pages)
                if not pages_to_extract: raise ValueError("No valid pages were selected.")
                
                writer = PdfWriter()
                for page_index in pages_to_extract:
                    writer.add_page(reader.pages[page_index])

                output_filename = f"extracted_pages_{uuid.uuid4().hex}.pdf"
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
                with open(output_path, "wb") as fp:
                    writer.write(fp)
                
                return jsonify({
                    'success': True, 'message': f'Successfully extracted {len(pages_to_extract)} pages!', 'category': 'success',
                    'download_url': url_for('download_file', filename=output_filename)
                })

            # --- MODE 2: All Pages to a ZIP File ---
            elif split_mode == 'all':
                job_id = uuid.uuid4().hex
                output_dir = os.path.join(app.config['UPLOAD_FOLDER'], job_id)
                os.makedirs(output_dir)

                for i, page in enumerate(reader.pages):
                    writer = PdfWriter()
                    writer.add_page(page)
                    page_filename = f'page_{i + 1}.pdf'
                    with open(os.path.join(output_dir, page_filename), 'wb') as output_stream:
                        writer.write(output_stream)

                zip_filename = f'split_pages_{job_id}.zip'
                zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for f in os.listdir(output_dir):
                        zipf.write(os.path.join(output_dir, f), arcname=f)
                
                return jsonify({
                    'success': True, 'message': f'Successfully split into {max_pages} separate files!', 'category': 'success',
                    'download_url': url_for('download_file', filename=zip_filename)
                })
            
            else:
                raise ValueError("Invalid split mode selected.")

        except Exception as e:
            return jsonify({'success': False, 'message': str(e), 'category': 'danger'})
        
        finally:
            if output_dir and os.path.exists(output_dir):
                shutil.rmtree(output_dir)

    return render_template('split.html')




@app.route('/rotate', methods=['GET', 'POST'])
def rotate_tool():
    if request.method == 'POST':
        try:
            if 'pdf_file' not in request.files: raise ValueError('No file part.')
            file, rotation = request.files['pdf_file'], int(request.form.get('rotation', 90))
            if file.filename == '': raise ValueError('No file selected.')
            if file.filename.lower().endswith('.pdf'):
                reader = PdfReader(file)
                writer = PdfWriter()
                for page in reader.pages: page.rotate(rotation); writer.add_page(page)
                output_filename = f"rotated_{uuid.uuid4().hex}.pdf"
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
                with open(output_path, "wb") as fp: writer.write(fp)
                return jsonify({'success': True, 'message': f'PDF successfully rotated by {rotation} degrees!', 'category': 'success', 'download_url': url_for('download_file', filename=output_filename)})
            else: raise ValueError('Invalid file type.')
        except Exception as e:
            return jsonify({'success': False, 'message': str(e), 'category': 'danger'})
    return render_template('rotate.html')

@app.route('/compress', methods=['GET', 'POST'])
def compress_tool():
    if request.method == 'POST':
        input_path = None
        try:
            if 'pdf_file' not in request.files: raise ValueError('No file part.')
            file = request.files['pdf_file']
            if file.filename == '': raise ValueError('No file selected.')
            if file.filename.lower().endswith('.pdf'):
                input_filename = f"input_{uuid.uuid4().hex}.pdf"
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
                file.save(input_path)
                output_filename = f"compressed_{uuid.uuid4().hex}.pdf"
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
                gs_command = 'gswin64c' if os.name == 'nt' else 'gs'
                command = [gs_command, '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4', '-dPDFSETTINGS=/ebook', '-dNOPAUSE', '-dQUIET', '-dBATCH', f'-sOutputFile={output_path}', input_path]
                subprocess.run(command, check=True, timeout=60)
                original_size = os.path.getsize(input_path) / 1024
                compressed_size = os.path.getsize(output_path) / 1024
                reduction = 100 - (compressed_size / original_size * 100) if original_size > 0 else 0
                message = f"Success! Reduced from {original_size:.1f} KB to {compressed_size:.1f} KB ({reduction:.1f}% reduction)."
                return jsonify({'success': True, 'message': message, 'category': 'success', 'download_url': url_for('download_file', filename=output_filename)})
            else: raise ValueError('Invalid file type.')
        except Exception as e:
            return jsonify({'success': False, 'message': str(e), 'category': 'danger'})
        finally:
            if input_path and os.path.exists(input_path): os.remove(input_path)
    return render_template('compress.html')

@app.route('/image-to-pdf', methods=['GET', 'POST'])
def image_to_pdf_tool():
    if request.method == 'POST':
        try:
            if 'image_files' not in request.files: raise ValueError('No file part.')
            files = request.files.getlist('image_files')
            if not files or files[0].filename == '': raise ValueError('No files selected.')
            image_list, first_image, allowed = [], None, {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
            for file in files:
                if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed:
                    img = Image.open(file.stream).convert("RGB")
                    if not first_image: first_image = img
                    else: image_list.append(img)
                else: raise ValueError(f"Invalid file type: '{file.filename}'.")
            if not first_image: raise ValueError("No valid images uploaded.")
            output_filename = f"converted_{uuid.uuid4().hex}.pdf"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            first_image.save(output_path, "PDF", resolution=100.0, save_all=True, append_images=image_list)
            return jsonify({'success': True, 'message': 'Images successfully converted to PDF!', 'category': 'success', 'download_url': url_for('download_file', filename=output_filename)})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e), 'category': 'danger'})
    return render_template('image_to_pdf.html')

@app.route('/pdf-to-image', methods=['GET', 'POST'])
def pdf_to_image_tool():
    if request.method == 'POST':
        input_path, output_dir = None, None
        try:
            if 'pdf_file' not in request.files: raise ValueError('No file part.')
            file, image_format = request.files['pdf_file'], request.form.get('format', 'jpeg')
            if file.filename == '': raise ValueError('No file selected.')
            if file.filename.lower().endswith('.pdf'):
                job_id = uuid.uuid4().hex
                input_filename = f"input_{job_id}.pdf"
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
                file.save(input_path)
                output_dir = os.path.join(app.config['UPLOAD_FOLDER'], job_id)
                os.makedirs(output_dir)
                images = convert_from_path(input_path)
                for i, image in enumerate(images): image.save(os.path.join(output_dir, f'page_{i + 1}.{image_format}'), image_format.upper())
                zip_filename = f'converted_images_{job_id}.zip'
                zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for root, _, files_in_dir in os.walk(output_dir):
                        for f in files_in_dir: zipf.write(os.path.join(root, f), arcname=f)
                message = f'Successfully converted {len(images)} pages to {image_format.upper()}!'
                return jsonify({'success': True, 'message': message, 'category': 'success', 'download_url': url_for('download_file', filename=zip_filename)})
            else: raise ValueError('Invalid file type.')
        except Exception as e:
            return jsonify({'success': False, 'message': f"An error occurred. Ensure poppler is installed and in your PATH. Details: {e}", 'category': 'danger'})
        finally:
            if input_path: os.remove(input_path)
            if output_dir: shutil.rmtree(output_dir)
    return render_template('pdf_to_image.html')

@app.route('/protect', methods=['GET', 'POST'])
def protect_tool():
    if request.method == 'POST':
        try:
            if 'pdf_file' not in request.files: raise ValueError('No file part.')
            file, password = request.files['pdf_file'], request.form.get('password')
            if file.filename == '': raise ValueError('No file selected.')
            if not password: raise ValueError('Password is required.')
            if file.filename.lower().endswith('.pdf'):
                reader = PdfReader(file)
                if reader.is_encrypted: raise ValueError('This PDF is already protected.')
                writer = PdfWriter()
                for page in reader.pages: writer.add_page(page)
                writer.encrypt(password.encode('utf-8'))
                output_filename = f"protected_{uuid.uuid4().hex}.pdf"
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
                with open(output_path, "wb") as fp: writer.write(fp)
                return jsonify({'success': True, 'message': 'Your PDF is now password protected!', 'category': 'success', 'download_url': url_for('download_file', filename=output_filename)})
            else: raise ValueError('Invalid file type.')
        except Exception as e:
            return jsonify({'success': False, 'message': str(e), 'category': 'danger'})
    return render_template('protect.html')

@app.route('/unlock', methods=['GET', 'POST'])
def unlock_tool():
    if request.method == 'POST':
        try:
            if 'pdf_file' not in request.files: raise ValueError('No file part.')
            file, password = request.files['pdf_file'], request.form.get('password')
            if file.filename == '': raise ValueError('No file selected.')
            if not password: raise ValueError('Password is required.')
            if file.filename.lower().endswith('.pdf'):
                reader = PdfReader(file)
                if not reader.is_encrypted: raise ValueError('This PDF is not password protected.')
                if reader.decrypt(password.encode('utf-8')):
                    writer = PdfWriter()
                    for page in reader.pages: writer.add_page(page)
                    output_filename = f"unlocked_{uuid.uuid4().hex}.pdf"
                    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
                    with open(output_path, "wb") as fp: writer.write(fp)
                    return jsonify({'success': True, 'message': 'Your PDF has been successfully unlocked!', 'category': 'success', 'download_url': url_for('download_file', filename=output_filename)})
                else: raise ValueError('Incorrect password.')
            else: raise ValueError('Invalid file type.')
        except Exception as e:
            return jsonify({'success': False, 'message': str(e), 'category': 'danger'})
    return render_template('unlock.html')

# --- Main Execution ---
#if __name__ == '__main__':
 #   app.run(host='0.0.0.0', port=5001, debug=True)