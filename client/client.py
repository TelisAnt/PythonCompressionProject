import requests
from flask import Flask, request, jsonify, render_template
import base64
import hashlib
import random
import magic  # Για αναγνώριση τύπου αρχείου
import os

app = Flask(__name__, template_folder='templates')

def lz77_compress(data):
    compressed = bytearray()
    i = 0
    data = bytearray(data)  # Μετατροπή σε bytearray
    
    while i < len(data):
        # Απλοποιημένη υλοποίηση - βρίσκει μόνο απλές επαναλήψεις
        if i > 0 and data[i] == data[i-1]:
            compressed.extend(bytes([1, 1, data[i]]))  # (offset, length, char)
            i += 1
        else:
            compressed.append(data[i])
            i += 1
            
    return bytes(compressed)

def add_pkcs7_padding(data, block_size=16): # Προσθήκη PKCS7 padding
    if isinstance(data, list):
        data = bytes(data)
    pad_len = block_size - (len(data) % block_size)
    padding = bytes([pad_len] * pad_len)
    return data + padding

def add_errors(data, error_percent):# Προσθήκη τυχαίων σφαλμάτων
    if not isinstance(data, bytearray):
        data = bytearray(data)
    error_bytes = max(1, int(len(data) * error_percent / 100))
    for _ in range(error_bytes):
        pos = random.randint(0, len(data)-1)
        data[pos] ^= 0xFF
    return data

@app.route('/')
def home():
    return render_template('index.html') # Αρχική σελίδα με φόρμα

@app.route('/process', methods=['POST'])
def handle_upload():
    if 'file' not in request.files:
        return jsonify({"error": "Δεν ανεβάσατε αρχείο"}), 400
    
    file = request.files['file']
    error_percent = int(request.form.get('error_percent', 5))
    
    try:
        # Διαβάζουμε τα δεδομένα ως bytes
        image_data = file.read()
        mime_type = magic.from_buffer(image_data, mime=True)
        if not file.mimetype.startswith('image/'):
            return jsonify({"error": "Το αρχείο δεν είναι εικόνα"}), 400
    
        compressed = lz77_compress(image_data) #Compress 
        
        # Padding
        padded = add_pkcs7_padding(compressed)
        
        # Προσθήκη σφαλμάτων
        corrupted = add_errors(padded, error_percent)
        
        # Base64 encoding
        encoded_b64 = base64.b64encode(corrupted).decode('utf-8')

        #JSON
        json_to_server = {
            "encoded_message": encoded_b64,
            "compression_algorithm": "lz77",
            "encoding": "cyclic",
            "parameters": ["generator_polynomial=1011"],
            "errors": error_percent,
            "SHA256": hashlib.sha256(image_data).hexdigest(),
            "entropy": 7.5
        }

        # Αποστολή στον server
        response = requests.post("http://localhost:5000/upload", json=json_to_server)
        return jsonify(response.json())

    except Exception as e:
        return jsonify({"error": f"Σφάλμα επεξεργασίας: {str(e)}"}), 500

if __name__ == '__main__':
    print("Template path:", os.path.join(os.path.dirname(__file__), 'templates', 'index.html'))
    app.run(port=8000, debug=True)