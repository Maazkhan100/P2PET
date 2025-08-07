# THIS IS NOT FUNCTIONAL AND NOT TESTED YET.

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from functions import execute_remotely, scp_distribution  # reuse your helpers if needed

# === CONFIGURATION ===
# 0 is laptop; 1.. are Pis. Adjust list to your desired participating nodes.
nodes_to_run = [0, 2, 3, 4]

# Mapping node number to reachable IPs (used to rewrite enode host part)
ip_dict = {
    0: "127.0.0.1",           # laptop (bind locally)
    1: '192.168.0.154',
    2: '192.168.0.111',
    3: '192.168.0.167',
    4: '192.168.0.137',
    5: '192.168.0.192',
    6: '192.168.0.152',
    7: '192.168.0.170',
    8: '192.168.0.133',
    9: '192.168.0.110',
    10: '192.168.0.152'
}

PI_USER = "pi"
PI_PASSWORD = "Lums12345"  # used if you rely on password flows (your helpers use sshpass)
PUBLIC_INFO_DIR = "public_info"  # on coordinator to collect agent JSONs
GENESIS_FILE = "genesis.json"
STATIC_NODES_FILE = "static-nodes.json"
ACCOUNT_PASSWORD = "12345"

# === UTILITIES ===

def sh(cmd, check=True, capture_output=False):
    result = subprocess.run(cmd, shell=True, check=check, text=True,
                            capture_output=capture_output)
    return result.stdout if capture_output else None

def build_istanbul_genesis(validators, chain_id=10, gas_limit="0xE0000000"):
    """
    Build minimal Istanbul BFT genesis with the list of validator addresses.
    extraData = 32 bytes vanity + concatenated validator addresses (20 bytes each) + 65 bytes of zero.
    """
    def canonical_addr(addr):
        a = addr.lower()
        if a.startswith("0x"):
            a = a[2:]
        if len(a) != 40:
            raise ValueError(f"Invalid address length: {addr}")
        return bytes.fromhex(a)

    vanity = bytes(32)
    validators_bytes = b"".join(canonical_addr(v) for v in validators)
    seal = bytes(65)
    extra_data = vanity + validators_bytes + seal
    extra_data_hex = "0x" + extra_data.hex()

    genesis = {
        "config": {
            "chainId": chain_id,
            "homesteadBlock": 0,
            "eip150Block": 0,
            "eip155Block": 0,
            "eip158Block": 0,
            "istanbul": {
                "epoch": 30000,
                "policy": 0
            },
            "isQuorum": True
        },
        "difficulty": "0x1",
        "gasLimit": gas_limit,
        "alloc": {},
        "extraData": extra_data_hex,
        "nonce": "0x0",
        "timestamp": "0x5c51a607",
        "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000000"
    }

    # Prefund validators so they have balance
    for addr in validators:
        genesis["alloc"][addr] = {"balance": "0x446c3b15f9926687d2c40534fdb564000000000000"}

    return genesis

def get_enode_and_address(ip_for_enode, rpc_port, datadir):
    """
    Launch a temporary geth instance to fetch enode and the first account (if any).
    Returns (enode, account_address)
    """
    # Ensure datadir exists
    Path(datadir).mkdir(parents=True, exist_ok=True)
    # Start geth in background with minimal flags; it will auto-create nodekey if absent.
    log_file = f"tmp_geth_{rpc_port}.log"
    cmd = (
        f"PRIVATE_CONFIG=ignore /usr/local/quorum_bins/geth "
        f"--datadir {datadir} --nodiscover --syncmode full "
        f"--http --http.addr {ip_for_enode} --http.port {rpc_port} "
        f"--http.api admin,personal,eth,net,web3 --verbosity 3 "
        f"--port 0 2>>{log_file} &"
    )
    sh(cmd)
    # Wait for RPC to be responsive
    time.sleep(5)

    # Retrieve enode
    enode = None
    address = None
    try:
        enode_raw = sh(f"echo 'admin.nodeInfo.enode' | geth attach http://{ip_for_enode}:{rpc_port}", capture_output=True)
        enode = enode_raw.strip().strip('"').strip("'")
    except Exception:
        pass

    # Retrieve account (if created already)
    try:
        accounts_raw = sh(f"echo 'eth.accounts' | geth attach http://{ip_for_enode}:{rpc_port}", capture_output=True)
        accounts = json.loads(accounts_raw.replace("'", '"'))
        if accounts:
            address = accounts[0]
    except Exception:
        pass

    # Kill the temporary geth (simplest rough method)
    sh(f"pkill -f '--datadir {datadir}' || true", check=False)
    time.sleep(1)
    return enode, address

# === AGENT (each node including laptop if not in pure coordinator-only run) ===

