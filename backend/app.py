from flask import Flask, request, jsonify
from ectd_pdf_validator import validate_ectd_pdf, combine_text
from flask_cors import CORS
import tempfile
import os

app = Flask(__name__)
CORS(app)

@app.route('/validate', methods=['POST'])
def validate():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        file.save(temp_file.name)
        pdf_path = temp_file.name

    try:
        extracted_text = combine_text(pdf_path)
        result = validate_ectd_pdf(extracted_text, pdf_path)
        return jsonify(result)
    finally:
        os.remove(pdf_path)

if __name__ == '__main__':
    app.run(debug=True, port=5050)
