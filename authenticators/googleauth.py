import pyotp

# create a TOTP object with a secret key
secret_key = 'MYSECRETKEY'
totp = pyotp.TOTP(secret_key)

# generate a 6-digit code
code = totp.now()

# print the code
print(code)
