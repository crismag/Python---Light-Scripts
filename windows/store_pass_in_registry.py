import winreg

# specify the key and value to store the password
key = winreg.HKEY_CURRENT_USER
subkey = r"Software\MyApp"
value_name = "password"

# set the password value in the registry
password = "mysecretpassword"
winreg.SetValueEx(winreg.CreateKey(key, subkey), value_name, 0, winreg.REG_SZ, password)

# retrieve the password value from the registry
password_key = winreg.OpenKey(key, subkey)
password, _ = winreg.QueryValueEx(password_key, value_name)

print(password)
