#!/usr/bin/env python3
import os
import json
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from decrypt_key import get_private_key, scp_distribution

load_dotenv()

# Load env
RPC_URL = os.getenv("RPC_URL")
ABI_PATH = os.getenv("ABI_PATH")
BYTECODE_PATH = os.getenv("BYTECODE_PATH")
OUTPUT_ADDRESS_FILE = os.getenv("OUTPUT_ADDRESS_FILE", "../deployed/contract_address.txt")

# Validate
if not all([RPC_URL, ABI_PATH, BYTECODE_PATH]):
    raise RuntimeError("Missing one of required env vars: RPC_URL, ABI_PATH, BYTECODE_PATH")

# Connect
w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
if not w3.is_connected():
    raise RuntimeError(f"Cannot connect to RPC at {RPC_URL}")

# Load private key securely
# private_key_bytes = bytes.fromhex(get_private_key())
account = Account.from_key(get_private_key())
deployer = account.address
print(f"Deploying from address: {deployer}")

# Load compiled contract
with open(ABI_PATH) as f:
    abi = json.load(f)
with open(BYTECODE_PATH) as f:
    bytecode = f.read().strip()

contract = w3.eth.contract(abi=abi, bytecode=bytecode)

# Build transaction
nonce = w3.eth.get_transaction_count(deployer)
tx = contract.constructor().build_transaction({
    'from': deployer,
    'nonce': nonce,
    'gas': 3000000,
    'gasPrice': w3.to_wei('0', 'gwei')  # Quorum uses 0 gasPrice
})

# Sign transaction
signed_tx = w3.eth.account.sign_transaction(tx, get_private_key())

# Send transaction
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
print(f"Transaction sent. Hash: {tx_hash.hex()}")

# Wait for receipt
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Contract deployed at address: {receipt.contractAddress}")

# Save deployed contract address to file
os.makedirs(os.path.dirname(OUTPUT_ADDRESS_FILE), exist_ok=True)
with open(OUTPUT_ADDRESS_FILE, "w") as f:
    f.write(receipt.contractAddress)
    print(f"Contract address saved to {OUTPUT_ADDRESS_FILE}")

# Define list of your Raspberry Pi node aliases
pi_nodes = ["pi_2", "pi_3", "pi_4", "pi_5"]

# List of files to distribute
files = [
    ABI_PATH,            # ../compiled/EnergyTrade_abi.json
    OUTPUT_ADDRESS_FILE  # ../deployed/contract_address.txt
]

# scp_distribution(pi_nodes, files_to_send=files)
