from azure.storage.blob import BlobServiceClient
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
load_dotenv()

# Step 1: Generate an encryption key
key = Fernet.generate_key()
cipher = Fernet(key)

# Save the key for later decryption
with open("encryption_key.key", "wb") as key_file:
    key_file.write(key)

# Step 2: Encrypt the file before uploading
input_file = "testfile.txt"
encrypted_file = "encrypted_testfile.txt"

with open(input_file, "rb") as file:
    encrypted_data = cipher.encrypt(file.read())

with open(encrypted_file, "wb") as file:
    file.write(encrypted_data)

print("✅ File encrypted successfully!")

# Step 3: Azure Blob Storage connection details
connection_string = os.getenv("AZURE_CONNECTION_STRING")
container_name = os.getenv("AZURE_CONTAINER_NAME")
blob_name = "encrypted_testfile.txt"

# Step 4: Initialize BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

# Create container if it does not exist
try:
    container_client.create_container()
except Exception as e:
    print("⚠️ Container may already exist:", str(e))

# Step 5: Upload the encrypted file to Azure Blob Storage
blob_client = container_client.get_blob_client(blob_name)
blob_client.upload_blob(encrypted_data, overwrite=True)

print("✅ Encrypted file uploaded successfully!")

# Step 6: Download the encrypted file
downloaded_blob = blob_client.download_blob().readall()

with open("downloaded_encrypted.txt", "wb") as file:
    file.write(downloaded_blob)

print("✅ Encrypted file downloaded successfully!")

# Step 7: Decrypt the downloaded file
with open("encryption_key.key", "rb") as key_file:
    decryption_key = key_file.read()

cipher = Fernet(decryption_key)

with open("downloaded_encrypted.txt", "rb") as file:
    decrypted_data = cipher.decrypt(file.read())

with open("decrypted_testfile.txt", "wb") as file:
    file.write(decrypted_data)

print("✅ File decrypted successfully! Check 'decrypted_testfile.txt'.")
