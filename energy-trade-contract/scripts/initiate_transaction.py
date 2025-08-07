#!/usr/bin/env python3
import os, time
import json
import eth_utils
import eth_abi
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from dotenv import load_dotenv
from decrypt_key import get_private_key

# Load .env
load_dotenv()

# Load config from .env
RPC_URL = os.getenv("RPC_URL")
ABI_PATH = os.getenv("ABI_PATH")
CONTRACT_ADDRESS_PATH = os.getenv("CONTRACT_ADDRESS_PATH")

if not RPC_URL or not ABI_PATH or not CONTRACT_ADDRESS_PATH:
    raise ValueError("One or more required environment variables are missing.")

# Read deployed contract address
with open(CONTRACT_ADDRESS_PATH, "r") as f:
    CONTRACT_ADDRESS = f.read().strip()

# Connect to Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Set up account
account = w3.eth.account.from_key(get_private_key())
sender_address = account.address

# Load ABI
with open(ABI_PATH, "r") as f:
    abi = json.load(f)

# To print the actual when phase change transaction is sent to the network
PHASE_NAMES = {
    0: "DataSubmission",
    1: "Execution",
    2: "Trading",
}

# Contract instance
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)

def extract_revert_reason(call_obj, block_identifier=None):
    try:
        w3.eth.call(call_obj, block_identifier=block_identifier)
        return None
    except Exception as e:
        error_data = None
        if hasattr(e, "args") and len(e.args) > 0:
            info = e.args[0]
            if isinstance(info, dict):
                # Geth-style nested data
                for v in info.get("data", {}).values():
                    error_data = v.get("return", None) or v.get("data", None) or v
            else:
                msg = str(info)
                hex_parts = [part for part in msg.split() if part.startswith("0x")]
                if hex_parts:
                    error_data = hex_parts[-1]
        if not error_data:
            return f"Could not extract error data: {e}"

        try:
            data_bytes = eth_utils.to_bytes(hexstr=error_data)
            # Standard Error(string) selector
            if data_bytes[:4] == eth_utils.to_bytes(hexstr="0x08c379a0"):
                # skip selector + offset (32) then decode
                # ABI.decode_single expects the full encoded payload after selector
                reason = eth_abi.decode_single("string", data_bytes[4 + 32 :])
                return reason
            else:
                return f"Non-standard revert data: {error_data}"
        except Exception as parse_err:
            return f"Failed to decode revert reason: {parse_err} / raw: {error_data}"

def send_transaction(function_call):
    nonce = w3.eth.get_transaction_count(sender_address, block_identifier='pending')
    tx = function_call.build_transaction({
        'from': sender_address,
        'nonce': nonce,
        'gas': 500000,
        'gasPrice': 0  # Quorum typically ignores gasPrice
    })

    signed_tx = w3.eth.account.sign_transaction(tx, get_private_key())
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    print(f"Transaction sent: {tx_hash.hex()} — waiting for confirmation...")

    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status == 1:
            print("Transaction successful.")
        else:
            print("Transaction failed (reverted).")
            # Try to extract revert reason by simulating the call at that block
            call_obj = {
                "to": tx["to"],
                "data": tx["data"],
                "from": tx["from"],
            }
            reason = extract_revert_reason(call_obj, block_identifier=receipt.blockNumber)
            print("Revert reason:", reason)
        return receipt
    except Exception as e:
        print(f"Error while waiting for receipt: {e}")
        return None

def register():
    print("Registering participant...")
    receipt = send_transaction(contract.functions.register())
    if receipt:
        print(f"Registration TX hash: {receipt.transactionHash.hex()}")

def submit_data(role: int, energy: int, price_wei: int):
    print("Submitting energy data...")
    receipt = send_transaction(contract.functions.submitData(role, energy, price_wei))
    if receipt:
        print(f"Data Submission TX hash: {receipt.transactionHash.hex()}")

def hash_participants():
    print("Hashing participants list...")
    receipt = send_transaction(contract.functions.hashParticipantsList())
    if receipt:
        print(f"Hashed Participants TX hash: {receipt.transactionHash.hex()}")

def advance_phase():
    print("Advancing to next phase...")
    receipt = send_transaction(contract.functions.advancePhase())
    if not receipt:
        print("No receipt; something went wrong.")
        return
    tx_hash = receipt.transactionHash.hex()
    print(f"Advance Phase TX hash: {tx_hash}")

    if receipt.status != 1:
        print("advancePhase transaction reverted; phase not changed.")
        return

    # Read the updated phase and round
    try:
        current_phase_raw = contract.functions.currentPhase().call()
        current_round = contract.functions.currentRound().call()
        phase_name = PHASE_NAMES.get(current_phase_raw, f"Unknown({current_phase_raw})")
        print(f"Phase changed to {phase_name}, round {current_round}.")
    except Exception as e:
        print("Failed to read updated phase/round:", e)

def verify_execution():
    print("Sending verifyExecutionResult transaction...")
    receipt = send_transaction(contract.functions.verifyExecutionResult())
    if not receipt:
        print("No receipt; something went wrong with sending.")
        return
    if receipt.status != 1:
        print("verifyExecutionResult transaction reverted.")
        return

    # Read back the stored result (state was updated by the successful tx)
    try:
        maj_h, verified = contract.functions.verifyExecutionResult().call({'from': sender_address})
        print(f"Final hash: majorityHash={maj_h.hex()}, isVerified={verified}")
    except Exception as e:
        print("Failed to read back result:", e)

SCALING_FACTOR = 100  # For 2 decimal places (e.g., 0.75 to 75)
def scale(value):
    return int(value * SCALING_FACTOR)

if __name__ == "__main__":
    try:
        # Example flow; adapt/order as needed
        # register()
        # submit_data(role=2, energy=scale(100), price_wei=scale(10))
        # submit_data(role=2, energy=scale(90), price_wei=scale(15))
        # submit_data(role=1, energy=scale(95), price_wei=scale(20))
        # submit_data(role=1, energy=scale(105), price_wei=scale(25))
        # hash_participants()
        advance_phase()  # move into Execution phase
        # verify_execution()
    except Exception as e:
        print(f"Error occurred: {e}")
