
from web3 import Web3
from web3.middleware import geth_poa_middleware
from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
import serial
import time
import threading

# Web3 setup
web3 = Web3(Web3.HTTPProvider('http://192.168.0.111:22001'))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)  # Apply POA middleware
web3.eth.default_account = web3.eth.accounts[0]

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

contract_deployed_at = "0xb9cF889A830F4ca38d834e838ea2f55D69e8cEC0"
contract_address = web3.to_checksum_address(contract_deployed_at)
contract = web3.eth.contract(address=contract_address, abi=abi)

# Arduino Serial Port setup
# arduino_serial_port = serial.Serial('/dev/cu.wchusbserial1410', 9600, timeout=1)

# Flask and SocketIO setup
app = Flask(__name__, static_folder='public')
socketio = SocketIO(app)

# Variables
producer_address = None
consumer_address = None
ether_per_token = 0
accepted_bid = None
accept_deal_flag = 0
block_deal_flag = 1
pending_tx_list = []
producer = None
consumer = None

def handle_arduino_serial():
    while True:
        break
        # if arduino_serial_port.in_waiting > 0:
        #     line = arduino_serial_port.readline().decode('utf-8').rstrip()
        #     print(f"Received from Arduino: {line}")

arduino_thread = threading.Thread(target=handle_arduino_serial)
arduino_thread.start()

@app.route('/')
def index():
    return send_from_directory('public', 'login_page.html')

@app.route('/enter_wallet')
def enter_wallet():
    try:
        print("Attempting to server wallet.html")
        return send_from_directory('public', 'wallet.html')
    except Exception as e:
        print(f"Error serving wallet.html: {e}")
        return "Error loading wallet page", 404 

@app.route('/node_modules/<path:path>')
def send_node_modules(path):
    return send_from_directory('public/node_modules', path)

@app.route('/consumer.py')
def send_consumer_py():
    return send_from_directory('public', 'consumer.py')

@socketio.on('check_passphrase')
def check_passphrase(data):
    try:
        unlock_result = web3.geth.personal.unlock_account(web3.eth.accounts[0], data, 100000)
        emit('unlock_ethereum_account_result', unlock_result)
    except Exception as e:
        emit('unlock_ethereum_account_result', False)

@socketio.on('startmine')
def startmine():
    web3.geth.miner.start()

@socketio.on('stopmine')
def stopmine():
    web3.geth.miner.stop()

@socketio.on('basic_tx')
def basic_tx(data):
    from_address = web3.eth.accounts[0]
    to_address = data['add']
    value = int(data['val'])
    web3.eth.send_transaction({'from': from_address, 'to': to_address, 'value': value})

def update_pending_tx_list():
    global pending_tx_list
    while True:
        block = web3.eth.get_block('pending', full_transactions=True)
        pending_tx_list = block.transactions if block else []
        time.sleep(1)

def emit_balance():
    while True:
        balance = web3.eth.get_balance(web3.eth.accounts[0])
        socketio.emit('pending_tx_list', {'tx_1': pending_tx_list[0], 'tx_2': pending_tx_list[1], 'tx_3': pending_tx_list[2]} if len(pending_tx_list) >= 3 else {})
        socketio.emit('energy_token_balance', {'bal': balance})
        time.sleep(1)

balance_thread = threading.Thread(target=emit_balance)
balance_thread.start()

pending_tx_thread = threading.Thread(target=update_pending_tx_list)
pending_tx_thread.start()

def check_bid_accepted():
    global accept_deal_flag, block_deal_flag, producer, consumer, ether_per_token
    while True:
        if accept_deal_flag == 1 and block_deal_flag == 1:
            producer = producer_address
            consumer = consumer_address
            ether_per_token = accepted_bid
            block_deal_flag = 2
        if accept_deal_flag == 1:
            print(producer)
            print(consumer)
            print(ether_per_token)
            contract.functions.send_eth(producer, ether_per_token).transact({'from': consumer, 'to': contract_address, 'value': ether_per_token})
        time.sleep(8)

bid_thread = threading.Thread(target=check_bid_accepted)
bid_thread.start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000)

