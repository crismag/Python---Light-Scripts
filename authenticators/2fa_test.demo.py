import hashlib
import time


def get_2fa_user_option():
    # Sample code to select the delivery method goes here
    return "email"

def generate_2fa(username, session_id):
    # Generate the secret token
    secret = "mysecrettoken"  # replace with code to generate random secret
    timestamp = int(time.time())
    token = hashlib.md5(f"{secret}-{username}-{session_id}-{timestamp}".encode()).hexdigest()

    # Store the token details in a session file
    session_file = f"{username}.{session_id}.session"
    with open(session_file, "w") as f:
        f.write(f'{{ "user": "{username}", "token": "{token}", "generated": "{timestamp}", "expires": "{timestamp + 600}" }}')

    # Send the token via the selected delivery method
    delivery_method = get_2fa_user_option()
    if delivery_method == "email":
        # code to send email goes here
        print(f"Token sent to {username} via email")
    elif delivery_method == "sms":
        # code to send SMS goes here
        print(f"Token sent to {username} via SMS")
    else:
        # code to use other delivery methods goes here
        print(f"Token sent to {username} via {delivery_method}")
