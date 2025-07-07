from web3 import Web3
from web3.middleware import geth_poa_middleware
from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
import serial
import time
import threading
import socketio
import numpy as np
import random
import os
import subprocess
from decrypt import decrypt_aes128

try:
    import RPi.GPIO as GPIO
except:
    print("RPi.GPIO (Raspberry Pi) not found. Running in simulation mode.")
    pass

RELAY_PIN = 23


try:
    GPIO.setmode(GPIO.BCM) # GPIO.BCM or GPIO.BOARD
    GPIO.setup(RELAY_PIN, GPIO.OUT)
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    time.sleep(5)
except KeyboardInterrupt:
    print("Keyboard Interrupt")
except Exception as e:
    print(f"Some error: {e}")
finally:
    print("Cleaning up GPIOs")
    GPIO.cleanup()

# Initialize web3
geth_node_link = 'http://192.168.0.152:22000'
print(f"Connecting to geth Node at {geth_node_link}")
web3 = Web3(Web3.HTTPProvider(geth_node_link))
web3.middleware_onion.inject(geth_poa_middleware, layer=0) # Apply PoA middle ware

if web3.is_connected():
    print("\n\nConnected to Prosumer :) \n\n")
else:
    print("\n\nFailed to connect to prosumer.\n\n")

# Node.js web application framework equivalent in Python
app = Flask(__name__, static_folder='public')
socketio_server = SocketIO(app)
main_server = socketio.Client()

# Connect to the main server
main_server.connect('http://localhost:4000')

@main_server.event
def connect():
    print("Connected to the main server")

@main_server.event
def disconnect():
    print("Disconnected from the main server")

# # Setup Serial Connection with Arduino Nano to control relay
# arduino_serial_port = serial.Serial('/dev/ttyUSB1', baudrate=9600, timeout=1)
# arduino_serial_port.flush()

# # Serial Port Setup for Energy Meter Reading
# meter_serial_port = serial.Serial('/dev/cu.usbserial', baudrate=115200, timeout=1)

meter_reading_string = ""
value_meter = None
producer_address = None
consumer_address = None
ether_per_token = 0
accepted_bid = None
accept_deal_flag = 0
block_deal_flag = 1
energy_tokens = 0
instantaneous_power = 0
power_array_len = 10
instantaneous_power_array = np.zeros(100)
pending_tx_list = []
wh_consumed = 0
wh_consumed_theoratical = 0
total_wh_theoratical = 0
prev_energy_KWH = 0
difference = 0
producer = None
consumer = None
pzem_energy = 0
pzem_instantaneous_power = 0

# Smart Contract for generation of Virtual Energy Tokens and Automate transactions
abi = [
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "name": "balances",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_account",
                "type": "address"
            }
        ],
        "name": "eth_balance",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getTotalTokensGiven",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getTotalTokensUsed",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_account",
                "type": "address"
            }
        ],
        "name": "getTotalTokensUsedByAccount",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address payable",
                "name": "_account",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            }
        ],
        "name": "send_eth",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_account",
                "type": "address"
            }
        ],
        "name": "token_balance",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "name": "tokensUsedByAccount",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalTokensGiven",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalTokensUsed",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_account",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            }
        ],
        "name": "update_tokens",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

contract_deployed_at = "0x56c76f85aa298a1ebf6fa8d0bf0289c1eb9463cf"
contract_address = web3.to_checksum_address(contract_deployed_at)

# Contract Object Creation at Contract Address
contract = web3.eth.contract(address=contract_address, abi=abi)
web3.eth.default_account = web3.eth.accounts[0]

num_of_samples = 100

assert num_of_samples > 0, "Too low number of samples"

sample_arr = np.zeros(num_of_samples)

do_calculations = False

def calculate_wh(instantaneous_power_array):
    # energy = power * time
    time_interval_hours = 0.1 / 3600  # Convert 1 second to hours (readings taken every 1 second from power meter)
    energy_wh = np.sum(instantaneous_power_array * time_interval_hours)

    return energy_wh    

def get_power_samples():
    global sample_arr, do_calculations, instantaneous_power

    for i in range(num_of_samples):
        instantaneous_power = random.uniform(10000, 15000)
        # instantaneous_power = 50
        # sample_arr = np.insert(sample_arr, i, instantaneous_power)
        sample_arr[i] = instantaneous_power
        time.sleep(0.1)
    
    # now sample_arr contains 100 valid samples
    do_calculations = True

def sampling_thread():
    while True:
        get_power_samples()

thread_sample = threading.Thread(target=sampling_thread, daemon=True)
thread_sample.start()

total_energy = 0

def theoratical_power_test():
    global do_calculations, total_energy
    while True:
        if (do_calculations):
            total_energy += calculate_wh(sample_arr)
            do_calculations = False
        time.sleep(0.1)

def read_meter():
    global pzem_energy, pzem_instantaneous_power

    from AC_COMBOX import AC_COMBOX
    energy_meter = AC_COMBOX()
    while True:
        pzem_energy = energy_meter.Poll().Energy
        pzem_instantaneous_power = energy_meter.Poll().Power
        time.sleep(1)

def relay_ctrl():
    global accept_deal_flag, block_deal_flag, producer_address, consumer_address, accepted_bid, ether_per_token, producer, consumer, energy_tokens, instantaneous_power, pending_tx_list, wh_consumed, prev_energy_KWH, difference
    while True:
        pass

