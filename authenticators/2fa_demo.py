import hashlib
import json
import time

# Function to generate a secret token and store it in a file
def generate_2fa_secret(username, session_id, method):
    # Generate a random 6-digit integer as the token
    token = str(random.randint(100000, 999999))
    
    # Compute the MD5 hash of the token
    token_hash = hashlib.md5(token.encode('utf-8')).hexdigest()
    
    # Set the timestamp for when the token was generated
    generated_timestamp = time.time()
    
    # Set the timestamp for when the token will expire (10 minutes from now)
    expires_timestamp = generated_timestamp + (10 * 60)
    
    # Create a dictionary with the relevant information
    data = {
        "user": username,
        "token": token_hash,
        "generated": generated_timestamp,
        "expires": expires_timestamp,
        "method": method
    }
    
    # Write the dictionary to a file
    filename = f"{username}.{session_id}.session"
    with open(filename, 'w') as f:
        json.dump(data, f)

# Function to validate a token and check if it has expired
def validate_2fa_token(username, session_id, token):
    # Load the session data from the file
    filename = f"{username}.{session_id}.session"
    with open(filename, 'r') as f:
        data = json.load(f)
    
    # Check if the token matches the stored hash
    if hashlib.md5(token.encode('utf-8')).hexdigest() == data["token"]:
        # Check if the token has expired
        if time.time() < data["expires"]:
            return True
        else:
            print("Token has expired.")
            return False
    else:
        print("Invalid token.")
        return False

#---------------------------------------------------------------------
