import hashlib
import json

from Cryptodome.Cipher import AES


# The key for the AES encryption must be 32 bytes long
def get_key(password):
    hasher = hashlib.sha256()
    hasher.update(password.encode('utf-8'))
    return hasher.digest()


# Function to encrypt the message using AES with a given key
def encrypt(message, password):
    key = get_key(password)
    cipher = AES.new(key, AES.MODE_EAX)
    plaintext = message.encode('utf-8')
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return [cipher.nonce, tag, ciphertext]


def decrypt(encrypted, password):
    key = get_key(password)
    nonce, tag, ciphertext = encrypted
    try:
    # Decrypt the message
        cipher = AES.new(key, AES.MODE_EAX, nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    except ValueError:
        # The message could not be decrypted or the tag is invalid
        return None
    else:
        # The message was decrypted successfully
        return plaintext