
import os
from os import system as shellRun
from functions import *
import sys

if (len(sys.argv) > 1): # to exclude the file name
    is_raspberrypi = int(sys.argv[1])
else:
    is_raspberrypi = 1  # run on Raspberry Pi nodes by default

# number of validator nodes initially
initial_validators = 2

# Local static ip addresses of raspberry pis
ip_dict = {1: '192.168.0.152', 2: '192.168.0.111', 3: '192.168.0.167', 4: '192.168.0.137', 5: '192.168.0.192', 6: '192.168.0.120', 7: '192.168.0.171', 8: '192.168.0.133', 9: '192.168.0.110', 10: '192.168.0.152'}

assert(initial_validators > 0)

for i in range(initial_validators):
    shellRun(f"mkdir -p node{i}")

# setting up the directory, giving the lead to node0
os.chdir("node0")
shellRun(f"istanbul setup --num {initial_validators} --nodes --quorum --save --verbose --verbose >> istanbul.log")
get_data_from_istanbul("istanbul.log")
shellRun("mv validators.log ../")
shellRun("mv dummy-genesis.json ../")
shellRun("mv dummy-static-nodes.json ../")

# update static-node.json to include intended IP and port numbers of all initial validators
os.chdir("..")
update_port_numbers("dummy-static-nodes.json", ip_dict, is_raspberrypi)

for i in range(initial_validators):
    shellRun(f"mkdir -p node{i}/data/geth")

# create accounts
acc_passwd = "12345"
for i in range(initial_validators):
    create_account(acc_passwd, f"node{i}/data", i)

# update genesis.json file with Public account adresses generated in the above steps
public_addr_dict = extract_acc_public_keys("geth_accounts_info.log")
balance = "0x446c3b15f9926687d2c40534fdb564000000000000"
for i in range(initial_validators):
    insert_in_json(f"node0/genesis.json", "alloc", public_addr_dict[i], balance)  # node0 only?? Because node0 is lead node and genesis is there

# distribute files among all initial validators
for i in range(initial_validators):
    shellRun(f"cp -Rn node0/genesis.json node{i}")
    shellRun(f"cp -Rn dummy-static-nodes.json node{i}/data/static-nodes.json") # dummy because it is the updated one
    shellRun(f"cp -Rn node0/{i}/nodekey node{i}/data/geth")
    shellRun(f"rm -rf node{i}/static-nodes.json")

# initialize the nodes
for i in range(initial_validators):
    os.chdir(f"node{i}")
    shellRun("geth --datadir data init genesis.json")
    os.chdir("..")

rpc_port_num = 22000  # used for RPC (remote procedure calls), port forwarding using HTTP etc, viewing in browsers
port_num = 30300      # actual port on which the process is running
pi_password = 'Lums12345'

for i in range(initial_validators):
    start_node_file = open(f"startnode{i}.sh", "w")

    if (is_raspberrypi):
        final_command = f"PRIVATE_CONFIG=ignore /usr/local/quorum_bins/geth --datadir data --nodiscover --istanbul.blockperiod 5 --syncmode full --mine --miner.threads 1 --verbosity 5 --networkid 10 --http --http.addr {ip_dict[i+1]} --http.port {rpc_port_num} --http.api admin,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,istanbul --emitcheckpoints --allow-insecure-unlock --port {port_num} 2>>node{i}.log &"
    else:
        final_command = f"PRIVATE_CONFIG=ignore /usr/local/quorum_bins/geth --datadir data --nodiscover --istanbul.blockperiod 5 --syncmode full --mine --miner.threads 1 --verbosity 5 --networkid 10 --http --http.addr 127.0.0.1 --http.port {rpc_port_num} --http.api admin,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,istanbul --http.corsdomain https://remix.ethereum.org --emitcheckpoints --allow-insecure-unlock --port {port_num} 2>>node{i}.log &"

    start_node_file.write(final_command)
    start_node_file.close()

    shellRun(f"chmod +x startnode{i}.sh")
    shellRun(f"mv startnode{i}.sh node{i}/startnode{i}.sh")

    # distribute node directory(s)
    if (is_raspberrypi):
        try:
            execute_remotely(["cd ~", "cd block-chain-network", "./del_junk.sh", "./del_junk.sh"], "pi", ip_dict[i+1], pi_password)
            command = f"scp -r node{i}/ pi@{ip_dict[i+1]}:/home/pi/block-chain-network"
            prompt_expected = f"pi@{ip_dict[i+1]}'s password: "
            scp_distribution(command, prompt_expected, pi_password)
            execute_remotely(["cd ~", f"cd block-chain-network/node{i}", f"./startnode{i}.sh"], "pi", ip_dict[i+1], pi_password)
        except:
            shellRun("./del_junk.sh")
            raise ConnectionError("Raspberry Pi nodes are off/not-accesible!")
    else:
        shellRun(f"cd node{i} && ./startnode{i}.sh")
        pass  # nothing needs to be copied, everything is settled up

    rpc_port_num = rpc_port_num + 1
    port_num = port_num + 1

shellRun("rm -rf dummy-genesis.json")
shellRun("rm -rf dummy-static-nodes.json")
