
import networkx as nx
from itertools import permutations
from gurobipy import *
import numpy as np
from src.utilities.plot_reconfig_time import calc_haversine
from src.utilities.link_on_path import link_on_path
from collections import defaultdict

MAX_DISTANCE = 5000 # km 
LINK_CAPACITY = 100000000 
BUDGET = 1

G = nx.read_gml("./data/graphs/gml/sprint.gml")
super_graph = G.copy()


demand = np.loadtxt("./data/traffic/sprint_200Gbps.txt")

####################################################
#### Read Base Network Topology and Derive Paths ###
####################################################
base_paths_dict = {}
base_paths_list = []
for source in G.nodes:
    for target in G.nodes:
        if source != target:
            base_paths_dict[(source, target)] = {}
            base_paths_dict[(source, target)]["paths"] = []
            count = 0
            s_t_paths = nx.all_shortest_paths(G, source, target)
            for s_t_path in s_t_paths:
                base_paths_dict[(source, target)]["paths"].append(s_t_path)
                base_paths_list.append(s_t_path)
                count += 1
            base_paths_dict[(source, target)]["n_paths"] = count

#####################################################
#### Read Traffic Matrix into Source/Destinations ###
#####################################################
'''
 demand_dict: {(source, target): demand_value}
'''
all_node_pairs =  list(permutations(G.nodes, 2))
demand_dict = {}
dim = int(np.sqrt(len(demand)))
for (i, j), (source, dest) in zip(permutations(range(len(G.nodes)), 2),
                                  all_node_pairs):
    demand_dict[(source, dest)] = demand[dim * i + j]

########################################################
#### Create list of candidate links a.k.a. Shortcuts ###
########################################################
candidate_links = []
for source, target in all_node_pairs:
    if (source, target) not in G.edges and sorted((source,target)) not in candidate_links:
        distance = calc_haversine(G.nodes[source]['Latitude'], G.nodes[source]['Longitude'],
                                  G.nodes[target]['Latitude'], G.nodes[target]['Longitude'])
        if  distance < MAX_DISTANCE:
            candidate_links.append( sorted((source,target)) )
        else: 
            print("Distance, {} km, too far between {} and {}").format(distance, source, target)
super_graph.add_edges_from(candidate_links)

########################################
#### Derive paths that use shortcuts ###
########################################
super_paths_dict = {}
super_paths_list = []
augmented_paths = []
for source in super_graph.nodes:
    for target in super_graph.nodes:
        if source != target:
            super_paths_dict[(source, target)] = {}
            super_paths_dict[(source, target)]["paths"] = []
            count = 0
            s_t_paths = nx.shortest_simple_paths(super_graph, source, target)
            for s_t_path in s_t_paths:
                if len(s_t_path) > nx.diameter(G) + 1:
                    break
                super_paths_dict[(source, target)]["paths"].append(s_t_path)
                if s_t_path not in base_paths_list:
                    augmented_paths.append(s_t_path)
                super_paths_list.append(s_t_path)
                count += 1
            super_paths_dict[(source, target)]["n_paths"] = count                

# CHECK ORIGINAL SHORTEST PATHS ARE IN SUPER PATHS! 
for node_pair in base_paths_dict:
    for path_i in base_paths_dict[node_pair]['paths']:
        if path_i not in super_paths_dict[node_pair]['paths']:
            print("\nPath not found! ", path_i)
        else:
            print("x", end="")
    


#################################################
# Map demands to paths                          #
# Keep demands on shortcut paths separate from  #
#   demands on default paths.                   #
#################################################

# Tunnels mapped by Source/Destination of demand in the network
default_flow_tunnels = defaultdict(list) 
shortcut_flow_tunnels = defaultdict(list)
for tunnel in augmented_paths:
    source, target = tunnel[0], tunnel[-1]
    shortcut_flow_tunnels[(source, target)].append(tunnel)

for tunnel in base_paths_list: 
    source, target = tunnel[0], tunnel[-1]
    default_flow_tunnels[(source, target)].append(tunnel)
    
# Tunnels mapped by by links in the network
default_link_tunnels = defaultdict(list)
shortcut_link_tunnels = defaultdict(list)
for tunnel in augmented_paths:
    source, target = tunnel[0], tunnel[-1]
    shortcut_flow_tunnels[(source, target)].append(tunnel)

for tunnel in base_paths_list: 
    source, target = tunnel[0], tunnel[-1]
    default_flow_tunnels[(source, target)].append(tunnel)
    




# Iterate through all paths. 
# For each path, 
#   if it contains a candidate link
#       add path to shortcut_flow_tunnels
#   else
#       add path to default flow tunnels

##########################
# Define Model Variables #
##########################

m = Model('ONSET')

candid_link_vars = m.addVars(range(len(candidate_links)), vtype=GRB.BINARY, name='b_link')

path_vars = m.addVars(range(len(super_paths_list)), vtype=GRB.BINARY, name='b_path')

demand_routable_paths = m.addVars(range(len(demand_dict)), vtype=GRB.BINARY, name='demand_routable_path') 

