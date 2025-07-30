from web3 import Web3
from matching import Offer
import json
import os

# === Configuration ===
QUORUM_RPC_URL = "http://192.168.0.111:22000"
CONTRACT_ADDRESS = Web3.to_checksum_address("0xYourContractAddressHere")  # Replace with actual contract address
ABI_PATH = os.path.join("contracts", "EnergyTrading.json")  # Replace with actual ABI or ABI path

# === Connect to Quorum Node ===
w3 = Web3(Web3.HTTPProvider(QUORUM_RPC_URL))

if not w3.isConnected():
    raise Exception("Failed to connect to Quorum node at", QUORUM_RPC_URL)
else:
    print("Connected to Quorum node")

# === Load ABI ===
with open(ABI_PATH) as f:
    contract_abi = json.load(f)

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

# === Fetch Offers from Contract ===
def fetch_active_offers():
    offers = []

    try:
        total_users = contract.functions.getTotalUsers().call()
        print(f"🔍 Found {total_users} users in contract")

        for i in range(total_users):
            user_data = contract.functions.getUserByIndex(i).call()

            user_id = user_data[0]
            role = user_data[1]
            energy = user_data[2]
            price = user_data[3]

            if role != "N_A":
                offer = Offer(user_id, role, energy, price)
                offers.append(offer)

    except Exception as e:
        print(f"⚠️ Error fetching offers: {e}")

    return offers

# === Debug Usage ===
if __name__ == "__main__":
    all_offers = fetch_active_offers()
    for o in all_offers:
        print(f"{o.role.upper()}: ID={o.id}, Energy={o.energy}, Price={o.price}")
