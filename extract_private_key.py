from eth_account import Account
import json

# Path to the keystore file
keystore_path = "node0/data/keystore/UTC--2025-07-14T17-46-40.191093314Z--2bf7aed45b11b95367b12ae0b920315151a728bb"
password = "12345"  # The password used when creating the account

# Load and decrypt the keystore file
with open(keystore_path) as f:
    keystore = json.load(f)

private_key = Account.decrypt(keystore, password).hex()
print("✅ Private Key:", private_key)
