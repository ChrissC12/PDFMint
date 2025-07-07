import os
import shutil
import re
from app import app

# --- CONFIGURATION ---
OUTPUT_FOLDER = 'docs'

# A dictionary mapping your view functions to the output HTML filename
# This is the single source of truth for our links.
PAGES = {
    'home': 'index.html',
    'merge_tool': 'merge.html',
    'split_tool': 'split.html',
    'rotate_tool': 'rotate.html',
    'compress_tool': 'compress.html',
    'image_to_pdf_tool': 'image_to_pdf.html',
    'pdf_to_image_tool': 'pdf_to_image.html',
    'protect_tool': 'protect.html',
    'unlock_tool': 'unlock.html',
}

# --- FUNCTIONS ---

def build_static_files():
    """Renders the Flask templates into static HTML files in the output folder."""
    print("--- 1. Rendering templates into static HTML files... ---")
    # We need a context to be able to use url_for
    with app.test_request_context():
        for endpoint, output_filename in PAGES.items():
            try:
                # Get the URL path for the endpoint (e.g., /merge)
                url_path = app.url_map.iter_rules(endpoint=endpoint).__next__().rule
                
                # Use the test client to get the rendered HTML content
                response = app.test_client().get(url_path)
                
                if response.status_code == 200:
                    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                    with open(output_path, 'wb') as f:
                        f.write(response.data)
                    print(f"  - Built: {output_filename}")
                else:
                    print(f"  - ERROR: Failed to build {output_filename} (Status: {response.status_code})")
            except Exception as e:
                print(f"  - ERROR: Could not build page for endpoint '{endpoint}'. Reason: {e}")

def fix_links():
    """Goes through all built HTML files and corrects the internal links."""
    print("\n--- 2. Fixing internal links for static deployment... ---")
    with app.test_request_context():
        for output_filename in os.listdir(OUTPUT_FOLDER):
            if output_filename.endswith('.html'):
                filepath = os.path.join(OUTPUT_FOLDER, output_filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # This is where we replace the links
                for endpoint, html_file in PAGES.items():
                    # Get the Flask-generated path (e.g., /merge)
                    flask_path = app.url_map.iter_rules(endpoint=endpoint).__next__().rule
                    
                    # Define the correct static path (e.g., merge.html)
                    static_path = html_file
                    
                    # Create the regex pattern to find href="/path"
                    pattern = f'href="{flask_path}"'
                    replacement = f'href="{static_path}"'
                    
                    # Replace all occurrences
                    content = re.sub(pattern, replacement, content)

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  - Processed links in: {output_filename}")


# --- MAIN EXECUTION ---
if __name__ == '__main__':
    print("Starting static site build...")

    # Create or clean the output directory
    if os.path.exists(OUTPUT_FOLDER):
        shutil.rmtree(OUTPUT_FOLDER)
    os.makedirs(OUTPUT_FOLDER)
    print(f"Created clean output folder: '{OUTPUT_FOLDER}'")

    # Step 1: Render the templates
    build_static_files()
    
    # Step 2: Fix the links in the rendered files
    fix_links()
    
    print("\nBuild complete! The 'docs' folder is ready for deployment.")