def agent_mode(local_node_number, coordinator_host):
    """
    Run on each participant. Generates its own account/nodekey, fetches enode+address,
    and sends public info to coordinator.
    """
    print(f"[Agent {local_node_number}] Starting agent.")

    # Prepare own node directory
    Path("node/data/geth").mkdir(parents=True, exist_ok=True)

    # Create account locally (encrypted keystore)
    pwd_file = Path("node/data/password.txt")
    pwd_file.write_text(ACCOUNT_PASSWORD)
    sh(f"geth --datadir node/data account new --password node/data/password.txt")

    # Determine IP to bind for enode discovery
    if local_node_number == 0:
        ip_for_enode = "127.0.0.1"
    else:
        ip_for_enode = ip_dict.get(local_node_number)
    rpc_port = 22000 + local_node_number

    # Get enode and public address; may need to retry a couple times if slow
    enode = None
    address = None
    for attempt in range(5):
        enode, address = get_enode_and_address(ip_for_enode, rpc_port, "node/data")
        if enode and address:
            break
        time.sleep(2)
    if not enode or not address:
        print(f"[Agent {local_node_number}] FAILED to get enode or address. enode={enode}, address={address}")
        sys.exit(1)

    # Replace host in enode with correct advertised IP
    if "@" in enode:
        prefix, rest = enode.split("@", 1)
        # Keep port from original; replace host with ip_dict entry
        hostport_and_rest = rest
        if "/" in rest:
            hostport, suffix = rest.split("/", 1)
            port = hostport.split(":")[1] if ":" in hostport else "30303"
            advertised_ip = ip_dict.get(local_node_number, "127.0.0.1")
            enode = f"{prefix}@{advertised_ip}:{port}/{suffix}"
        else:
            # no suffix
            if ":" in rest:
                port = rest.split(":")[1]
            else:
                port = "30303"
            advertised_ip = ip_dict.get(local_node_number, "127.0.0.1")
            enode = f"{prefix}@{advertised_ip}:{port}"

    print(f"[Agent {local_node_number}] Enode: {enode}")
    print(f"[Agent {local_node_number}] Address: {address}")

    # Persist public info locally
    info = {"enode": enode, "address": address}
    filename = f"node_{local_node_number}.json"
    with open(filename, "w") as f:
        json.dump(info, f, indent=2)

    # Send to coordinator (assumes SSH available)
    if local_node_number != 0:
        print(f"[Agent {local_node_number}] Sending public info to coordinator at {coordinator_host}")
        # Ensure remote directory exists
        sh(f"ssh {PI_USER}@{coordinator_host} 'mkdir -p ~/{PUBLIC_INFO_DIR}'")
        sh(f"scp {filename} {PI_USER}@{coordinator_host}:~/{PUBLIC_INFO_DIR}/")
    else:
        # laptop acting as its own agent: move file into its own public_info dir
        Path(PUBLIC_INFO_DIR).mkdir(exist_ok=True)
        sh(f"mv {filename} {PUBLIC_INFO_DIR}/")

    print(f"[Agent {local_node_number}] Done. Waiting for coordinator to distribute genesis/static.")

    # Wait up to some time for genesis/static to appear (coordinator will drop them)
    for _ in range(60):
        if Path(GENESIS_FILE).exists() and Path(STATIC_NODES_FILE).exists():
            break
        time.sleep(2)
    else:
        print(f"[Agent {local_node_number}] Timeout waiting for genesis/static from coordinator.")
        sys.exit(1)

    # Copy those into own node structure
    Path("node").mkdir(exist_ok=True)
    sh(f"cp {GENESIS_FILE} node/")
    sh("mkdir -p node/data")
    sh(f"cp {STATIC_NODES_FILE} node/data/static-nodes.json")

    # Initialize locally
    sh("cd node && geth --datadir data init genesis.json")

    # Write uniform startnode.sh
    rpc_port = 22000 + local_node_number
    swarm_port = 30300 + local_node_number
    http_addr = "127.0.0.1" if local_node_number == 0 else ip_dict.get(local_node_number)
    start_cmd = (
        f"PRIVATE_CONFIG=ignore /usr/local/quorum_bins/geth "
        f"--datadir data --nodiscover --istanbul.blockperiod 60 --syncmode full "
        f"--mine --miner.threads 1 --verbosity 5 --networkid 10 "
        f"--http --http.addr {http_addr} --http.port {rpc_port} "
        f"--http.api admin,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,istanbul "
        f"--emitcheckpoints "
        f"--port {swarm_port} 2>>node.log &"
    )
    with open("node/startnode.sh", "w") as f:
        f.write(start_cmd + "\n")
    sh("chmod +x node/startnode.sh")
    # Start node
    sh("cd node && ./startnode.sh")
    print(f"[Agent {local_node_number}] Node started.")

# === COORDINATOR ===

