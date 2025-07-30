import json
import os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

KEYSTORE_PATH = os.getenv("KEYSTORE_PATH")
ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")

# Read and decrypt keystore
with open(KEYSTORE_PATH, "r") as f:
    keystore = json.load(f)

private_key = Account.decrypt(keystore, ACCOUNT_PASSWORD)
hex_key = private_key.hex()

# Append PRIVATE_KEY to .env file if not already present
env_path = ".env"

with open(env_path, "r") as f:
    lines = f.readlines()

# Remove existing PRIVATE_KEY if already present
lines = [line for line in lines if not line.startswith("PRIVATE_KEY=")]

# Add the new key
lines.append(f"PRIVATE_KEY={hex_key}\n")

# Write back
with open(env_path, "w") as f:
    f.writelines(lines)

print("Private key extracted and added to .env successfully.")
