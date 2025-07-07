import socketio

# Create a Socket.IO client
sio = socketio.Client()

prosumers = []
consumers = []

@sio.event
def connect():
    print("Connected to the server.")

@sio.event
def disconnect():
    print("Disconnected from the server.")

@sio.on('add_prosumer')
def add_prosumer(data):
    print("New prosumer added: ", data)
    prosumer_id          =     data["prosumer_id"]
    prosumer_name        =     data["prosumer_name"]
    prosumer_address     =     data["prosumer_address"]
    prosumer_capacity    = int(data["prosumer_capacity"])
    prosumer_offer_price = int(data["prosumer_offer_price"])

    conditioned_dict = {
        'id'              : prosumer_id,
        'name'            : prosumer_name,
        'acc_addr'        : prosumer_address,
        'capacity_kw'     : prosumer_capacity,
        'offer_price'     : prosumer_offer_price
    }
    prosumers.append(conditioned_dict)

@sio.on('add_consumer')
def add_consumer(data):
    print("New consumer added: ", data)
    consumer_id        =     data["consumer_id"]
    consumer_name      =     data["consumer_name"]
    consumer_address   =     data["consumer_address"]
    consumer_demand    = int(data["consumer_demand"])
    consumer_bid_price = int(data["consumer_bid_price"])

    conditioned_dict = {
        'id'              : consumer_id,
        'name'            : consumer_name,
        'acc_addr'        : consumer_address,
        'demand_kw'       : consumer_demand,
        'bid_price'       : consumer_bid_price
    }
    consumers.append(conditioned_dict)

sio.connect('http://localhost:4000')

def plot_transactions(transactions: list):
  import matplotlib.pyplot as plt

  # Data for graphing
  buyer_names   = [t[0] for t in transactions]
  buyer_prices  = [t[1] for t in transactions]
  buyer_demand  = [t[2] for t in transactions]
  seller_names  = [t[3] for t in transactions]
  seller_prices = [t[4] for t in transactions]
  seller_capacity  = [t[5] for t in transactions]
  transaction_prices = [t[6] for t in transactions]
  allocated_energy   = [t[7] for t in transactions]
  rounds = list(range(1, len(transactions) + 1))

  # Plot the results
  plt.figure(figsize=(12, 6))

  plt.plot(rounds, buyer_prices, label="Buyers' Bids", marker='o', color='blue', linestyle='--', markersize=4)
  for idx, (buyer_name, buyer_value, buyer_demand, seller_name, seller_value, seller_capacity, price, allocated_energy) in enumerate(transactions):
     plt.text(rounds[idx], buyer_value, f'{buyer_name}, {buyer_demand}kW', fontsize=10, ha='center', va='bottom')

  plt.plot(rounds, seller_prices, label="Sellers' Offers", marker='o', color='green', linestyle='--', markersize=4)
  for idx, (buyer_name, buyer_value, buyer_demand, seller_name, seller_value, seller_capacity, price, allocated_energy) in enumerate(transactions):
      plt.text(rounds[idx], seller_value, f'{seller_name}, {seller_capacity}kW', fontsize=10, ha='center', va='bottom')

  plt.plot(rounds, transaction_prices, label="Transaction Prices", marker='o', color='red', markersize=4)
  for idx, (buyer_name, buyer_value, buyer_demand, seller_name, seller_value, seller_capacity, price, allocated_energy) in enumerate(transactions):
      plt.text(rounds[idx], price, f'{price}Rs, {allocated_energy}kW', fontsize=8, ha='center', va='bottom')

  plt.xlabel('Transaction Round')
  plt.ylabel('Price')
  plt.title(f'Double Auction and Demand Supply matching with {len(transactions)} Random Entries')
  plt.legend(loc='upper right')
  plt.grid(True)

  plt.show()

#@title unment demand allocation with double auction

from typing import Union, List, Dict, Tuple

from typing import List, Dict, Union

