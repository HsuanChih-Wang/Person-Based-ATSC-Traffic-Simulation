
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




# {路口ID {狀態,優先的時相代號}}
Vlim = 13 #(m/s)

phaseStrDict = {0: "J1", 1: "J2", 2: "J3", 3: "J4",4: "J5", 5: "J6", 6: "J7", 7: "J8"}
#phaseStrDict1 = {0: "J1"}

phaseStrDict_rev = {"J1": 0, "J2":1, "J3":2, "J4":3, "J5":4, "J6":5, "J7":6, "J8":7}
phaseAndGreenStatePairs = {"J1": [0,1,2], "J2": [13,14], "J3": [15,16,17], "J4": [8,9], "J5": [10,11,12], "J6": [3,4], "J7": [5,6,7], "J8": [18,19]}


# 車道參數
# Nj = {"J1": 2, "J2": 1, "J3": 2, "J4": 1, "J5": 2, "J6": 1, "J7": 2, "J8": 1}
Nj = {0: 2, 1: 1, 2: 2, 3: 1,
        4: 2, 5: 1, 6: 2, 7: 1}
# 停等車輛
vehQueue = {"J1": [], "J2": [], "J3": [], "J4": [], "J5": [], "J6": [], "J7": [], "J8": []}
# 車輛編號與位置
vehNoneQueue = {"J1": [], "J2": [], "J3": [], "J4": [], "J5": [], "J6": [], "J7": [], "J8": []}
# 有安裝OBU車輛列表
OBU_Dict = {}
# 各時相停等車輛總數 (IQj)
IQj = {"J1": 0, "J2": 0, "J3": 0, "J4": 0, "J5": 0, "J6": 0, "J7": 0, "J8": 0}

#路口編號資料
intersectionList = ["I1"]

#模擬設定(最佳化時段區間)
planHorizon = [0,1]

#號誌資料
IntersectionSignal = {"I1": [{j:PhaseObject.Phase() for j in ['J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8']},
                                {j:PhaseObject.Phase() for j in ['J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8']}]
                              }  # 未來新增多路口

#原定時制內容
BackgroundGreen = {0: 9, 1: 5, 2: 18, 3: 5,
                    4: 9, 5: 5, 6: 18, 7: 5}
BackgroundCycle = 57

# 號誌
toleranceFactor = 0.3
R = 5  #yellow + allred
C_opt = BackgroundCycle
Cmin = round(C_opt * (1 - toleranceFactor+0.1))
Cmax = round(C_opt * (1 + toleranceFactor+0.1))+1

# Gmax = {0: int(BackgroundGreen[0]*(1+toleranceFactor)), 1: int(BackgroundGreen[1]*(1+toleranceFactor)),
#         2: int(BackgroundGreen[2]*(1+toleranceFactor)), 3: int(BackgroundGreen[3]*(1+toleranceFactor)),
#         4: int(BackgroundGreen[4]*(1+toleranceFactor)), 5: int(BackgroundGreen[5]*(1+toleranceFactor)),
#         6: int(BackgroundGreen[5]*(1+toleranceFactor)), 7: int(BackgroundGreen[7]*(1+toleranceFactor))}

Gmin = {0: round(BackgroundGreen[0]*(1-toleranceFactor)), 1: round(BackgroundGreen[1]*(1-toleranceFactor)),
        2: round(BackgroundGreen[2]*(1-toleranceFactor)), 3: round(BackgroundGreen[3]*(1-toleranceFactor)),
        4: round(BackgroundGreen[4]*(1-toleranceFactor)), 5: round(BackgroundGreen[5]*(1-toleranceFactor)),
        6: round(BackgroundGreen[5]*(1-toleranceFactor)), 7: round(BackgroundGreen[7]*(1-toleranceFactor))}

phaseList = [0, 1, 2, 3, 4, 5, 6, 7]
# GijkList = [0, 1, 2, 3, 4, 5, 6, 7]
# TijkList = [0, 1, 2, 3, 4, 5, 6, 7]

# phaseEndTimeResult = {0: 38, 1: 53, 2: 91, 3: 106,
#                       4: 38, 5: 53, 6: 91, 7: 106}
TijkResult = {0: 0, 1: 0, 2: 0, 3: 0,
              4: 0, 5: 0, 6: 0, 7: 0}

GijkResult = {0: 0, 1: 0, 2: 0, 3: 0,
              4: 0, 5: 0, 6: 0, 7: 0}

CycleAccumulated = 0

GijkLengthCal = {0: 0, 1: 0, 2: 0, 3: 0,
              4: 0, 5: 0, 6: 0, 7: 0}

phaseIsEnd = {0: False, 1: False, 2: False, 3: False,
           4: False, 5: False, 6: False, 7: False}
currentPhase = [0,4]
phasePendingCounter = {0: R, 1: R, 2: R, 3: R,
                       4: R, 5: R, 6: R, 7: R}

accumulatedIIS = 0


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
    # SUMO
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true",
                          default=False, help="run the commandline version of sumo")
    options, args = opt_parser.parse_args()
    ##

    # 參數基本上分兩種，一種是位置參數 (positional argument)，另一種就是選擇性參數 (optional argument)，主要差別在於參數指定方式的不同。
    parser = ArgumentParser()
    parser.add_argument("pos1", help="positional argument 1")
    parser.add_argument("-o", "--optional-arg", help="optional argument", dest="opt", default="default")
    args = parser.parse_args()
    print("positional arg:", args.pos1)
    print("optional arg:", args.opt)


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
