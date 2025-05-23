from azure.storage.blob import BlobServiceClient
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
load_dotenv()

key = Fernet.generate_key()
cipher = Fernet(key)
print(key)
with open("testfile.txt", "rb") as file:
    encrypted_data = cipher.encrypt(file.read())

connection_string = os.getenv("AZURE_CONNECTION_STRING")
container_name = os.getenv("AZURE_CONTAINER_NAME")
blob_name = "encrypted_testfile.txt"

blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

blob_client = container_client.get_blob_client(blob_name)
blob_client.upload_blob(encrypted_data, overwrite=True)

print("Encrypted file uploaded successfully!")
