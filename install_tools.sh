#!/bin/bash  -i

set -e # Exit immediately is some error occurs

## install dependencies
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install curl jq make git build-essential -y

## ==================== Install go ====================

eval "$(cat ~/.bashrc | tail -n +10)"  # source ~/.bashrc

if [ ! $(which go) ]
then
    echo ""
    echo "Installing Go..."
    echo ""
    rm -rf go.tar.gz
    sudo rm -rf $(which go) # remove existing version

    if [ $(whoami) = 'pi' ];
    then
        wget https://go.dev/dl/go1.22.1.linux-arm64.tar.gz -O go.tar.gz     # for Rpi4, change the version accordingly by refering to https://go.dev
    else
        wget https://go.dev/dl/go1.22.1.linux-amd64.tar.gz -O go.tar.gz     # for Ubuntu, change the version accordingly by refering to https://go.dev
    fi

    tar -xzf go.tar.gz
    sudo rm -rf /usr/local/go
    sudo mv go/ /usr/local/
    rm -rf go.tar.gz
    echo "export PATH=/usr/local/go/bin:\$PATH" >> ~/.bashrc
    echo ""
    eval "$(cat ~/.bashrc | tail -n +10)"  # source ~/.bashrc
    echo ""
    echo "Succesfully installed Go in $(which go)"
    echo ""
else
    echo ""
    echo "Go is already present in $(which go)"
    echo ""
fi
# ==================== Install geth ====================

if [ ! $(which geth) ]
then
    echo ""
    echo "Installing Quorum..."
    echo ""

    rm -rf quorum    # remove it if already present some old folder
    git clone https://github.com/Consensys/quorum.git
    eval "$(cat ~/.bashrc | tail -n +10)"  # source ~/.bashrc
    cd quorum && git checkout v23.4.0 && make all
    cd ..
    mkdir quorum_bins
    cp $PWD/quorum/build/bin/* $PWD/quorum_bins
    rm -rf quorum
    sudo mv quorum_bins /usr/local/
    echo "export PATH=/usr/local/quorum_bins:\$PATH" >> ~/.bashrc
    echo ""
    eval "$(cat ~/.bashrc | tail -n +10)"  # source ~/.bashrc
    echo ""
    echo "Succesfully installed Quorum in $(which geth)"
    echo ""
else
    echo ""
    echo "geth is already present in $(which geth)"
    echo ""
fi
## ==================== Install istanbul-tools ====================

if [ ! $(which istanbul) ]
then
    echo ""
    echo "Installing istanbul-tools..."
    echo ""

    rm -rf istanbul-tools    # remove it if already present some old folder
    git clone https://github.com/ConsenSys/istanbul-tools.git
    cd istanbul-tools && make
    cd ..
    mkdir istanbul_tools_bins
    cp $PWD/istanbul-tools/build/bin/* $PWD/istanbul_tools_bins
    rm -rf istanbul-tools
    sudo mv istanbul_tools_bins /usr/local/
    echo "export PATH=/usr/local/istanbul_tools_bins:\$PATH" >> ~/.bashrc
    echo ""
    eval "$(cat ~/.bashrc | tail -n +10)"  # source ~/.bashrc
    echo ""
    echo "Succesfully istanbul-tools in $(which istanbul)"
    echo ""
else
    echo ""
    echo "istanbul is already present in $(which istanbul)"
    echo ""
fi

## ==================== Install node and npm ====================

if [ ! $(which node) ]
then
    if [ $(whoami) = 'pi' ];
    then
        node_name_and_version="node-v22.2.0-linux-arm64"
    else
        node_name_and_version="node-v22.2.0-linux-x64"
    fi

    wget https://nodejs.org/dist/v22.2.0/${node_name_and_version}.tar.xz -O node.tar.xz
    tar xf node.tar.xz
    sudo mv ${node_name_and_version} /usr/local/
    rm node.tar.xz
    echo "export PATH=/usr/local/${node_name_and_version}/bin:\$PATH" >> ~/.bashrc
else
    echo ""
    echo "node is already present in $(which node)"
    echo ""
fi

## ==================== Install some pip things ====================
sudo apt install python3-pip -y
pip3 install modbus_tk --break-system-packages
pip3 install pyserial --break-system-packages
pip3 install pymodbus --break-system-packages
pip3 install pexpect --break-system-packages
pip3 install eth_utils --break-system-packages
pip3 install web3 flask flask-socketio pyserial --break-system-packages
pip3 install py-solc-x --break-system-packages

## ==================== Install some node modules using npm (for server related things like socket.io) ====================
npm install express
npm install socket.io

## ==================== Final things ====================
eval "$(cat ~/.bashrc | tail -n +10)"  # source ~/.bashrc
source ~/.bashrc

echo ""
echo "You are all set. Installed all the tools!"
echo ""

eval "$(cat ~/.bashrc | tail -n +10)"  # source ~/.bashrc
source ~/.bashrc

## ==================== end ====================
