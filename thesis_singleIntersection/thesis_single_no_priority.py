
import os
import sys
import optparse
from argparse import ArgumentParser

import math
import thesis.PhaseObject as PhaseObject
import thesis.RecommendSpeed as RS
# C:\Users\WangRabbit\AppData\Local\Programs\Python\Python37\Lib\thesis

import numpy as np
import scipy.sparse as sp
import gurobipy as gp
from gurobipy import GRB

from scipy import stats

# we need to import some python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # Checks for the binary in environ vars
import traci

# contains TraCI control loop
def run():
    step = 0

    while traci.simulation.getMinExpectedNumber() > 0:
        # 迴圈直到所有車輛都已離開路網
        traci.simulationStep()


        step += 1

    traci.close()
    sys.stdout.flush()



def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true",
                          default=False, help="run the commandline version of sumo")
    options, args = opt_parser.parse_args()
    return options

# main entry point
if __name__ == "__main__":
    options = get_options()
    print(options)

    # check binary
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # traci starts sumo as a subprocess and then this script connects and runs
    sumo_start = [sumoBinary, "-c", "thesis_single.sumocfg", "--tripinfo-output", "thesis_single_noPriority_tripInfo.xml",
                  "--random", "--seed", "8"]
                # random 使SUMO隨機挑選seed，會覆蓋--seed效果

    traci.start(sumo_start)
    run()
