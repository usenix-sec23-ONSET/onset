# Define the quality of attack and benign traffic distrbutions for a network.
# State the source network file (gml file)
# # State aggregate volume, e.g., 10 Gbps, 1 Tbps, 10 Tbps, etc.
# State proportions of benign to malicious traffic, e.g., 100:1, 90:10, 80:20, 50:50, etc.
# State the number of links to attack, e.g., 1, 2, 3, ...
# State the accuracy of the attack, e.g., 10%, 50%, 90%, 100%. 
 
'''
RUN ./cvi_config/mkConfig.py first.
Then run this script. 
'''

# systems libraries
import os
import sys
import json

# third party libraries 
import networkx

# custom functions
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/utilities'))
from src.utilities.tmg import make_human_readable, sanitize_magnitude
from src.utilities.tmg import rand_gravity_matrix
from src.utilities.paths_to_json import get_paths
from src.attacker import Attacker

# save benign matrix to ./data/traffic/<NETWORK NAME>_<BENIGN VOLUME>.txt
EXPERIMENT_DIR = "/home/USERNAME/onset/cvi_config/"
NETWORKS = ['bellCanada', 'surfNet']
VOLUMES = ['100Gbps', '150Gbps', '200Gbps']
NUM_TARGETED = [1, 2, 3, 4, 5]

def usage():
    print("Usage:\n\t{} (name) (gml_file) (flow_volume) (benign_to_malicious_ratio) (num_links_targeted) (attacker_accuracy)".format(sys.argv[0]))
    print("Example:\n\t{} my_topology /path/to/my_topology.gml 1Tbps 50:50 2 100%".format(sys.argv[0]))
    exit()

def batch_create():
    # experiments = os.listdir("./cvi_config/")
    experiments = os.listdir(EXPERIMENT_DIR)
    for exp in experiments: 
        if exp.endswith('.json'):
            print("=== CREATING INPUT FILES FROM '{}' ===".format(exp))
            create_input_files(exp)

def create_input_files(experiment:str):
    if 0:
        try:
            network_name                = sys.argv[1]
            gml_file                    = sys.argv[2]
            aggregate_volume            = sys.argv[3]
            benign_to_malicious_ratio   = sys.argv[4]
            links_targeted              = int(sys.argv[5])
            attack_accuracy             = sys.argv[6]
        except Exception:
            usage()
    else:
        with open(EXPERIMENT_DIR + experiment, 'r') as fob:
             config = json.load(fob)

        network_name                = config["network_name"]
        gml_file                    = config["gml_file"]
        atk_vol                     = config["malicious_volume"]            
        benign_vol                  = config["benign_volume"]            
        links_targeted              = config["links_targeted"]            


    if network_name not in NETWORKS: 
        return
    if atk_vol not in VOLUMES:
        return
    if links_targeted not in NUM_TARGETED: 
        return 

    print("Network name:             : " + network_name)        
    print("GML File                  : " + gml_file)
    print("links targeted            : " + str(links_targeted))
    
    num_hosts = get_num_hosts(gml_file)

    benign_volume = sanitize_magnitude(benign_vol)
    benign_vol_hr = benign_vol
        
    malicious_volume = sanitize_magnitude(atk_vol)
    malicious_vol_hr = atk_vol

    print("benign volume    : {}".format(benign_volume))
    print("malicious volume : {}".format(malicious_volume))
    
    benign_matrix_file = "./data/traffic/{}_benign_{}.txt".format(network_name, benign_vol_hr)
    rand_gravity_matrix(num_hosts, 1, benign_volume, benign_matrix_file)    
    
    json_paths_file = "./data/paths/{}.json".format(network_name)
    
    # Check that these functions work correctly before creating files. 
    assert sanitize_magnitude(make_human_readable(malicious_volume)) == malicious_volume
    assert sanitize_magnitude(make_human_readable(benign_volume)) == benign_volume
    
    OVER_WRITE = False
    if os.path.exists(json_paths_file):
        print("JSON file for paths exists.\n{}".format(json_paths_file))
        if OVER_WRITE: 
            get_paths(gml_file, json_paths_file)    
    else:
        get_paths(gml_file, json_paths_file)
    
    
    attack_matrix = "./data/traffic/{}_{}".format(network_name, malicious_vol_hr)

    attacker = Attacker(network_name, json_paths_file)
    attacker.find_target_link(n_edges=links_targeted)
    attacker.one_shot_sustained_attack(benign_matrix_file, malicious_volume, 'oneShot')
    
def get_num_hosts(gml_file_name):
    G = networkx.read_gml(gml_file_name)
    return len(G.nodes())

if __name__ == "__main__":
    batch_create()
