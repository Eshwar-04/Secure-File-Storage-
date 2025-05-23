from flask import Flask, render_template, request, send_file, redirect, url_for
from azure.storage.blob import BlobServiceClient
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Load secrets from environment variables
CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")

if not CONNECTION_STRING or not CONTAINER_NAME:
    raise EnvironmentError("❌ Missing Azure connection info. Set AZURE_CONNECTION_STRING and AZURE_CONTAINER_NAME as environment variables.")

# Initialize BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

# Encryption key file
KEY_FILE = "encryption_key.key"

# Generate or load encryption key
if not os.path.exists(KEY_FILE):
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)
else:
    with open(KEY_FILE, "rb") as key_file:
        key = key_file.read()

cipher = Fernet(key)

# Ensure container exists
try:
    container_client.create_container()
except Exception:
    pass

@app.route('/')
def index():
    blob_list = []
    for blob in container_client.list_blobs():
        local_time = blob.last_modified.astimezone().strftime("%Y-%m-%d %H:%M:%S") if blob.last_modified else "N/A"
        blob_list.append({"name": blob.name, "timestamp": local_time})
    return render_template('index.html', files=blob_list)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files or request.files['file'].filename == '':
        return "No file uploaded or selected!"

    file = request.files['file']
    encrypted_filename = f"encrypted_{file.filename}"
    encrypted_data = cipher.encrypt(file.read())

    blob_client = container_client.get_blob_client(encrypted_filename)
    blob_client.upload_blob(encrypted_data, overwrite=True)

    return redirect(url_for('index'))

@app.route('/download/<filename>')
def download(filename):
    try:
        blob_client = container_client.get_blob_client(filename)
        encrypted_data = blob_client.download_blob().readall()
        decrypted_data = cipher.decrypt(encrypted_data)

        decrypted_filename = filename.replace("encrypted_", "")
        decrypted_path = os.path.join("downloads", decrypted_filename)
        os.makedirs("downloads", exist_ok=True)

        with open(decrypted_path, "wb") as file:
            file.write(decrypted_data)

        return send_file(decrypted_path, as_attachment=True)

    except Exception as e:
        return f"⚠️ Error downloading file: {str(e)}"

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    try:
        blob_client = container_client.get_blob_client(filename)
        blob_client.delete_blob()
        return redirect(url_for('index'))
    except Exception as e:
        return f"⚠️ Error deleting file: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
