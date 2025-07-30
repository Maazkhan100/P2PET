from solcx import compile_source, install_solc
import json
import os

# Install Solidity compiler
install_solc("0.8.0")

with open("../contracts/EnergyTrade.sol", "r") as file:
    contract_source_code = file.read()

# Compile
compiled = compile_source(contract_source_code, solc_version="0.8.0")
_, contract_interface = compiled.popitem()

# Save ABI
os.makedirs("../compiled", exist_ok=True)
with open("../compiled/EnergyTrade_abi.json", "w") as abi_file:
    json.dump(contract_interface['abi'], abi_file)

# Save bytecode
with open("../compiled/EnergyTrade_bytecode.txt", "w") as bytecode_file:
    bytecode_file.write(contract_interface['bin'])

print("Compilation complete.")
