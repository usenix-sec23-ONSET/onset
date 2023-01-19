import sys
from sys import argv
import os
import json
import csv
from time import time
from typing import DefaultDict

sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/utilities'))
from src.utilities.post_process import post_proc_timeseries
from src.utilities.tmg import sanitize_magnitude, make_human_readable
from net_sim import Attack_Sim

from multiprocessing import Pool

def main(argv):
    networks = ['bellCanada', 'surfNet']
    VOLUMES = ['200Gbps']
    NUM_TARGETED = [5]    
    EXPERIMENT_DIR = "./cvi_config/"
    EXPERIMENT_DIR = "/home/USERNAME/onset/sim_config/cvi_config/"
    experiments = os.listdir(EXPERIMENT_DIR)
    te_methods = ["-ecmp", "-mcf"]

    for net in networks:
        for te_method in te_methods:
            data = {}
            for exp in experiments: 
                # print("exp: " + exp)        
                if exp.endswith('.json') and net in exp:
                    with open(EXPERIMENT_DIR + exp, 'r') as fob:
                        config = json.load(fob)
                    
                    network_name                = config["network_name"]
                    gml_file                    = config["gml_file"]
                    atk_vol                     = config["malicious_volume"]            
                    benign_vol                  = config["benign_volume"]            
                    links_targeted              = config["links_targeted"]            

                    if atk_vol not in VOLUMES:
                        continue
                    if links_targeted not in NUM_TARGETED:
                        continue
                    data["Attack"] = "{}x{}".format(links_targeted, atk_vol.strip("Gbps"))
                    print(te_method + ": " + str(network_name))
                    print("\t" + "gml_file" + ": " + str(gml_file))
                    print("\t" + "malicious_volume" + ": " + str(atk_vol))
                    print("\t" + "benign_volume" + ": " + str(benign_vol))
                    print("\t" + "links_targeted" + ": " + str(links_targeted))
                    network = network_name
                    iterations = 3
                    targets = str(links_targeted)
                    tag = "oneShot"
                    traffic_file = '/home/USERNAME/onset/data/traffic/{}_benign_{}_{}x{}_{}_{}.txt'.format(network, benign_vol, links_targeted, atk_vol, iterations, tag)

                    proportion="{}-{}".format(benign_vol, atk_vol)
                    print("Traffic File: {}".format(traffic_file))
                    
                    if 0: ############################# Preprocessing ############################            
                        t0_initialize = time()
                        attack_sim = Attack_Sim(net, 
                                                "add_circuit_heuristic", 
                                                te_method=te_method,
                                                method="heuristic",
                                                # traffic_file= "/home/USERNAME/onset/data/traffic/" + net + ".txt", 
                                                traffic_file=traffic_file,
                                                strategy="cache", 
                                                use_heuristic="yes",
                                                fallow_transponders=10,
                                                proportion=proportion)
                        t1_initialize = time()
                        precompute_initialization_time = t1_initialize - t0_initialize
                        t0_precompute = time()
                        attack_sim.evaluate_performance_from_adding_link(10)   
                        t1_precompute = time()
                        precompute_time = t1_precompute - t0_precompute

                    if 0: ########################## Baseline Analaysis #########################
                        t0_baseline_init = time()
                        attack_sim = Attack_Sim(net, 
                                                "attack_heuristic", 
                                                iterations=iterations, 
                                                te_method=te_method,
                                                method="heuristic",    
                                                traffic_file=traffic_file,
                                                strategy="cache", 
                                                use_heuristic='yes',
                                                fallow_transponders=0,
                                                proportion=proportion)
                        t1_baseline_init = time()
                        baseline_initialization_time = t1_baseline_init - t0_baseline_init
                        
                        t0_baseline = time()
                        attack_sim.perform_sim(circuits=0)
                        t1_baseline = time()
                        baseline_time = t1_baseline - t0_baseline
                    
                    if 0: ####################### Run ONSET Heuristic Experiment #################
                        
                        t0_onset_init = time()
                        attack_sim = Attack_Sim(net, 
                                                "attack_heuristic", 
                                                iterations=iterations, 
                                                te_method=te_method,
                                                method="heuristic",
                                                traffic_file=traffic_file,
                                                strategy="cache", 
                                                use_heuristic="7",
                                                fallow_transponders=10, 
                                                congestion_threshold_upper_bound=0.8,
                                                congestion_threshold_lower_bound=0.2,
                                                proportion=proportion)
                        t1_onset_init = time()
                        onset_init_time = t1_onset_init - t0_onset_init

                        t0_onset = time()
                        attack_sim.perform_sim(circuits=10)                    
                        t1_onset = time()
                        onset_time = t1_onset - t0_onset
                    
                    if 1: ################### Run ONSET Optimization Experiment ##################
                        t0_onset_init = time()
                        attack_sim = Attack_Sim(net, 
                                                "optimal_{}_link_attack".format(links_targeted), 
                                                iterations=iterations, 
                                                te_method=te_method,
                                                method="optimal",
                                                traffic_file=traffic_file,
                                                strategy="optimal", 
                                                use_heuristic="",
                                                fallow_transponders=100, 
                                                congestion_threshold_upper_bound=0.8,
                                                congestion_threshold_lower_bound=0.2,
                                                proportion=proportion)
                        t1_onset_init = time()
                        onset_init_time = t1_onset_init - t0_onset_init

                        t0_onset = time()
                        result = attack_sim.perform_sim(circuits=10)                    
                        t1_onset = time()
                        onset_time = t1_onset - t0_onset
                        
                        for key in result:
                            if key in data:
                                data[key].extend(result[key])
                            else:
                                data[key] = result[key]                        



            with open("data/results/{}_multiattack{}.csv".format(net, te_method), "w") as outfile:
                # pass the csv file to csv.writer function.
                writer = csv.writer(outfile)
            
                # pass the dictionary keys to writerow
                # function to frame the columns of the csv file
                writer.writerow(data.keys())
            
                # make use of writerows function to append
                # the remaining values to the corresponding
                # columns using zip function.
                writer.writerows(zip(*data.values()))
                
if __name__ == "__main__":
    main(argv)