def iterative_matching(prosumers: List[Dict[Union[str, int], Union[str, int]]], 
                       consumers: List[Dict[Union[str, int], Union[str, int]]], 
                       max_iterations: int = 10, 
                       bid_increment: float = 0.1, 
                       offer_decrement: float = 0.1):
    """
    Iterative matching algorithm with bid increase and offer decrease.
    Unmatched consumers increase their bid, and unmatched prosumers decrease their offer.
    
    Args:
    - prosumers: List of dictionaries with prosumer data (name, offer_price, capacity_kw, etc.).
    - consumers: List of dictionaries with consumer data (name, bid_price, demand_kw, etc.).
    - max_iterations: Maximum number of iterations before stopping.
    - bid_increment: Amount by which unmatched consumers increase their bid.
    - offer_decrement: Amount by which unmatched prosumers decrease their offer.

    Returns:
    - List of matched transactions.
    """
    
    for _ in range(max_iterations):
        # Sort for matching process
        prosumers.sort(key=lambda p: p["offer_price"])
        consumers.sort(key=lambda c: c["bid_price"], reverse=True)

        energy_allocations = []

        for consumer in consumers:
            remaining_demand = consumer["demand_kw"]
            for prosumer in prosumers:
                if remaining_demand <= 0:
                    break

                if prosumer["capacity_kw"] > 0 and consumer["bid_price"] >= prosumer["offer_price"]:
                    energy_to_allocate = min(remaining_demand, prosumer["capacity_kw"])
                    remaining_demand -= energy_to_allocate

                    transaction_price = (consumer["bid_price"] + prosumer["offer_price"]) / 2  

                    energy_allocations.append({
                        "prosumer_name": prosumer["name"],
                        "prosumer_id": prosumer["id"],
                        "prosumer_acc_addr": prosumer["acc_addr"],
                        "prosumer_offer": prosumer["offer_price"],
                        "prosumer_capacity": prosumer["capacity_kw"],
                        "consumer_name": consumer["name"],
                        "consumer_id": consumer["id"],
                        "consumer_acc_addr": consumer["acc_addr"],
                        "consumer_bid": consumer["bid_price"],
                        "consumer_demand": consumer["demand_kw"],
                        "price": transaction_price,
                        "allocated_energy": energy_to_allocate
                    })

                    prosumer["capacity_kw"] -= energy_to_allocate
                    consumer["demand_kw"] -= energy_to_allocate

        if energy_allocations:
            return energy_allocations  # Return as soon as successful matches occur
        
        # Adjust bids and offers for the next iteration
        for consumer in consumers:
            if consumer["demand_kw"] > 0:  # Unmatched consumers increase bid
                consumer["bid_price"] += bid_increment
        
        for prosumer in prosumers:
            if prosumer["capacity_kw"] > 0:  # Unmatched prosumers decrease offer
                prosumer["offer_price"] = max(0, prosumer["offer_price"] - offer_decrement)  # Ensure non-negative price

    return None  # Return None if no matches were found

def greedy_matching(prosumers: List[Dict[Union[str, int], Union[str, int]]], consumers: List[Dict[Union[str, int], Union[str, int]]]):
  """
  This functions matches the appropriate consumers with consumers based on price and demand.
  Takes two arguments:
  1. prosumers: list of dictionaries containing data of each prosumer such as name, offer_price, capacity_kw
  2. consumers: list of dictionaries containing data of each consumer such as name, bid_price, demand_kw
  """

  # Sort the data for double auction

  # Sort prosumers by price (ascending)
  prosumers.sort(key=lambda p: p["offer_price"])

  # Sort consumers by price (descending)
  consumers.sort(key=lambda c: c["bid_price"], reverse=True)

  # Matching process: Allocate energy to the consumer
  energy_allocations = []

  i = 0 # consumer index
  j = 0 # prosumer index

  transactions = []

  for consumer in consumers:
    remaining_demand = consumer["demand_kw"]
    for prosumer in prosumers:
      if (remaining_demand <= 0):
        break # move to next consumer if demand in fulfilled

      if (prosumer["capacity_kw"] > 0 and consumer["bid_price"] >= prosumer["offer_price"]):
        energy_to_allocate = min(remaining_demand, prosumer["capacity_kw"])
        remaining_demand -= energy_to_allocate

        transaction_price = (consumer["bid_price"] + prosumer["offer_price"]) / 2  # Average price

        # Record the transaction
        energy_allocations.append({
          "prosumer_name"    : prosumer["name"],
          "prosumer_id"      : prosumer["id"],
          "prosumer_acc_addr": prosumer["acc_addr"],
          "prosumer_offer"   : prosumer["offer_price"],
          "prosumer_capacity": prosumer["capacity_kw"],
          "consumer_name"    : consumer["name"],
          "consumer_id"      : consumer["id"],
          "consumer_acc_addr": consumer["acc_addr"],
          "consumer_bid"     : consumer["bid_price"],
          "consumer_demand"  : consumer["demand_kw"],
          "price"            : transaction_price,
          "allocated_energy" : energy_to_allocate
        })

        prosumer["capacity_kw"] -= energy_to_allocate
        consumer["demand_kw"] -= energy_to_allocate

  if (len(energy_allocations) > 0):
    return energy_allocations
  return None

