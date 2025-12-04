from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Gib diesen Schlüssel aus und füge ihn in deinen Code ein
