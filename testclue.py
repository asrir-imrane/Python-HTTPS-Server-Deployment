from Crypto.Cipher import AES
import base64
import hashlib

# The Base64-decoded data with padding handled
encoded_data = "d8b8a0563f0ce9590f930fb8fd6aef99820b11dab41f459aa98414629a34ef65882decaaebe8a34969bd3b37df1a312904a2d48c0f5338d6a76aa2218a76a86cbbc66944abe77f94ec76f0ff4f7a8df8aeb431ac4f1253e5ae083863c643ea98b2fa531ce573aba8696bff52186b161802a4849346e071e3aa32ac4e6256ab96d40b97fe19d668f132247ab4e8dfd3925695089b926e80e7169213584af2d5cdfe..."

while len(encoded_data) % 4 != 0:
    encoded_data += "="

encrypted_data = base64.b64decode(encoded_data)

# Ensure encrypted data is a multiple of 16 bytes
if len(encrypted_data) % 16 != 0:
    encrypted_data += b' ' * (16 - len(encrypted_data) % 16)

rovers = {
    "Sojourner": "1997",
    "Spirit": "2004",
    "Opportunity": "2004",
    "Curiosity": "2012",
    "Perseverance": "2020"
}

# Attempt decryption using CBC with an IV of zeroes
def decrypt_aes_cbc(encrypted_data, rover_name, year):
    key = f"data,{rover_name}{year}".encode()
    key = hashlib.sha256(key).digest()  # Generate 256-bit AES key
    iv = b'\x00' * 16  # Assuming IV is all zeroes as a trial

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = cipher.decrypt(encrypted_data)

    try:
        return decrypted_data.decode('utf-8')
    except UnicodeDecodeError:
        return None

# Try each rover name and year combination
for rover, year in rovers.items():
    result = decrypt_aes_cbc(encrypted_data, rover, year)
    if result:
        print(f"Decrypted data with rover '{rover}' and year '{year}':\n{result}")
        break
    else:
        print(f"Failed with rover '{rover}' and year '{year}'")
