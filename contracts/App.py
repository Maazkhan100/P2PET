import sys
import os
from flask import Flask, request, jsonify, render_template
from web3 import Web3
from get_contract_addr import get_contract_addr

app = Flask(__name__)

# ========== Blockchain Config ==========
NODE_URL = "http://192.168.0.111:22000"
CHAIN_ID = 10
CONTRACT_ADDRESS_FILE = "contract_address.txt"

web3 = Web3(Web3.HTTPProvider(NODE_URL))
if not web3.is_connected():
    raise ConnectionError("Failed to connect to Ethereum node.")

# ========== Contract Info ==========
ABI = [ ]  # Insert your contract's ABI
BYTECODE = ""  # Insert your contract's bytecode

contract = None
account_addr = None
private_key = None
contract_address = None

# ========== Determine Mode ==========
mode = None
if len(sys.argv) > 1:
    mode = sys.argv[1].lower()

if mode == "deploy":
    print("[MODE] Forcing deployment...")
    account_addr, private_key, nonce, tx_receipt = get_contract_addr(BYTECODE, ABI, node_url=NODE_URL, chain_id=CHAIN_ID)
    contract_address = tx_receipt.contractAddress
    with open(CONTRACT_ADDRESS_FILE, "w") as f:
        f.write(contract_address)
    print(f"[INFO] Contract deployed at: {contract_address}")

elif mode == "use":
    print("[MODE] Using existing contract address from file...")
    if not os.path.exists(CONTRACT_ADDRESS_FILE):
        raise FileNotFoundError("Contract address file not found. Run in 'deploy' mode first.")
    with open(CONTRACT_ADDRESS_FILE, "r") as f:
        contract_address = f.read().strip()
    # Set your credentials manually
    account_addr = "0xYourAccountAddress"
    private_key = "0xYourPrivateKey"

else:
    print("[MODE] Auto-detecting mode...")
    if os.path.exists(CONTRACT_ADDRESS_FILE):
        print("[AUTO] Found contract address file. Using existing contract.")
        with open(CONTRACT_ADDRESS_FILE, "r") as f:
            contract_address = f.read().strip()
        # Set your credentials manually
        account_addr = "0xYourAccountAddress"
        private_key = "0xYourPrivateKey"
    else:
        print("[AUTO] No address file found. Deploying new contract...")
        account_addr, private_key, nonce, tx_receipt = get_contract_addr(BYTECODE, ABI, node_url=NODE_URL, chain_id=CHAIN_ID)
        contract_address = tx_receipt.contractAddress
        with open(CONTRACT_ADDRESS_FILE, "w") as f:
            f.write(contract_address)
        print(f"[INFO] Contract deployed at: {contract_address}")

# ========== Build Contract Instance ==========
contract = web3.eth.contract(address=contract_address, abi=ABI)

# ========== Flask Routes ==========
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/submit_trade", methods=["POST"])
def submit_trade():
    data = request.json
    role = data["role"]
    sender = web3.to_checksum_address(data["sender"])
    energy = int(data["energy"]) if role != "N/A" else 0
    price = int(data["price"]) if role != "N/A" else 0
    nonce = web3.eth.get_transaction_count(sender)

    if role == "buyer":
        txn = contract.functions.submitBid(energy, price).build_transaction({
            "from": sender,
            "gasPrice": web3.eth.gas_price,
            "nonce": nonce,
        })
    elif role == "seller":
        txn = contract.functions.submitOffer(energy, price).build_transaction({
            "from": sender,
            "gasPrice": web3.eth.gas_price,
            "nonce": nonce,
        })
    elif role == "N/A":
        return jsonify({"message": "No trade submitted for N/A role"}), 200
    else:
        return jsonify({"error": "Invalid role"}), 400

    signed_txn = web3.eth.account.sign_transaction(txn, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"[INFO] Trade submitted: {web3.to_hex(tx_hash)}")
    return jsonify({"message": "Trade submitted", "tx_hash": web3.to_hex(tx_hash)})

@app.route("/execute_trades", methods=["POST"])
def execute_trades():
    sender = account_addr
    nonce = web3.eth.get_transaction_count(sender)
    txn = contract.functions.matchTrades().build_transaction({
        "from": sender,
        "gasPrice": web3.eth.gas_price,
        "nonce": nonce,
    })

    signed_txn = web3.eth.account.sign_transaction(txn, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"[INFO] Trades executed: {web3.to_hex(tx_hash)}")
    return jsonify({"message": "Trades executed", "tx_hash": web3.to_hex(tx_hash)})

@app.route("/run_rounds", methods=["POST"])
def run_rounds():
    rounds = int(request.json.get("rounds", 1))
    sender = account_addr

    for i in range(rounds):
        nonce = web3.eth.get_transaction_count(sender)
        txn = contract.functions.matchTrades().build_transaction({
            "from": sender,
            "gasPrice": web3.eth.gas_price,
            "nonce": nonce,
        })
        signed_txn = web3.eth.account.sign_transaction(txn, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"[INFO] Round {i+1} executed: {web3.to_hex(tx_hash)}")

    return jsonify({"message": f"{rounds} rounds executed successfully"})

# ========== Run Server ==========
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
