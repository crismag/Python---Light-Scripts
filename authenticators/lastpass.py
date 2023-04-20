import hashlib
import hmac
import base64
import time

# Enter your secret key here
secret_key = 'YourSecretKeyHere'

# Convert the secret key from base32 to bytes
key_bytes = base64.b32decode(secret_key)

# Get the current time in 30-second intervals
timestamp = int(time.time() / 30)

# Convert the timestamp to bytes (big-endian)
timestamp_bytes = timestamp.to_bytes(8, byteorder='big')

# Calculate the HMAC-SHA1 hash of the timestamp using the secret key
hmac_hash = hmac.new(key_bytes, timestamp_bytes, hashlib.sha1).digest()

# Get the 4-byte offset from the hash (the last 4 bits of the hash)
offset = hmac_hash[-1] & 0x0f

# Get the 4-byte code from the hash (the 4 bytes starting at the offset)
code_bytes = hmac_hash[offset:offset+4]

# Convert the code bytes to an integer (big-endian)
code_int = int.from_bytes(code_bytes, byteorder='big')

# Truncate the code to 6 digits
code = code_int % 10**6

# Print the code
print(code)
