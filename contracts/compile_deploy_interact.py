from eth_utils import address
from web3 import Web3
import os
from solcx import compile_standard, compile_solc
from dotenv import load_dotenv
from decrypt import decrypt_aes128
import json
import subprocess

smart_contract_file_path = "./"
smart_contract_file = "test"

with open(smart_contract_file_path + smart_contract_file + ".sol", "r") as file:
    simple_storage_file = file.read()

#compile_solc("0.8.0")

#compiled_sol = compile_standard(
#    {
#        "language": "Solidity",
#        "sources": {f"{smart_contract_file}.sol": {"content": simple_storage_file}},
#        "settings": {
#            "outputSelection": {
#                "*": {
#                    "*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"]
#                }
#            }
#        },
#    },
#    solc_version="0.8.0",
#)

#with open(smart_contract_file_path + smart_contract_file + ".json", "w") as file:
#    json.dump(compiled_sol, file)

# retrieve bytecode
#bytecode = compiled_sol["contracts"][f"{smart_contract_file}.sol"][f"{smart_contract_file}"]["evm"][
#    "bytecode"
#]["object"]
bytecode = "608060405234801561001057600080fd5b506108fb806100206000396000f3fe60806040526004361061009c5760003560e01c80633c355120116100645780633c355120146101ae5780634e61e2ed146101d957806353ba8e061461021657806381e5e9e5146102535780639ba7548e1461027e578063cef29f371461029a5761009c565b806305b8effa146100a1578063105ae03a146100de5780631724a0971461011b57806327e235e3146101465780632ed7aec114610183575b600080fd5b3480156100ad57600080fd5b506100c860048036038101906100c3919061063d565b6102c3565b6040516100d5919061074d565b60405180910390f35b3480156100ea57600080fd5b506101056004803603810190610100919061063d565b61030c565b604051610112919061074d565b60405180910390f35b34801561012757600080fd5b50610130610354565b60405161013d919061074d565b60405180910390f35b34801561015257600080fd5b5061016d6004803603810190610168919061063d565b61035a565b60405161017a919061074d565b60405180910390f35b34801561018f57600080fd5b50610198610372565b6040516101a5919061074d565b60405180910390f35b3480156101ba57600080fd5b506101c361037c565b6040516101d0919061074d565b60405180910390f35b3480156101e557600080fd5b5061020060048036038101906101fb919061063d565b610382565b60405161020d919061074d565b60405180910390f35b34801561022257600080fd5b5061023d6004803603810190610238919061063d565b6103a3565b60405161024a919061074d565b60405180910390f35b34801561025f57600080fd5b506102686103bb565b604051610275919061074d565b60405180910390f35b61029860048036038101906102939190610666565b6103c5565b005b3480156102a657600080fd5b506102c160048036038101906102bc91906106a2565b610555565b005b6000600360008373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020549050919050565b60008060008373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020549050919050565b60015481565b60006020528060005260406000206000915090505481565b6000600154905090565b60025481565b60008173ffffffffffffffffffffffffffffffffffffffff16319050919050565b60036020528060005260406000206000915090505481565b6000600254905090565b806000808473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020541015610446576040517f08c379a000000000000000000000000000000000000000000000000000000000815260040161043d9061072d565b60405180910390fd5b806000808473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020600082825461049491906107cf565b9250508190555080600260008282546104ad9190610779565b9250508190555080600360008473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060008282546105039190610779565b925050819055508173ffffffffffffffffffffffffffffffffffffffff166108fc829081150290604051600060405180830381858888f19350505050158015610550573d6000803e3d6000fd5b505050565b806000808473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000205461059f9190610779565b6000808473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000208190555080600160008282546105f39190610779565b925050819055505050565b60008135905061060d81610880565b92915050565b60008135905061062281610897565b92915050565b600081359050610637816108ae565b92915050565b60006020828403121561064f57600080fd5b600061065d848285016105fe565b91505092915050565b6000806040838503121561067957600080fd5b600061068785828601610613565b925050602061069885828601610628565b9150509250929050565b600080604083850312156106b557600080fd5b60006106c3858286016105fe565b92505060206106d485828601610628565b9150509250929050565b60006106eb601483610768565b91507f496e73756666696369656e742062616c616e63650000000000000000000000006000830152602082019050919050565b61072781610847565b82525050565b60006020820190508181036000830152610746816106de565b9050919050565b6000602082019050610762600083018461071e565b92915050565b600082825260208201905092915050565b600061078482610847565b915061078f83610847565b9250827fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff038211156107c4576107c3610851565b5b828201905092915050565b60006107da82610847565b91506107e583610847565b9250828210156107f8576107f7610851565b5b828203905092915050565b600061080e82610827565b9050919050565b600061082082610827565b9050919050565b600073ffffffffffffffffffffffffffffffffffffffff82169050919050565b6000819050919050565b7f4e487b7100000000000000000000000000000000000000000000000000000000600052601160045260246000fd5b61088981610803565b811461089457600080fd5b50565b6108a081610815565b81146108ab57600080fd5b50565b6108b781610847565b81146108c257600080fd5b5056fea264697066735822122000503442ee416e18f6b5787f8bd8587830743d83a8a57948aab2fd6888d2baec64736f6c63430008000033"

# get abi
#abi = json.loads(
#    compiled_sol["contracts"][f"{smart_contract_file}.sol"][f"{smart_contract_file}"]["metadata"]
#)["output"]["abi"]
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

# ===================== Establishing the connection with the network =====================
w3 = Web3(Web3.HTTPProvider("http://192.168.0.152:22000"))
chain_id = 10

# get absolute path to UTC file of the node
directory = "../node0/data/keystore"
files = os.listdir(directory)
file_name = files[0]
file_path=os.path.join(directory, file_name)
absolute_path = subprocess.check_output(["readlink", "-f", file_path], text=True).strip()
utc_file = absolute_path
sender_account = '0x' + utc_file.split("--")[2]
my_address = Web3.to_checksum_address(sender_account)

encryption_file = utc_file
acc_passwd = "12345"
private_key = decrypt_aes128(encryption_file, acc_passwd)

# ===================== Instantiate the contract =====================
SimpleStorage = w3.eth.contract(abi=abi, bytecode=bytecode)

nonce = w3.eth.get_transaction_count(my_address)

# ===================== Set up transaction from constructor =====================
tx = SimpleStorage.constructor().build_transaction(
    {
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": my_address,
        "nonce": nonce,
    }
)

signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Contract deployed to address {tx_receipt.contractAddress}")

# # ===================== Interact with the deployed contract =====================
# simple_storage = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
# print(f"\nInitial value stored is: {simple_storage.functions.get().call()}")

# # nonce is increamented by 1 for every attemp made (https://www.investopedia.com/terms/n/nonce.asp#:~:text=A%20nonce%20is%20a%20numerical%20value%20used%20in,values%20in%20the%20block%20consumes%20significant%20computational%20power.)
# nonce = nonce + 1

# new_transaction = simple_storage.functions.set(12344321).build_transaction(
#     {
#         "chainId": chain_id,
#         "gasPrice": w3.eth.gas_price,
#         "from": my_address,
#         "nonce": nonce,
#     }
# )

# signed_new_txn = w3.eth.account.sign_transaction(
#     new_transaction, private_key=private_key
# )
# tx_new_hash = w3.eth.send_raw_transaction(signed_new_txn.rawTransaction)
# print("\nSending new transaction...\n")
# tx_new_receipt = w3.eth.wait_for_transaction_receipt(tx_new_hash)

# print(f"We have updated the value. New value is: {simple_storage.functions.get().call()}")
