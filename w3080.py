
def w3080(url: str) -> dict:
    """
    Takes url in the format http://ip/monitorjson and returns a dictionary
    that contains the following information:

    {   
        'method' : 'uploadsn',
        'mac'    : <mac_addr>,
        'version': 'i.75.98.71',
        'server' : 'em',
        'SN'     : <serial_number>,
        'Data'   : [<voltage>, <current>, <active_power>, <import_energy>, <export_energy>]
    }
    """

    import requests
    import json

    headers   = {'Authorization':'Basic YWRtaW46YWRtaW4='}

    try:
        response  = requests.request("get", url, headers=headers)
    except Exception as e:
        print(f"{e}")
        print("\n\nEnergy Meter not available! Make sure it is turned on and connected to internet.\n\n")
        exit(1)

    resp_dict = json.loads(response.text)
    return resp_dict

while True:
    print(w3080("http://192.168.0.164/monitorjson"))