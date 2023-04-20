import rsa
import hashlib
import base64

#ONLY WORKS PROVIDED WE HAVE THE GENERATED RSA PRIVATE KEYS.

ctfData = 'SOMECTFXXXXXXXXXXXXXXXXXXXXXDATA'

# Convert ctfData to bytes
ctfData_bytes = bytes.fromhex(ctfData)

# Create hash of ctfData
hash_obj = hashlib.sha1(ctfData_bytes)
hash_bytes = hash_obj.digest()

# Pad hash with leading zeros to make it 20 bytes
padded_hash_bytes = b'\x00' * (20 - len(hash_bytes)) + hash_bytes

# Load RSA key from file (or generate key pair)
with open('private.pem', mode='rb') as privatefile:
    keydata = privatefile.read()
privkey = rsa.PrivateKey.load_pkcs1(keydata)

# Encrypt hash with RSA private key
token_bytes = rsa.pkcs1.encrypt(padded_hash_bytes, privkey)

# Convert encrypted hash to Base64-encoded token
token = base64.b32encode(token_bytes).decode('ascii')

print(token)
