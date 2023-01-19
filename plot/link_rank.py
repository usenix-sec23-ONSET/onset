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


def rank_links(d:defaultdict, f:str):
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
            if s2 >= 1:
                d[s1] += 1
            else:
                d[s1] += 0

    return


networks = [
    "sprint",
    "ANS",
    "CRL",
    "bellCanada",
    "surfNet",        
    ]

experiment_folders = [
    "/home/USERNAME/onset/data/archive/results/results-04-27-2022/sprint_crossfire_attack_baseline_100E9_100__-mcf",
    "/home/USERNAME/onset/data/archive/results/results-04-18-2022/ANS_crossfire_attack_baseline_100__-mcf",
    "/home/USERNAME/onset/data/archive/results/results-04-18-2022/CRL_crossfire_attack_baseline_200E9_100__-mcf",
    "/home/USERNAME/onset/data/archive/results/results-04-27-2022/bellCanada_crossfire_attack_baseline_200E9_100__-mcf",
    "/home/USERNAME/onset/data/archive/results/results-04-27-2022/surfNet_crossfire_attack_baseline_200E9_100__-mcf",    
    ]

total_attacks = defaultdict(int)
link_rank = defaultdict(lambda:defaultdict(int))

for network, experiment_folder in zip(networks, experiment_folders):
    lr = link_rank[network]
    ta = total_attacks[network]
    experiments = os.listdir(experiment_folder)
    for experiment in experiments:
        path_p = os.path.join(experiment_folder, experiment, "EdgeCongestionVsIterations.dat")
        if not os.path.exists(path_p):
            continue
            
        if re.findall(r'\d+',experiment)[0] == '1':
            continue
        
        rank_links(lr, path_p)
        ta += 1
    
    
    # kwargs = {'cumulative': True}
    # plt.rc('font', size=22) 
    link_rank[network] = np.array(sorted(list(lr.values()), reverse=True)) / ta * 100
    # sns.ecdfplot(X/ta)
    # plt.xlabel("Link Rank")
    # plt.ylabel("CDF")
        
    # plt.scatter(list(range(len(X))), X/ta)
    # plt.xlabel("Link ID")
    # plt.ylabel("Link Rank")

    # plt.legend(networks)
    # plt.tight_layout()
    # plt.savefig("/home/USERNAME/onset/plot/cdf_link_rank_Crossfire.pdf".format(network))

kwargs = {'cumulative': True}
plt.rc('font', size=22) 
# X = np.array(sorted(list(lr.values()), reverse=True))
# x, y = sns.ecdfplot(link_rank)
linestyle = ['-', '--', '-.', ':', '-']
marker = ['.', 'o', '^', 'v', '<']
label = ['11', '18', '33', '48', '50'] 
for d, l, m, lbl in zip(link_rank, linestyle, marker, label):
    x, y = ecdf(link_rank[d])
    plt.plot(x, y, marker=m, linestyle=l, label=lbl)

plt.xlabel("Link Rank (%)")
plt.ylabel("CDF")
plt.legend(title="Nodes")
plt.tight_layout()
plt.savefig("/home/USERNAME/onset/plot/cdf_link_rank_Crossfire.pdf".format(network))

