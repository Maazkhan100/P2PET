from web3 import Web3
import os
from decrypt import decrypt_aes128
import subprocess

def get_contract_addr(
	bytecode: str,
	abi: list,
	node_url: str = "http://192.168.0.152:22000",
	chain_id: int = 10
):

    """
    This functions takes bytecode and abi of a solidity smart contract and deploy it on given
    node/peer with url node_url and chain id as chain_id

    bytecode: hex bytecode string (no 0x at the start)
    abi: abi of smart contract (list)
    node_url: rpc url (string)
    chain_id: chain id of blockchain (integer)
    """

    try:
        # ===================== Establishing the connection with the network =====================
        w3 = Web3(Web3.HTTPProvider(node_url))

        # get absolute path to UTC file of the node
        directory      = "../node0/data/keystore"
        files          = os.listdir(directory)
        file_name      = files[0]
        file_path      = os.path.join(directory, file_name)
        absolute_path  = subprocess.check_output(["readlink", "-f", file_path], text=True).strip()
        utc_file       = absolute_path
        account_addr   = '0x' + utc_file.split("--")[2]
        account_addr   = Web3.to_checksum_address(account_addr)

        encryption_file = utc_file
        acc_passwd      = "12345"
        private_key     = decrypt_aes128(encryption_file, acc_passwd)

        # ===================== Instantiate the contract =====================
        SmartContract = w3.eth.contract(abi=abi, bytecode=bytecode)

        nonce = w3.eth.get_transaction_count(account_addr)

        # ===================== Set up transaction from constructor =====================
        tx = SmartContract.constructor().build_transaction(
            {
                "chainId": chain_id,
                "gasPrice": w3.eth.gas_price,
                "from": account_addr,
                "nonce": nonce,
            }
        )

        signed_tx  = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash    = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        return account_addr, private_key, nonce, tx_receipt

    except Exception as e:
        print(f"{e}")
        exit(1)
