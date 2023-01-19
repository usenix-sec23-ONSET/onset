from typing import DefaultDict
import sys
import os
import csv
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./src'))
sys.path.append(os.path.abspath('./src/utilities'))
from src.utilities import SCRIPT_HOME
from src.utilities.post_process import post_proc_timeseries
from net_sim import Attack_Sim
from time import time
from itertools import product
from sys import argv

def main(argv):
    if len(argv) == 1:
        network         = 'sprint'
        te_methods      = ["-mcf"]
        strategies      = ["baseline", "optimal"]
        attack_string   = "200E9"
    else:
        network = argv[1]
        te_methods = [argv[2]]
        strategies      = [argv[3]]
        attack_string   = argv[4] 
        # print("network: {}\nte_method: {}\nstrategy: {}\nattack: {}".format(network, te_methods, strategies, attack_string))
   
    gml_file        = SCRIPT_HOME + "/data/graphs/gml/" + network + ".gml"
    traffic_file    = SCRIPT_HOME + "/data/traffic/" + network + "_crossfire_every_node_" + attack_string + ".txt"
    iterations      = int(os.popen('wc -l ' + traffic_file).read().split()[0])

    data = DefaultDict(list)
    for te_method, strategy in product(te_methods, strategies):
        attack_sim = Attack_Sim(network, 
                                "crossfire_attack_{}_{}".format(strategy, attack_string),
                                iterations=iterations, 
                                te_method=te_method,
                                method="optimal",
                                traffic_file=traffic_file,
                                strategy=strategy, 
                                use_heuristic="",
                                fallow_transponders=100, 
                                congestion_threshold_upper_bound=0,
                                congestion_threshold_lower_bound=float("inf"),
                                )

        result = attack_sim.perform_sim(circuits=10)
        for key in result:
            data[key].extend(result[key])

    result_file = SCRIPT_HOME + "/data/results/{}_{}_{}_{}_crossfire_every_link.csv".format(
        network, te_method, strategy, attack_string)

    print("writing results to: " + result_file)

    with open(result_file, "w") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(data.keys())
        writer.writerows(zip(*data.values()))

if __name__ == "__main__":
    main(argv)