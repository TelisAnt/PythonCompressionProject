# Image Transfer and Processing Web Application (Flask, Python)

## Description

This project is a client-server web application implemented in Python using Flask. It demonstrates a custom image transmission protocol, including compression, padding, encoding, error insertion, and decoding using socket-style HTTP communication via a RESTful API.

The application performs the following:

1. **Client-Side**:
    - Receives an image file from the user through a web interface.
    - Verifies that the uploaded file is an actual image using its **MIME type** (not the file extension).
    - Compresses the image using a custom-implemented algorithm (**LZ77**) — no external compression libraries are allowed.
    - Applies **PKCS#7 padding** to achieve a 128-bit length.
    - Encodes the result using a selected error-correcting code (**cyclic**) with user-defined parameters (e.g., generator polynomial).
    - Inserts random bit errors in **X%** of the message length, where **X** is chosen by the user.
    - Encodes the final binary into a Base64 string.
    - Calculates the **SHA256 hash** and **entropy** of the original compressed message.
    - Sends a JSON object to the server with all the required metadata and the encoded message.

2. **Server-Side**:
    - Receives the JSON payload.
    - Uses the parameters to decode the message and attempt error correction.
    - Displays the number of errors it was able to correct and compares this with the user's input.
    - Recomputes the SHA256 hash of the decoded message and compares it to the original hash.
    - Calculates and displays the entropy of the final message.

---

## How to Run the Project
**1. Clone the repository**: 
  -git clone https://github.com/TelisAnt/PythonCompressionProject
  -cd PythonCompressionProject

**2. Create and activate a virtual environment**:
  -python -m venv venv
  -source venv/bin/activate  # For Unix/macOS
  -venv\Scripts\activate     # For Windows

**3. Install required libraries**:
With the virtual environment activated, install the following libraries using pip:
 -pip install Flask
 -pip install requests
 -pip install python-magic

## Running the Application
 **Terminal 1 – Server**
 Activate virtual environment
source venv/bin/activate

# Start the Flask server
 -python webapp.py
 -Flask server will be available at: http://localhost:5000

**Terminal 2 – Client**
Activate virtual environment
 -source venv/bin/activate

**Start the Flask client interface**
 -python client.py
**Flask client UI will open in your browser at: http://localhost:8000**
