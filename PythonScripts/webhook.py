from flask import *
import ssl
import os

cert_path = os.path.expanduser('/home/babykali/tools/UploadAttacks/cert.pem')
key_path = os.path.expanduser('/home/babykali/tools/UploadAttacks/key.pem')

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile=cert_path, keyfile=key_path)

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello, HTTPS!'


@app.route('/webhook', methods=['POST', 'GET'])
@app.route('/webhook/', methods=['POST', 'GET'])
def handle_webhook():
    if request.method == 'POST':
        # Process the incoming POST webhook payload here
        data = request.get_json()  # Get JSON payload (if webhook sends JSON)
        print("Received POST webhook data:", data)
        # Perform actions based on the received data
        return 'Webhook received via POST successfully', 200
    elif request.method == 'GET':
        # Process the incoming GET request (optional)
        return 'Webhook received via GET successfully', 200
    else:
        return 'Method not allowed', 405

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

'''
@app.route('/<path:file_path>')
def serve_file(file_path):
    # Get the absolute path of the requested file
    abs_file_path = os.path.join(os.path.dirname(__file__), file_path)
    
    # Check if the file exists and is within the current directory
    if os.path.isfile(abs_file_path) and abs_file_path.startswith(os.path.dirname(__file__)):
        return send_file(abs_file_path)
    else:
        return 'File not found or access denied', 404
'''

@app.route('/<path:file_path>')
def serve_file(file_path):
    # Get the absolute path of the requested file
    abs_file_path = os.path.join(os.getcwd(), file_path)
    
    # Check if the file exists and is within the current directory
    if os.path.isfile(abs_file_path) and abs_file_path.startswith(os.getcwd()):
        return send_file(abs_file_path)
    else:
        return 'File not found or access denied', 404


if __name__ == '__main__':
    app.run(ssl_context=context, host='0.0.0.0', port=443)
