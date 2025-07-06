from flask import Flask, request, jsonify
import base64
import hashlib
import math

app = Flask(__name__)  # Δημιουργία Flask εφαρμογής

def lz77_decompress(data: bytes) -> bytes: # Αποσυμπίεση με LZ77
    decompressed = bytearray()  # Δημιουργία bytearray για αποσυμπιεσμένα δεδομένα
    i = 0  # Αρχικοποίηση δείκτη
    while i < len(data):
        # Έλεγχος για συγκεκριμένο μοτίβο (1,1) που χρησιμοποιήθηκε στη συμπίεση
        if i + 2 < len(data) and data[i] == 1 and data[i+1] == 1:
            decompressed.append(data[i+2])  # Προσθήκη του επόμενου byte
            i += 3  # Μετάβαση 3 θέσεις μπροστά
        else:
            decompressed.append(data[i])  # Προσθήκη του τρέχοντος byte
            i += 1  # Μετάβαση στην επόμενη θέση
    return bytes(decompressed)  # Μετατροπή σε bytes και επιστροφή

def pkcs7_unpad(data: bytes) -> bytes: # Αφαίρεση PKCS7 padding
    if not data:  # Έλεγχος για κενά δεδομένα
        return data
    
    pad_len = data[-1]  # Το τελευταίο byte δείχνει το μήκος του padding
    
    # Έλεγχος εγκυρότητας του padding
    if pad_len < 1 or pad_len > 16:  # Το padding πρέπει να είναι 1-16 bytes
        return data
    
    # Έλεγχος αν όλα τα bytes του padding είναι σωστά
    if data[-pad_len:] != bytes([pad_len]) * pad_len:
        return data
    
    return data[:-pad_len]  # Επιστροφή δεδομένων χωρίς το padding

def shannon_entropy(data: bytes) -> float: # Υπολογισμός εντροπίας
    if not data:  # Έλεγχος για κενά δεδομένα
        return 0.0
    
    freq = {}  # Λεξικό για καταμέτρηση συχνοτήτων bytes
    
    # Καταμέτρηση συχνοτήτων κάθε byte
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    
    entropy = 0.0  # Αρχικοποίηση εντροπίας
    length = len(data)  # Μήκος δεδομένων
    
    # Υπολογισμός εντροπίας για κάθε byte
    for count in freq.values():
        p = count / length  # Πιθανότητα εμφάνισης του byte
        entropy -= p * math.log2(p)  # Τύπος εντροπίας Shannon
    
    return entropy

def error_correction(data: bytes, errors_in_message: int) -> (bytes, int):
    corrected_errors = int(errors_in_message * 0.9)  # Προσομοίωση 90% επιτυχίας
    return data, corrected_errors  # Επιστροφή ίδιων δεδομένων και αριθμού διορθώσεων

@app.route('/')
def index():
    return "Server is running. Use POST /upload to send data."

@app.route('/upload', methods=['POST'])
def upload(): # Διαχείριση αιτήματος POST για αποστολή δεδομένων
    if not request.is_json:  # Έλεγχος ότι τα δεδομένα είναι JSON
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.json  # Ανάγνωση JSON δεδομένων
    
    # Ανάκτηση απαραίτητων πεδίων από το JSON
    encoded_message_b64 = data.get("encoded_message")  # Base64 κωδικοποιημένο μήνυμα
    original_sha256 = data.get("SHA256")  # Αρχικό hash SHA256
    expected_errors = int(data.get("errors", 0))  # Αριθμός σφαλμάτων (μετατροπή σε int)
    parameters = data.get("parameters", [])  # Παράμετροι επεξεργασίας
    
    # Έλεγχος υποχρεωτικών πεδίων
    if not encoded_message_b64 or not original_sha256:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        # Αποκωδικοποίηση από base64
        corrupted_bytes = base64.b64decode(encoded_message_b64)
        
        # Αποσυμπίεση με LZ77
        decompressed = lz77_decompress(corrupted_bytes)
        
        # Αφαίρεση padding
        unpadded = pkcs7_unpad(decompressed)
        
        # Διόρθωση σφαλμάτων (προσομοίωση)
        corrected_message, corrected_errors = error_correction(unpadded, expected_errors)
        
        # Υπολογισμός SHA256 για τα αποκωδικοποιημένα δεδομένα
        decoded_sha256 = hashlib.sha256(corrected_message).hexdigest()
        
        # Υπολογισμός εντροπίας
        entropy_value = shannon_entropy(corrected_message)
        
        # Κωδικοποίηση των αποτελεσμάτων σε base64 για επιστροφή
        decoded_message_b64 = base64.b64encode(corrected_message).decode()
        
        # Επιστροφή JSON με τα αποτελέσματα
        return jsonify({
            "status": "success",
            "corrected_errors": corrected_errors,  # Αριθμός διορθωμένων σφαλμάτων
            "errors_difference": abs(expected_errors - corrected_errors),  # Διαφορά
            "sha256_match": (decoded_sha256 == original_sha256),  # Έλεγχος hash
            "decoded_sha256": decoded_sha256,  # Το νέο hash
            "entropy": entropy_value,  # Τιμή εντροπίας
            "decoded_message_base64": decoded_message_b64  # Αποκωδικοποιημένα δεδομένα
        })
        
    except Exception as e:
        # Χειρισμός σφαλμάτων κατά την επεξεργασία
        return jsonify({"error": f"Server processing error: {str(e)}"}), 500

if __name__ == '__main__':
    # Εκκίνηση του Flask server
    app.run(port=5000, debug=True)