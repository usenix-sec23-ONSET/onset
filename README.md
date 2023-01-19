# Instructions

## Pull the repository and install requirements

`git clone https://github.com/usenix-sec23-onset/onset.git`

`cd onset`

`python3 -m venv ./venv`

`source venv/bin/activate`

`pip install -r requirements.txt`

### Note: IF `pip install -r requirements.txt` FAILS

install numpy and cython manually then try again. 

`pip install numpy`

`pip install cython`

`pip install -r requirements.txt`


## Install Yates

Follow instructions from Yates source repo. 
https://github.com/cornell-netlab/yates

## Create experiment files.

run `python cvi_config/mkConfig.py` followed by `python cvi_config/create_varied_inputs.py`
This will create traffic matrices specific to the types specified in mkConfig.py

## Run the simulator

`python net_sim.py`

Examples for parameters to input to `net_sim.py` can be found in the `eval_scripts.py` folder. 

## Results

Graphs showing results are written to ./data/results/

The directory is structured with results stored in files noted by <TOPOLOGY NAME>_<ITERATIONS>.

The `.dot` files in the folder are the topologies passed to Yates. They are named based on which iteration they correspond to, e.g., `<TOPOLOGY NAME>_1-2.dot` is the graph used in the first iteration and the other `.dot` file is the graph used in the second iteration. 
