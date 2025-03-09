# encryption.py
import os
import base64
from google.cloud import storage, kms
from nacl.secret import SecretBox

class EncryptionManager:
    def __init__(self, logger, json_key_path="/app/tee-key.json"):
        self.logger = logger
        self.storage_client = storage.Client.from_service_account_json(json_key_path)
        self.kms_client = kms.KeyManagementServiceClient.from_service_account_json(json_key_path)
        self.bucket_name = "quincefinance-user-ids-tee"
        self.kms_key_name = "projects/2646471602940057664/locations/global/keyRings/quincefinance-keyring/cryptoKeys/user-id-encryption-key" 
        self.tee_key = self.load_or_generate_tee_key()

    def load_or_generate_tee_key(self):
        """Load or generate the TEE-local key, stored in GCS."""
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob("tee_key.enc")
        if blob.exists():
            encrypted_key = blob.download_as_string()
            decrypt_response = self.kms_client.decrypt(
                request={"name": self.kms_key_name, "ciphertext": encrypted_key}
            )
            self.logger.debug("Loaded TEE key from GCS")
            return decrypt_response.plaintext  # 32-byte key
        else:
            key = os.urandom(32)
            encrypt_response = self.kms_client.encrypt(
                request={"name": self.kms_key_name, "plaintext": key}
            )
            blob.upload_from_string(encrypt_response.ciphertext)
            self.logger.info("Generated and stored new TEE key in GCS")
            return key

    def encrypt(self, plaintext: str) -> str:
        """Encrypt with TEE-local key and KMS."""
        box = SecretBox(self.tee_key)
        encrypted_tee = box.encrypt(plaintext.encode())
        encrypt_response = self.kms_client.encrypt(
            request={"name": self.kms_key_name, "plaintext": encrypted_tee}
        )
        return base64.b64encode(encrypt_response.ciphertext).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt from KMS and TEE-local key."""
        ciphertext_bytes = base64.b64decode(ciphertext)
        decrypt_response = self.kms_client.decrypt(
            request={"name": self.kms_key_name, "ciphertext": ciphertext_bytes}
        )
        box = SecretBox(self.tee_key)
        return box.decrypt(decrypt_response.plaintext).decode()