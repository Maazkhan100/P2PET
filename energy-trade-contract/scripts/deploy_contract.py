from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import os

# Connect to Raspberry Pi node
w3 = Web3(Web3.HTTPProvider("http://192.168.0.111:22000"))

# Inject PoA middleware
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

assert w3.is_connected(), "Not connected to RPC"

# Load ABI and bytecode
with open("../compiled/EnergyTrade_abi.json") as f:
    abi = json.load(f)

with open("../compiled/EnergyTrade_bytecode.txt") as f:
    bytecode = f.read()

# Use first available account
account = w3.eth.accounts[0]
w3.eth.default_account = account

# Deploy contract
EnergyTrade = w3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = EnergyTrade.constructor().transact()
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

# Save contract address
os.makedirs("../deployed", exist_ok=True)
with open("../deployed/contract_address.txt", "w") as f:
    f.write(tx_receipt.contractAddress)

print(f"Contract deployed at: {tx_receipt.contractAddress}")
