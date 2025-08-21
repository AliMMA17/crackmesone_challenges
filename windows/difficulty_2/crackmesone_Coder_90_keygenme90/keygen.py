import base64

def keygen(username: str) -> str:
    # XOR each ASCII byte with 0x5A, then Base64-encode
    xored = bytes(b ^ 0x5A for b in username.encode('ascii'))
    return base64.b64encode(xored).decode('ascii')

print(keygen("abcd"))
