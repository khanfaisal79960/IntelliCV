from flask import Flask, request, render_template, redirect, url_for, flash
from parser.resume_parser import ResumeParser
import os
import io
# NLTK import and path configuration removed as NLTK is no longer used

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Replace with a strong secret key
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

parser = ResumeParser()

@app.route('/')
def index():
    """Renders the main upload form page."""
    return render_template('index.html')

@app.route('/parse', methods=['POST'])
def parse_resume():
    """Handles resume file uploads and parsing."""
    if 'resume_file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['resume_file']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file:
        filename = file.filename
        
        # Pass the file stream directly to the parser
        # Using io.BytesIO to ensure the file stream is rewindable and usable by PyPDF2/python-docx
        file_stream = io.BytesIO(file.read())
        
        # Parse the resume
        extracted_data = parser.parse_resume(file_stream, filename)
        
        if "error" in extracted_data:
            flash(extracted_data["error"])
            return redirect(url_for('index'))
        
        return render_template('index.html', extracted_data=extracted_data)
    
    flash('An unexpected error occurred during file upload.')
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 error handler."""
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True) # Set debug=False in production
