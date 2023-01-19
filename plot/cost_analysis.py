import sys
import os
import re
sys.path.append("/home/USERNAME/onset/")
sys.path.append("/home/USERNAME/onset/src")
sys.path.append("/home/USERNAME/onset/src/utilities/")

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
from collections import defaultdict
from math import ceil
# from utilities.post_process import read_result_val

def ecdf(data, array: bool=True):
    """Compute ECDF for a one-dimensional array of measurements."""
    # Number of data points: n
    n = len(data)
    # x-data for the ECDF: x
    x = np.sort(data)
    # y-data for the ECDF: y
    y = np.arange(1, n+1) / n
    if not array:
        return pd.DataFrame({'x': x, 'y': y})
    else:
        return x, y


def get_max_link_demand(d:defaultdict, f:str):
    '''
    d: dictionary, passed by reference. This function modifies d
    f: file descriptor (str). Absolute path.
    returns None.
    Adds 1 to each link in d for which congestion is present (>=1). 
    '''
    
    with open(f, 'r') as fob:
        # skip first two lines (header text).
        fob.readline()
        fob.readline()
        for line in fob.readlines():
            # only count congestion on core links (between sN and sM).
            if len(re.findall('s', line)) < 2:
                continue
            # expects line to look like r"\t\t(sX,sY) : Z\n" were X, Y are int and Z is float. 
            s1, s2 = line.strip().replace(" ", "").split(":")
            s2 = float(s2)

            d[s1] = max(d[s1], ceil(s2))


    return


networks = [
    "sprint",
    "ANS",
    "CRL",
    "bellCanada",
    "surfNet",        
    ]


experiment_folders = [
    "/home/USERNAME/onset/data/archive/results/results-04-27-2022/sprint_crossfire_attack_baseline_200E9_100__-mcf",
    "/home/USERNAME/onset/data/archive/results/results-04-18-2022/ANS_crossfire_attack_baseline_100__-mcf",
    "/home/USERNAME/onset/data/archive/results/results-05-09-2022/CRL_rolling_attack_baseline_100__-mcf",
    "/home/USERNAME/onset/data/archive/results/results-04-18-2022/CRL_crossfire_attack_baseline_200E9_100__-mcf",
    "/home/USERNAME/onset/data/results/CRL_baseline_0__-mcf",
    "/home/USERNAME/onset/data/results/CRL_baseline_3.00e+11_0__-mcf",
    "/home/USERNAME/onset/data/archive/results/results-04-27-2022/bellCanada_crossfire_attack_baseline_200E9_100__-mcf",
    "/home/USERNAME/onset/data/archive/results/results-04-27-2022/surfNet_crossfire_attack_baseline_200E9_100__-mcf",    
    ]



total_attacks = defaultdict(int)
max_link_demand = defaultdict(lambda:defaultdict(int))

for network, experiment_folder in zip(networks, experiment_folders):
    mld = max_link_demand[network]
    ta = total_attacks[network]
    experiments = os.listdir(experiment_folder)
    for experiment in experiments:
        path_p = os.path.join(experiment_folder, experiment, "EdgeExpCongestionVsIterations.dat")
        if not os.path.exists(path_p):
            continue
            
        if re.findall(r'\d+',experiment)[0] == '1':
            continue
        
        get_max_link_demand(mld, path_p)
        ta += 1
    
lineStyle = ['-', '--', '-.', ':', '-']
marker = ['.', 'o', '^', 'v', '<']
label = ['11', '18', '33', '48', '50'] 

print("Network& 2x Capacity (Static)& 2x Capacity (ONSET)& 3x Capacity (Static)& 3x Capacity (ONSET)\\\\" )
for d, l, m, lbl in zip(max_link_demand, lineStyle, marker, label):
    cost = sum(x for x in max_link_demand[d].values())
    edges = len([x for x in max_link_demand[d].values()])
    print("{} & {} & {} & {} & {}\\\\".format(d, 2 * edges, 
                                    int(lbl) * 1 + edges, 
                                    3 * edges, 
                                    int(lbl) * 2 + edges))