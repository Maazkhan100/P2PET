
from os import system as shellRun

def get_data_from_istanbul(file_name):
    with open(file_name, 'r') as file:
        content = file.read()

    sections = [section.strip() for section in content.split('\n\n') if section.strip()]

    target_file_names = {
        "validators": "validators.log",
        "static-nodes.json": "dummy-static-nodes.json",
        "genesis.json": "dummy-genesis.json"
    }

    for section in sections:
        name, data = section.split('\n', 1)

        with open(target_file_names[name], 'w') as file:
            file.write(data)

import json

def update_port_numbers(file_path, ip_dict, is_raspberrypi=0):
    # Read content from the file
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Define the updated lines
    updated_data = []

    # Iterate through each line
    port_ = 30300
    for n, line in enumerate(data):
        # Extract the current IP address and port number from the line
        parts = line.split('@')
        if len(parts) < 2:
            print(f"Skipping line: {line.strip()} - Invalid format")
            continue
        
        ip_and_port = parts[1].split('?')[0]
        ip, port = ip_and_port.split(':')

        # Construct the updated line
        if (is_raspberrypi):
            updated_line = f"{parts[0]}@{ip_dict[n+1]}:{str(port_)}?{parts[1].split('?')[1]}"  # +1 in ip_dict becasue Raspberry Pis assigned numbers are unsigned starting from 1
        else:
            updated_line = f"{parts[0]}@127.0.0.1:{str(port_)}?{parts[1].split('?')[1]}"  # +1 in ip_dict becasue Raspberry Pis assigned numbers are unsigned starting from 1

        updated_data.append(updated_line)
        port_ = port_ + 1

    # Write the updated content back to the file
    with open(file_path, 'w') as file:
        file.write('[')
        file.write('\n')
        for i in range(len(updated_data)):
            if (i == len(updated_data)-1):
                file.write('\t\"' + updated_data[i] + '\"\n')
            else:
                file.write('\t\"' + updated_data[i] + '\",\n')
        file.write(']')

def create_account(passwd, datadir, node_num):
    import pexpect

    # Define your command and password
    command = f'geth account new --datadir {datadir} account new'
    password = passwd

    # Start the command
    child = pexpect.spawn(command)

    # Wait for the password prompt
    child.expect('Password:')
    child.sendline(password)  # Send the password

    # Wait for the password confirmation prompt
    child.expect('Repeat password:')
    child.sendline(password)  # Send the password again

    # Wait for the process to complete and print its output
    child.expect(pexpect.EOF)

    # Write the command result to a file
    out_file = open("geth_accounts_info.log", "a")   # multiple accounts, so need to dump data in single file, therefore used append mode
    out_file.write(child.before.decode('unicode_escape')) 

def scp_distribution(command, prompt_expected, prompt_password):
    """This method is used distribute files to Raspberry Pis using secure copy (scp) command"""

    import pexpect

    # Spawn a child process
    child = pexpect.spawn(command)

    # Wait for the password prompt and send the password
    child.expect(prompt_expected)
    child.sendline(prompt_password)

    # Wait for the process to complete
    child.expect(pexpect.EOF)

def extract_acc_public_keys(file_path):
    texts_dict = {}
    with open(file_path, 'r') as file:
        node_num = 0
        for line in file:
            if line.startswith("Public address of the key:"):
                text = line.split(":")[1].replace(" ", "").replace("\n", "")

                # store node number as key and Public account address as value
                texts_dict[node_num] = text
                node_num += 1
    return texts_dict

def insert_in_json(file_name, existing_key, new_key, new_value):
    """Appends a new key-value pair to an existing key (existing_key)
       in json file with name file_name"""

    import json

    with open(file_name, 'r') as file:
        data_dict = json.load(file)

    # Make a new key value pair inside the existing key
    data_dict[existing_key][new_key] = {'balance': new_value}

    # Write modified dict to the json file
    with open(file_name, 'w') as file:
        json.dump(data_dict, file, indent=2)

def execute_remotely(commands: list, remote_username: str, remote_ip: str, password: str):
    """
    Takes list of commands and executes remotely using sshpass
    """

    try:
        if (len(commands)):
            commands = "; ".join(commands) # make them a single command semi-colon separated
            print(f"Executing: {commands}")
            exitFlag = shellRun(f"timeout 20 sshpass -p {password} ssh {remote_username}@{remote_ip} \"{commands}\"") # execute all the commands
        else:
            print("Commands list is empty; Try populting it and try again ):")
            exit(1)
    except Exception as e:
        print(e)
        exit(1)

    return exitFlag