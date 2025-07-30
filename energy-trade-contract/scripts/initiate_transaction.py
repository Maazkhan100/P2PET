#!/usr/bin/env python3
import os, time
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Load config from .env
RPC_URL = os.getenv("RPC_URL")
ABI_PATH = os.getenv("ABI_PATH")
CONTRACT_ADDRESS_PATH = os.getenv("CONTRACT_ADDRESS_PATH")

# Read deployed contract address
with open(CONTRACT_ADDRESS_PATH, "r") as f:
    CONTRACT_ADDRESS = f.read().strip()

# Connect to Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
private_key = PRIVATE_KEY

# Set up account
account = w3.eth.account.from_key(private_key)
sender_address = account.address

# Load ABI
with open(ABI_PATH, "r") as f:
    abi = json.load(f)

# Contract instance
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

def send_transaction(function_call):
    nonce = w3.eth.get_transaction_count(sender_address)

    tx = function_call.build_transaction({
        'from': sender_address,
        'nonce': nonce,
        'gas': 500000,
        'gasPrice': 0
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash.hex()

def register():
    print("Registering participant...")
    tx_hash = send_transaction(contract.functions.register())
    print(f"Registration TX: {tx_hash}")

def submit_data(role: int, energy: int, price_wei: int):
    print("Submitting energy data...")
    tx_hash = send_transaction(contract.functions.submitData(role, energy, price_wei))
    print(f"Data Submission TX: {tx_hash}")

if __name__ == "__main__":
    try:
        # register()
        time.sleep(60)
        submit_data(role=2, energy=100, price_wei=Web3.to_wei(0.05, "ether"))
    except Exception as e:
        print(f"Error occurred: {e}")
