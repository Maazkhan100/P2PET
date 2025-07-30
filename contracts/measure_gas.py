#!/usr/bin/env python3
"""
measure_gas.py – Deploy P2PEnergyTrading locally and log gas usage
"""
import json, csv, time
from pathlib import Path
from web3 import Web3
from web3.middleware import geth_poa_middleware

# ───── CONFIG ───────────────────────────────────────────────────────────
NODE_URL   = "http://127.0.0.1:22000"      # first local validator
CHAIN_ID   = 10
SENDER_PK  = "0x5741c136445b9ca22ebe0b57dcad474b54e4dda2dc7882d13a11db85a0be50d7"    # By running the extract_private_key.py file
ABI        = json.loads(Path("abi.json").read_text())
BYTECODE   = Path("bytecode.txt").read_text().strip()
CSV_OUT    = "gas_report.csv"
# ────────────────────────────────────────────────────────────────────────

w3 = Web3(Web3.HTTPProvider(NODE_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
acct = w3.eth.account.from_key(SENDER_PK)

def send(tx):
    tx["nonce"] = w3.eth.get_transaction_count(acct.address)
    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.gasUsed

def deploy():
    c = w3.eth.contract(abi=ABI, bytecode=BYTECODE)
    gas = send(c.constructor().build_transaction({
        "from": acct.address,
        "gas": 8000000,      # manually set gas limit
        "gasPrice": 0,       # required for Quorum
        "chainId": CHAIN_ID,
    }))
    addr = w3.eth.get_transaction_receipt(w3.eth.get_block("latest").transactions[-1]).contractAddress
    return gas, w3.eth.contract(address=addr, abi=ABI)

def log(csv_writer, fn, label, *args):
    tx = fn(*args).build_transaction({
        "from": acct.address,
        "gas": 8000000,
        "gasPrice": 0,
        "chainId": CHAIN_ID,
    })
    gas = send(tx)
    csv_writer.writerow([label, gas])
    print(f"{label:32s} {gas:>10,}")

def main():
    with open(CSV_OUT, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["Function", "GasUsed"])

        dep_gas, contract = deploy()
        w.writerow(["constructor", dep_gas])
        print(f"{'constructor':32s} {dep_gas:>10,}")

        # ── Sample calls ──────────────────────────────
        log(w, contract.functions.submitData,        "submitData (new slot)", 1, 50, 20)
        log(w, contract.functions.submitData,        "submitData (same slot)",1, 60, 22)
        log(w, contract.functions.advancePhase,      "advancePhase",)
        log(w, contract.functions.submitExecutionResult,
                                               "submitExecutionResult", Web3.keccak(text="dummy"))
        log(w, contract.functions.verifyExecutionResult,
                                               "verifyExecutionResult")
        # …add more as needed …
    print(f"\nCSV saved → {CSV_OUT}")

if __name__ == "__main__":
    main()
