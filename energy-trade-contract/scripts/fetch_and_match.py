import json
import os
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from dotenv import load_dotenv
from matching import Offer, greedy_double_auction
from eth_utils import keccak

# Load .env
load_dotenv()

# Env vars
RPC_URL = os.getenv("RPC_URL")
KEYSTORE_PATH = os.getenv("KEYSTORE_PATH")
ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")
ABI_PATH = os.getenv("ABI_PATH")
CONTRACT_ADDRESS_PATH = os.getenv("CONTRACT_ADDRESS_PATH")

# Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Load ABI
with open(ABI_PATH, "r") as f:
    abi = json.load(f)

# Load contract address
with open(CONTRACT_ADDRESS_PATH, "r") as f:
    CONTRACT_ADDRESS = f.read().strip()

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

# Load keystore and decrypt
with open(KEYSTORE_PATH) as keyfile:
    encrypted_key = json.load(keyfile)
    private_key = Account.decrypt(encrypted_key, ACCOUNT_PASSWORD).hex()

account = w3.eth.account.from_key(private_key)
sender_address = account.address

def fetch_all_participants():
    offers = []
    for i in range(10):
        try:
            data = contract.functions.participantsList(i).call()
            addr, role, energy, price = data

            if role == 0:  # Role.N_A
                continue

            role_str = "buyer" if role == 1 else "seller"
            offer = Offer(addr, role_str, energy, price)
            offers.append(offer)
        except Exception as e:
            print(f"Error fetching slot {i}: {e}")
    return offers

def send_result_hash_to_contract(result_hash_hex):
    nonce = w3.eth.get_transaction_count(sender_address)

    tx = contract.functions.submitExecutionResult(Web3.to_bytes(hexstr=result_hash_hex)).build_transaction({
        'from': sender_address,
        'nonce': nonce,
        'gas': 500000,
        'gasPrice': 0
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash.hex()

def main():
    print("Fetching participants...")
    offers = fetch_all_participants()

    if not offers:
        print("No valid participants submitted data.")
        return

    print(f"Running double auction on {len(offers)} participants...")
    matches = greedy_double_auction(offers)

    # Save to result file
    result_file = "../result/match_result.json"
    os.makedirs(os.path.dirname(result_file), exist_ok=True)
    with open(result_file, "w") as f:
        json.dump(matches, f, indent=2)

    print(f"Result written to: {result_file}")

    # Hash result file contents
    with open(result_file, "rb") as f:
        content_bytes = f.read()
        hash_bytes = keccak(content_bytes)
        result_hash_hex = hash_bytes.hex()

    print(f"Keccak256 hash of result: 0x{result_hash_hex}")

    # Submit hash
    tx_hash = send_result_hash_to_contract(result_hash_hex)
    print(f"Execution result submitted. TX Hash: {tx_hash}")

if __name__ == "__main__":
    main()