def manage_deals():
    global accept_deal_flag, block_deal_flag, producer_address, consumer_address, accepted_bid, ether_per_token, producer, consumer
    while True:
        if accept_deal_flag == 1 and block_deal_flag == 1:
            producer = producer_address
            consumer = consumer_address
            ether_per_token = accepted_bid
            block_deal_flag = 2
        if accept_deal_flag == 1:
            contract.functions.send_eth(producer, ether_per_token).transact({'from': consumer, 'to': contract_address, 'value': ether_per_token})
        time.sleep(8)

@app.route('/')
def index():
    return send_from_directory('public', 'login_page.html')

@app.route('/enter_wallet')
def enter_wallet():
    return send_from_directory('public', 'wallet.html')

@app.route('/node_modules/<path:path>')
def send_node_modules(path):
    return send_from_directory('public/node_modules', path)

@app.route('/consumer.py')
def send_consumer_py():
    return send_from_directory('public', 'consumer.py')

@socketio_server.on('check_passphrase')
def check_passphrase(data):
    unlock_result = web3.geth.personal.unlock_account(web3.eth.accounts[0], data, 100000)
    emit('unlock_ethereum_account_result', unlock_result)

@socketio_server.on('startmine')
def start_mine(data):
    try:
        web3.geth.miner.start()
        emit('mine status', {'status': 'Mining started'})
        print('\n\nMining started\n\n')
    except Exception as e:
        emit('mine_status', {'status': f'Error starting mining: {str(e)}'})
        print('\n\nError starting mining\n\n')

@socketio_server.on('stopmine')
def stop_mine(data):
    try:
        web3.geth.miner.stop()
        emit('mine status', {'status': 'Mining stoped'})
        print('\n\nMining started\n\n')
    except Exception as e:
        emit('mine_status', {'status': f'Error stoping mining: {str(e)}'})
        print('\n\nError stoping mining\n\n')

@socketio_server.on('basic_tx')
def basic_tx(data):
    web3.eth.send_transaction({'from': web3.to_checksum_address(web3.eth.accounts[0]), 'to': web3.to_checksum_address(data['add']), 'value': data['val']})

@main_server.on('req_tokens_0')
def handle_req_tokens_0(data):
    print("\n\nreq_token_0 requested\n\n")
    main_server.emit('display_tokens_0', energy_tokens)

@main_server.on('req_tokens_1')
def handle_req_tokens_1(data):
    main_server.emit('display_tokens_1', energy_tokens)

@main_server.on('req_tokens_2')
def handle_req_tokens_2(data):
    main_server.emit('display_tokens_2', energy_tokens)

@main_server.on('req_tokens_3')
def handle_req_tokens_3(data):
    main_server.emit('display_tokens_3', energy_tokens)

@main_server.on('accept_deal_0')
def accept_deal_0(data):
    producer_address = data['producer_address']
    consumer_address = data['consumer_address']
    accepted_bid     = data['bid']

    print(f"Consumer address from webportal: {consumer_address}, type: {type(consumer_address)}")
    print(f"Consumer address from geth     : {web3.eth.accounts[0]}, type: {type(web3.eth.accounts[0])}")
    # Toggle Relay Connection to start energy trading
    # if (consumer_address == web3.eth.accounts[0]):
        # arduino_serial_port.write('1')
    GPIO.output(RELAY_PIN, GPIO.LOW) # activate the relay
    accept_deal_flag = 1
    # else:
        # print("Account addresses don't mactch, check again!")

def update_energy_tokens():
    global energy_tokens, pzem_energy, pzem_instantaneous_power, instantaneous_power, wh_consumed, total_energy, wh_consumed_theoratical, prev_energy_KWH, difference, pending_tx_list
    while True:
        difference = wh_consumed - prev_energy_KWH
        balance = web3.eth.get_balance(web3.eth.accounts[0])

        pending_tx_dict = {}
        for i in range(min(3, len(pending_tx_list))):
            pending_tx_dict[f'tx_{i+1}'] = pending_tx_list[i]

        socketio_server.emit('pending_tx_list', pending_tx_dict)
        socketio_server.emit('energy_token_balance', {'tok': energy_tokens, 'instantaneous_power': round(pzem_instantaneous_power, 2), 'wh_consumed': round(pzem_energy, 2), 'bal': balance})

        if difference != 0:
            difference = int(difference) # the function update_tokens in test.sol takes int, so that's why, change it accordingly
            contract.functions.update_tokens(web3.eth.accounts[0], difference).transact()
            prev_energy_KWH = wh_consumed
        pending_tx_list = web3.eth.get_block('pending').transactions
        energy_tokens = contract.functions.token_balance(web3.to_checksum_address(web3.eth.accounts[0])).call()
        tokens_used   = contract.functions.getTotalTokensUsedByAccount(web3.eth.accounts[0]).call()
        time.sleep(1)

if __name__ == '__main__':
    threading.Thread(target=read_meter).start()
    threading.Thread(target=theoratical_power_test).start()
    threading.Thread(target=relay_ctrl).start()
    threading.Thread(target=manage_deals).start()
    threading.Thread(target=update_energy_tokens).start()
    socketio_server.run(app, host='0.0.0.0', port=3000, debug=False)
