import asyncio
import logging
from pprint import pprint

# Configure minimal logging to avoid cluttering output
logging.basicConfig(level=logging.ERROR)

from api.services.encryption_service import EncryptionService, current_dek, current_user_id
from api.models import JournalEntry

async def run_demo():
    print("==================================================")
    print("  HIPAA/GDPR Envelope Encryption (AES-GCM 256)   ")
    print("==================================================")
    
    # 1. Simulate Auth Middleware Context
    user_id = 1234
    print(f"\n[ Auth ] User {user_id} logging in...")
    
    # Generate a unique Data Encryption Key (DEK) for the User
    dek = EncryptionService.generate_dek()
    print(f"[ KEK  ] Wrapping User DEK with System Master Key...")
    wrapped_dek = EncryptionService.wrap_dek(dek)
    print(f"[ DB   ] Storing wrapped DEK in UserEncryptionKey vault:")
    print(f"         {wrapped_dek[:30]}...\n")
    
    # Set the ContextVars (This is what the middleware does)
    current_dek.set(dek)
    current_user_id.set(user_id)
    print("[ Sys  ] Auth middleware bound DEK to current request Thread/Context.\n")
    
    # 2. Simulate Creating a Journal Entry
    plaintext_content = "Today I felt a lot of anxiety about my upcoming presentation, but I managed to use my coping mechanisms to stay calm."
    
    print("--------------------------------------------------")
    print("              WRITE PATH (App -> DB)              ")
    print("--------------------------------------------------")
    print(f"User writes Journal Entry:\n>> '{plaintext_content}'\n")
    
    # The TypeDecorator handles this automatically, but we invoke it directly here to simulate SQLAlchemy's bind param processing
    encrypted_value = EncryptionService.encrypt_data(plaintext_content, dek)
    print("SQLAlchemy TypeDecorator Encrypts (AES-GCM + Nonce):")
    print(f">> {encrypted_value}\n")
    print("[ DB   ] Data is permanently unreadable without the User's DEK.")
    print("         (Even if the DB is stolen, data is secure.)\n")
    
    # 3. Simulate Reading a Journal Entry
    print("--------------------------------------------------")
    print("              READ PATH (DB -> App)               ")
    print("--------------------------------------------------")
    # Simulate an attacker or admin looking at the DB directly WITHOUT the ContextVar set
    current_dek.set(None)
    malicious_read = EncryptionService.decrypt_data(encrypted_value, None, log_audit=False)
    print("[ Attacker DB Access ] Trying to read without Context DEK:")
    print(f">> {malicious_read}\n")
    
    # Restore User Context for normal App usage
    current_dek.set(dek)
    print("[ App Valid Context ] User requests their own Journal Entry:")
    
    # Simulate SQLAlchemy's result value processing
    decrypted_value = EncryptionService.decrypt_data(encrypted_value, dek)
    print(f">> '{decrypted_value}'")
    print("\n[ Kafka ] background audit_trail event emitted: DATA_ACCESS (decrypted_sensitive_content) for user 1234")
    print("==================================================")

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_demo())