def test_double_auction(prosumers, consumers):
    # unmet demand allocation
    import random
    from matplotlib import pyplot as plt

    # random.seed(42)

    # Plot prosumer data without sorting
    plt.plot([i for i in range(len(prosumers))], [j["offer_price"] for j in prosumers], 'go', label="Prosumers")

    for i in range(len(prosumers)):
        plt.text(i, prosumers[i]["offer_price"], prosumers[i]["name"]+", "+str(round(prosumers[i]["capacity_kw"], 1))+"kW", ha='center', va='bottom')
    plt.show()

    print("Consumers are:")
    print(consumers)

    print("Prosumers are:")
    print(prosumers)
    plt.plot([i for i in range(len(consumers))], [j["bid_price"] for j in consumers], 'bo', label="Consumers")

    for i in range(len(consumers)):
        plt.text(i, consumers[i]["bid_price"], consumers[i]["name"]+", "+str(round(consumers[i]["demand_kw"], 1))+"kW", ha='center', va='bottom')
    plt.show()

    # Call unment demand allocation and double auction function
    energy_allocations = greedy_matching(prosumers, consumers)

    # Output the allocation details
    if (energy_allocations != None):
        print("Energy Allocations:")
        for allocation in energy_allocations:
            print(f"{allocation['consumer_name']} buys {allocation['allocated_energy']} kW from {allocation['prosumer_name']} "
                f"at {allocation['price']} Rs/unit")
    else:
        print("No allocations could be made. The consumer's bid is too low.")

    for i in prosumers:
        if i["name"] not in [j["prosumer_name"] for j in energy_allocations]:
            print(f"Prosumer {i['name']} could not get allocated")

    for i in consumers:
        if i["name"] not in [j["consumer_name"] for j in energy_allocations]:
            print(f"Consumer {i['name']} could not get allocated")

    total_demand = 0
    for i in consumers:
        total_demand += i["demand_kw"]

    total_supply = 0
    for i in prosumers:
        total_supply += i["capacity_kw"]

    total_allocated_demand = 0
    for i in energy_allocations:
        total_allocated_demand += i["prosumer_capacity"]

    total_allocated_capacity = 0
    for i in energy_allocations:
        total_allocated_capacity += i["consumer_demand"]

    total_allocated_energy = 0
    for i in energy_allocations:
        total_allocated_energy += i["allocated_energy"]

    print(f"Total demand: {total_demand}")
    print(f"Total supply: {total_supply}")
    print(f"Total allocated demand: {total_allocated_demand}")
    print(f"Total allocated capacity: {total_allocated_capacity}")
    print(f"Total allocated energy: {total_allocated_energy}")

    temp_lst = [(i["consumer_name"], round(i["consumer_bid"], 1), round(i["consumer_demand"], 1), i["prosumer_name"], round(i["prosumer_offer"], 1), round(i["prosumer_capacity"], 1), round(i["price"], 1), round(i["allocated_energy"], 1)) for i in energy_allocations]

    plot_transactions(temp_lst)

    return energy_allocations

@sio.on('start_auction')
def start_auction(data):
    print("Auction Started...")
    energy_allocations = test_double_auction(prosumers, consumers)
    sio.emit("energy_allocations", energy_allocations)
    print(energy_allocations)
    print(len(energy_allocations))

# Wait indefinitely to keep the client running
sio.wait()