link_util = m.addVars(range(len(super_graph.edges())), 
                      vtype=GRB.SEMICONT, lb=0, ub=LINK_CAPACITY, name="link_util")

budget_constraint = m.addConstr(quicksum(candid_link_vars.values()) <= BUDGET, "budget")

per_tunnel_flow_allocation = m.addVars(range(len(super_paths_list)), 
                      vtype=GRB.SEMICONT, lb=0, name="per_tunnel_flow_allocation")


##############################
# Add Active Path Constraint #
##############################

# Path value is min of link values for links on that path. 
# path value: path_var[p_i] 
# links on the path: zip(sp_list[p_i], sp_list[p_i][1:])
# path_var is true if link_var is true for each link on path. 
# path_var = min_(LINK_VARS_ON_PATH)

for p_i in range(len(path_vars)):
    # print("path: ", sp_list[p_i])
    path_i_links = list(zip(super_paths_list[p_i], super_paths_list[p_i][1:]))
    # print("path_i_links: ", path_i_links)
    # IF THIS PATH CONTAINS A CANDIDATE LINK
    candidate_links_on_path = []
    for link_l in path_i_links:
        l1 = list(link_l) 
        l2 = [l1[1], l1[0]]
        if l1 in candidate_links or l2 in candidate_links:
            candidate_index = candidate_links.index(l1) if l1 in candidate_links else candidate_links.index(l2)
            candidate_links_on_path.append(candidate_index)

    print("Candidate links on path: {}".format(candidate_links_on_path))
    # Which are the link variables for candidate links on this path
    if candidate_links_on_path: 
        path_candidate_link_vars = [candid_link_vars[var_i] for var_i in candidate_links_on_path]
        m.addConstr(path_vars[p_i] == min_(path_candidate_link_vars), name='path_link_constr_{}'.format(p_i))
        
    else:
        m.addConstr(path_vars[p_i] == True, name='path_link_constr_{}'.format(p_i))

########################################################
# Routable Paths Constraint.                           #
# Path is routable if every link on the path is active #
########################################################

for demand_i, (demand_source, demand_target) in enumerate(demand_dict):
    demand_paths = []
    for path_i in super_paths_list:
        path_source = super_paths_list[0]
        path_target = super_paths_list[-1]
        if path_source == demand_source and path_target == demand_target:
            demand_paths.append(path_i)
        
    m.addConstr(demand_routable_paths[demand_i] == quicksum(path_vars[dp_i] for dp_i in demand_paths),
                "demand_routable_paths_{}".format(demand_i))




#####################################################
# Find demand per tunnel considering active tunnels #
#####################################################
for tunnel_i in range(len(super_paths_list)):
    tunnel_source = super_paths_list["tunnel_i"][0]
    tunnel_target = super_paths_list["tunnel_i"][-1]
    demand = demand_dict[(tunnel_source, tunnel_target)]
    # n_default_paths = len(default_flow_tunnels[(tunnel_source, tunnel_target)])
    m.addConstr(per_tunnel_flow_allocation[tunnel_i] == demand / demand_routable_paths )

###############################################################
# Find Demand per link considering demand from active tunnels #
###############################################################
for link_i, (link_source, link_target) in list(super_graph.edges()):
    # default_tunnels_on_link = default_link_tunnels[(link_source, link_target)]
    # shortcut_tunnels_on_link = shortcut_link_tunnels[(link_source, link_target)]
    
    tunnels_on_link = []
    # ASSUME ANY TUNNEL WILL ONLY TRAVEL A LINK ONCE. NO LOOPED PATHS.
    for tunnel_i, tunnel in enumerate(super_paths_list): 
        tunnel_source = tunnel[0]
        tunnel_target = tunnel[-1]
        if link_on_path(tunnel, [link_source, link_target]):
            tunnels_on_link.append(tunnel_i)

    m.addConstr(link_util[link_i] <= quicksum(per_tunnel_flow_allocation[tunnel_i] for tunnel_i in tunnels_on_link), "link_demand_{}".format(link_i))
            

    # link utilization <= sum(demand for st_default_link_tunnels) + sum(demand for st_shortcut_link_tunnels))
    
    
    # LINK DEMAND IS 
    # SUM OF DEMANDS ON LINK
    # DEMANDS ON LINK = FOR EACH DEMAND, D / ACTIVE PATHS. 
    # st_default_flow_tunnels = default_flow_tunnels[source, target]
    # st_shortcut_flow_tunnels = shortcut_flow_tunnels[source, target]
    
    m.addConstr()
    







link_on_path(my_path, the_link_reversed)


m.update()


m.remove(m.getVars())


(m.getVars()[-1])


link_constr = lambda link_label, link_variable, path_links: link_variable and link_on_path(path_links, link_label)
my_path = ['Cheyenne', 'Kansas City', 'Atlanta','Seattle']
link_id = 8
print(candidate_links[link_id])
print(candid_link_vars[link_id])
print(my_path)
link_constr(candidate_links[link_id], candid_link_vars[link_id], my_path)


0/0


candid_link_vars
candidate_links





