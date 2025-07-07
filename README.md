
# Introduction
This repository provides basic tools and instructions to setup a network of IBFT nodes on Raspberry Pis.

# Getting Started
To get started, we need some tools to setup network. The tools include [Go (GoLang)](https://go.dev/dl/), [Quorum](https://github.com/Consensys/quorum) and [istanbul tools](https://github.com/Consensys/istanbul-tools). All these tools are pretty easy to install for different platforms like Ubuntu, Raspberry Pi OS etc.

- `install_tools.sh` is used to install all these tools. Just clone the repository and run `./install_tools.sh`
- To keep ourself at the safe point, open a new terminal to check if the tools are installed. `which go`, `which geth`, `which istanbul`. If you don't want to open a new terminal, you can run `source ~/.bashrc` and check using `which` command.
- There is a file `initial_validators.py`. This is used to setup network using Raspberry Pis (Rpi) with each Rpi representing each node of the network. This contains some hardcoded IP address for our local network in dictionary named `ip_dict`. You can change according to you requirements. Change the number of validators in variable `initial_validators` according to your requirements and run `python3 initial_validators.py`.
 
# After the network
Communicating with the network through each node is an important process. Head to the some arbitrary node and go to `data directory`.
```
cd data/
```
Attach to the node:
```
geth attach geth.ip
```
This will open geth console (we will represent is using >>>) in front of you. Check if all the nodes have synchronized:
```
>>> net.peerCount
```
If it results 5, it means that you have 5 more nodes attached to current node, total 6 nodes in the network. If something else, then there is surely some problem and requires debugging.
