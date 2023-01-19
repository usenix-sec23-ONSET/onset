import json 

def sanitize_magnitude(mag_arg: str) -> int:
    """Converts input magnitude arg into an integer
        Unit identifier is the 4th from list character in the string, mag_arg[-4].
        e.g., 1231904Gbps G is 4th from last.
        this returns 1231904 * 10**9.
    Args:
        mag_arg (str): number joined with either T, G, M, or K.

    Returns:
        int: Value corresponding to the input.
    """
    if mag_arg =='0bps':
        return 0

    mag = mag_arg[-4].strip()
    coefficient = int(mag_arg[0:-4])
    print("Coefficient : {}".format(coefficient))
    print("Magnitude   : {}".format(mag))
    exponent = 0
    if mag == 'T':
        exponent = 12
    elif mag == 'G':
        exponent = 9
    elif mag == 'M':
        exponent == 6
    elif mag == 'k':
        exponent == 3
    else:
        raise("ERROR: ill formed magnitude argument. Expected -m <n><T|G|M|k>bps, e.g., 33Gbps")
    result = coefficient * 10 ** exponent
    print("Result: {}".format(result))
    return result


TARGET_PATH = "/home/USERNAME/onset/sim_config/cvi_config/"
networks = ['sprint', 'ANS']
attack_vol = ['100Gbps', '150Gbps', '200Gbps']
benign_vol = '0Gbps'
n_links = [1, 2, 3, 4, 5]
accuracy = "100%"

for net in networks: 
    for tv in attack_vol:
        for n in n_links:
            aggregate_volume = sanitize_magnitude(tv)
            experiment_id = "_".join([net, tv, str(n) + "_link"])
            json_obj = {
                "network_name"                : net,
                "gml_file"                    : "./data/graphs/gml/{}.gml".format(net),
                "links_targeted"              : n,
                "benign_volume"               : benign_vol,
                "malicious_volume"            : tv
            }
            filename = TARGET_PATH + experiment_id + '.json' 
            with open(filename,'w') as fob:
                json.dump(json_obj, fob, indent=4)
                print("wrote to: " + filename)
