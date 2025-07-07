import json

def analyze_energy_agreements(pre_file, post_file):
    with open(pre_file, 'r') as f:
        pre_data = json.load(f)
    
    with open(post_file, 'r') as f:
        post_data = json.load(f)
    
    results = []
    
    for pre, post in zip(pre_data, post_data):
        result = {
            "prosumer_name": pre["prosumer_name"],
            "consumer_name": pre["consumer_name"],
            "agreed_allocated_energy": pre["allocated_energy"],
            "actual_export_energy": post.get("export_energy", 0),
            "actual_import_energy": post.get("import_energy", 0),
            "prosumer_fulfilled": post.get("export_energy", 0) >= pre["allocated_energy"],
            "consumer_fulfilled": post.get("import_energy", 0) >= pre["allocated_energy"]
        }
        results.append(result)
    
    return results

results = analyze_energy_agreements("energy_allocations.json", "post_agreement.json")
print(json.dumps(results, indent=4))
