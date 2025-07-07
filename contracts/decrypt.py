
def decrypt_aes128(encryption_file, passphrase='somethingSilly'):
    import json
    from eth_keyfile import decode_keyfile_json # pip install eth-keyfile

    with open(encryption_file, 'r') as f:
        keystore = json.load(f)

    # Decode the private key from the keystore file
    private_key = decode_keyfile_json(keystore, passphrase.encode('utf-8'))

    return private_key.hex() # return hex form, usual form is still not readable
