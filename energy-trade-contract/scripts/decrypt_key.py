import json
import os
from eth_account import Account
from dotenv import load_dotenv

import subprocess

def scp_distribution(
    node_hosts,
    files_to_send,
    remote_base_dir="~/P2PET"
):
    """
    Distributes given files to Pi nodes using scp and SSH host aliases.

    Args:
        node_hosts (list): List of hostnames or aliases defined in ~/.ssh/config.
        files_to_send (list): List of local file paths to copy.
        remote_base_dir (str): Destination base directory on remote node.
    """
    failed_nodes = []

    for host in node_hosts:
        print(f"Sending files to {host}...")
        for local_file in files_to_send:
            if "compiled" in local_file:
                remote_path = f"{remote_base_dir}/compiled/"
            elif "deployed" in local_file:
                remote_path = f"{remote_base_dir}/deployed/"
            else:
                print(f"Skipping unrecognized path: {local_file}")
                continue

            try:
                subprocess.run(
                    ["scp", local_file, f"{host}:{remote_path}"],
                    check=True
                )
                print(f"Sent {local_file} to {host}:{remote_path}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to send {local_file} to {host}: {e}")
                failed_nodes.append(host)

    if failed_nodes:
        print("\nThe following nodes failed:")
        for host in failed_nodes:
            print(f" - {host}")

def get_private_key():
    # Load environment variables
    load_dotenv()

    KEYSTORE_PATH = os.getenv("KEYSTORE_PATH")
    ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")

    if not KEYSTORE_PATH or not ACCOUNT_PASSWORD:
        raise ValueError("Missing KEYSTORE_PATH or ACCOUNT_PASSWORD in environment variables.")

    # Read keystore file
    with open(KEYSTORE_PATH, "r") as f:
        keystore = json.load(f)

    # Decrypt private key
    try:
        private_key_bytes = Account.decrypt(keystore, ACCOUNT_PASSWORD)
        private_key_hex = private_key_bytes.hex()
        return private_key_hex
    except Exception as e:
        raise ValueError(f"Failed to decrypt private key: {str(e)}")
