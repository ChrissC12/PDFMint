import os
import shutil
from flask import Flask
from app import app, home, merge_tool, split_tool, rotate_tool, compress_tool, image_to_pdf_tool, pdf_to_image_tool, protect_tool, unlock_tool

# Define the output directory
OUTPUT_FOLDER = 'docs'

# Create or clean the output directory
if os.path.exists(OUTPUT_FOLDER):
    shutil.rmtree(OUTPUT_FOLDER)
os.makedirs(OUTPUT_FOLDER)

print(f"Created clean output folder: {OUTPUT_FOLDER}")

# A dictionary mapping your view functions to the output HTML filename
PAGES = {
    'home': 'index.html',  # The homepage should be index.html
    'merge_tool': 'merge.html',
    'split_tool': 'split.html',
    'rotate_tool': 'rotate.html',
    'compress_tool': 'compress.html',
    'image_to_pdf_tool': 'image_to_pdf.html',
    'pdf_to_image_tool': 'pdf_to_image.html',
    'protect_tool': 'protect.html',
    'unlock_tool': 'unlock.html',
}

def build_static_files():
    """
    Renders the Flask templates into static HTML files.
    """
    with app.test_request_context():
        # Loop through our page definitions
        for endpoint, output_filename in PAGES.items():
            try:
                # Get the URL for the endpoint (e.g., url_for('merge_tool'))
                url = app.url_map.iter_rules(endpoint=endpoint).__next__().rule
                
                # Use the test client to get the rendered HTML content
                response = app.test_client().get(url)
                
                if response.status_code == 200:
                    # Write the content to the corresponding file in the docs folder
                    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                    with open(output_path, 'wb') as f:
                        f.write(response.data)
                    print(f"Successfully built: {output_filename}")
                else:
                    print(f"ERROR: Failed to build {output_filename}. Status code: {response.status_code}")

            except Exception as e:
                print(f"ERROR: Could not build page for endpoint '{endpoint}'. Reason: {e}")

if __name__ == '__main__':
    print("Starting static site build...")
    build_static_files()
    print("Build complete!")