def coordinator_mode():
    """
    Run on coordinator (laptop). Collect public info from all nodes, build genesis and static-nodes,
    distribute back, and trigger initialization/start.
    """
    print("[Coordinator] Starting coordinator.")
    Path(PUBLIC_INFO_DIR).mkdir(exist_ok=True)

    # Ensure coordinator also has its public info (agent mode behavior) before collecting
    if not Path(f"{PUBLIC_INFO_DIR}/node_0.json").exists():
        print("[Coordinator] Generating own public identity (node 0) as agent.")
        agent_mode(0, coordinator_host=ip_dict[0])

    # Wait for all public info files
    expected = set(nodes_to_run)
    collected = {}
    timeout = 180
    start = time.time()
    while True:
        for node in list(expected):
            fpath = Path(PUBLIC_INFO_DIR) / f"node_{node}.json"
            if fpath.exists():
                data = json.loads(fpath.read_text())
                if "enode" in data and "address" in data:
                    collected[node] = data
                    expected.discard(node)
        if not expected:
            break
        if time.time() - start > timeout:
            raise TimeoutError(f"[Coordinator] Timeout waiting for nodes: {expected}")
        time.sleep(2)

    print(f"[Coordinator] Collected public info from nodes: {sorted(collected.keys())}")

    # Build static-nodes list (ensure enode host part matches ip_dict)
    static_nodes = []
    validators = []
    for node in sorted(collected.keys()):
        enode = collected[node]["enode"]
        address = collected[node]["address"]
        # If enode host part is not the desired IP, replace it
        if "@" in enode:
            prefix, rest = enode.split("@", 1)
            if "/" in rest:
                hostport, suffix = rest.split("/", 1)
                if ":" in hostport:
                    port = hostport.split(":", 1)[1]
                else:
                    port = "30303"
                advertised_ip = ip_dict.get(node, "127.0.0.1")
                enode = f"{prefix}@{advertised_ip}:{port}/{suffix}"
            else:
                if ":" in rest:
                    port = rest.split(":", 1)[1]
                else:
                    port = "30303"
                advertised_ip = ip_dict.get(node, "127.0.0.1")
                enode = f"{prefix}@{advertised_ip}:{port}"
        static_nodes.append(enode)
        validators.append(address)

    # Build genesis.json
    genesis = build_istanbul_genesis(validators)
    with open(GENESIS_FILE, "w") as f:
        json.dump(genesis, f, indent=2)
    with open(STATIC_NODES_FILE, "w") as f:
        json.dump(static_nodes, f, indent=2)

    print("[Coordinator] Created genesis.json and static-nodes.json.")

    # Distribute to all nodes
    for node in sorted(collected.keys()):
        if node == 0:
            # local copy already happens inside agent if it was run; ensure presence
            sh(f"cp {GENESIS_FILE} node/")
            sh(f"mkdir -p node/data")
            sh(f"cp {STATIC_NODES_FILE} node/data/static-nodes.json")
        else:
            # send to remote
            print(f"[Coordinator] Sending genesis/static to node {node}")
            sh(f"scp {GENESIS_FILE} {PI_USER}@{ip_dict[node]}:/home/{PI_USER}/P2PET/node/")
            sh(f"scp {STATIC_NODES_FILE} {PI_USER}@{ip_dict[node]}:/home/{PI_USER}/P2PET/node/data/static-nodes.json")

    print("[Coordinator] Distribution complete.")

    # Trigger init & start remotely and locally
    for node in sorted(collected.keys()):
        if node == 0:
            sh("cd node && geth --datadir data init genesis.json")
            # start script already created by agent
            sh("cd node && ./startnode.sh")
        else:
            sh(f"ssh {PI_USER}@{ip_dict[node]} 'cd ~/P2PET/node && geth --datadir data init genesis.json'")
            # create and run start script remotely
            rpc_port = 22000 + node
            swarm_port = 30300 + node
            http_addr = ip_dict[node]
            remote_cmd = (
                f"PRIVATE_CONFIG=ignore /usr/local/quorum_bins/geth "
                f"--datadir data --nodiscover --istanbul.blockperiod 60 --syncmode full "
                f"--mine --miner.threads 1 --verbosity 5 --networkid 10 "
                f"--http --http.addr {http_addr} --http.port {rpc_port} "
                f"--http.api admin,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,istanbul "
                f"--emitcheckpoints "
                f"--port {swarm_port} 2>>node.log &"
            )
            # Write remote startnode.sh
            sh(f"ssh {PI_USER}@{ip_dict[node]} 'cat <<\"EOF\" > ~/P2PET/node/startnode.sh\n{remote_cmd}\nEOF'")
            sh(f"ssh {PI_USER}@{ip_dict[node]} 'chmod +x ~/P2PET/node/startnode.sh && cd ~/P2PET/node && ./startnode.sh'")

    print("[Coordinator] All nodes should be up (check logs).")

# === ENTRY POINT ===

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Decentralized Pattern A validator bootstrap")
    parser.add_argument("--coordinator", action="store_true", help="Run coordinator (build genesis, collect public info)")
    parser.add_argument("--node-number", type=int, required=True, help="Local node number (0 for laptop, 1+ for Pis)")
    parser.add_argument("--coordinator-host", type=str, default=None, help="Hostname/IP of coordinator (laptop). If omitted, assumes node 0 is local.")
    args = parser.parse_args()

    if args.node_number not in nodes_to_run:
        print(f"Node number {args.node_number} not in configured nodes_to_run: {nodes_to_run}")
        sys.exit(1)

    coordinator_host = args.coordinator_host if args.coordinator_host else ip_dict[0]

    if args.coordinator:
        # First ensure local agent ran to supply its identity
        agent_mode(0, coordinator_host)
        coordinator_mode()
    else:
        agent_mode(args.node_number, coordinator_host)

if __name__ == "__main__":
    main()
