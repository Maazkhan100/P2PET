import os
from os import system as shellRun
from functions import *
import sys

# Set default to Raspberry Pi execution unless specified
if len(sys.argv) > 1:
    is_raspberrypi = int(sys.argv[1])
else:
    is_raspberrypi = 1

# List of specific Raspberry Pi nodes to run the blockchain on
nodes_to_run = [2, 3, 4, 5]
# nodes_to_run = [1, 2, 3, 4]

# Mapping of node number to IP addresses
ip_dict = {
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

assert len(nodes_to_run) > 0

# Map real node index to virtual local indices (e.g., [2, 3, 5] → {0: 2, 1: 3, 2: 5})
index_to_node = {i: node for i, node in enumerate(nodes_to_run)}
node_to_index = {node: i for i, node in enumerate(nodes_to_run)}

# Create node folders
for i in range(len(nodes_to_run)):
    shellRun(f"mkdir -p node{i}")

# Setup Istanbul with number of validators
os.chdir("node0")
shellRun(f"istanbul setup --num {len(nodes_to_run)} --nodes --quorum --save --verbose >> istanbul.log")
get_data_from_istanbul("istanbul.log")
shellRun("mv validators.log ../")
shellRun("mv dummy-genesis.json ../")
shellRun("mv dummy-static-nodes.json ../")
os.chdir("..")

# Update IPs in static-nodes.json
ip_subset = {i+1: ip_dict[node] for i, node in enumerate(nodes_to_run)}
update_port_numbers("dummy-static-nodes.json", ip_subset, is_raspberrypi)

# Create accounts
acc_passwd = "12345"
for i in range(len(nodes_to_run)):
    shellRun(f"mkdir -p node{i}/data/geth")
    create_account(acc_passwd, f"node{i}/data", i)
    with open(f"node{i}/data/password.txt", "w") as pw_file:
        pw_file.write(acc_passwd)

# Update genesis with public keys
public_addr_dict = extract_acc_public_keys("geth_accounts_info.log")
balance = "0x446c3b15f9926687d2c40534fdb564000000000000"
for i in range(len(nodes_to_run)):
    insert_in_json("node0/genesis.json", "alloc", public_addr_dict[i], balance)

# Distribute genesis & static-nodes
for i in range(len(nodes_to_run)):
    shellRun(f"cp -Rn node0/genesis.json node{i}")
    shellRun(f"cp -Rn dummy-static-nodes.json node{i}/data/static-nodes.json")
    shellRun(f"cp -Rn node0/{i}/nodekey node{i}/data/geth")
    shellRun(f"rm -rf node{i}/static-nodes.json")

# Initialize nodes
for i in range(len(nodes_to_run)):
    os.chdir(f"node{i}")
    shellRun("geth --datadir data init genesis.json")
    os.chdir("..")

# Starting up nodes
rpc_port_num = 22000
port_num = 30300
pi_password = 'Lums12345'

for i in range(len(nodes_to_run)):
    node_number = index_to_node[i]
    start_node_file = open(f"startnode{i}.sh", "w")

    unlock_addr = public_addr_dict[i]

    if is_raspberrypi:
        final_command = (
        f"PRIVATE_CONFIG=ignore /usr/local/quorum_bins/geth "
        f"--datadir data --nodiscover --istanbul.blockperiod 60 --syncmode full "
        f"--mine --miner.threads 1 --verbosity 5 --networkid 10 "
        f"--http --http.addr {ip_dict[node_number]} --http.port {rpc_port_num} "
        f"--http.api admin,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,istanbul "
        f"--emitcheckpoints --allow-insecure-unlock "
        f"--unlock {unlock_addr} --password data/password.txt "
        f"--port {port_num} 2>>node{i}.log &"
    )
    else:
        final_command = (
        f"PRIVATE_CONFIG=ignore /usr/local/quorum_bins/geth "
        f"--datadir data --nodiscover --istanbul.blockperiod 60 --syncmode full "
        f"--mine --miner.threads 1 --verbosity 5 --networkid 10 "
        f"--http --http.addr 127.0.0.1 --http.port {rpc_port_num} "
        f"--http.api admin,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,istanbul "
        f"--http.corsdomain https://remix.ethereum.org "
        f"--emitcheckpoints --allow-insecure-unlock "
        f"--unlock {unlock_addr} --password data/password.txt "
        f"--port {port_num} 2>>node{i}.log &"
    )

    start_node_file.write(final_command)
    start_node_file.close()

    shellRun(f"chmod +x startnode{i}.sh")
    shellRun(f"mv startnode{i}.sh node{i}/startnode{i}.sh")

    if is_raspberrypi:
        try:
            execute_remotely(["cd ~", "cd block-chain-network", "./del_junk.sh", "./del_junk.sh"], "pi", ip_dict[node_number], pi_password)
            command = f"scp -r node{i}/ pi@{ip_dict[node_number]}:/home/pi/block-chain-network"
            prompt_expected = f"pi@{ip_dict[node_number]}'s password: "
            scp_distribution(command, prompt_expected, pi_password)
            execute_remotely(["cd ~", f"cd block-chain-network/node{i}", f"./startnode{i}.sh"], "pi", ip_dict[node_number], pi_password)
        except:
            shellRun("./del_junk.sh")
            raise ConnectionError(f"Raspberry Pi node {node_number} is off/not accessible!")
    else:
        shellRun(f"cd node{i} && ./startnode{i}.sh")

    rpc_port_num += 1
    port_num += 1

# Cleanup
shellRun("rm -rf dummy-genesis.json")
shellRun("rm -rf dummy-static-nodes.json")
