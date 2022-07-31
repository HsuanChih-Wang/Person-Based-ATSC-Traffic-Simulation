
import os
import sys
import optparse
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


def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true",
                          default=False, help="run the commandline version of sumo")
    options, args = opt_parser.parse_args()
    return options


phaseStrDict = {0: "J1", 1: "J2", 2: "J3", 3: "J4",4: "J5", 5: "J6", 6: "J7", 7: "J8"}
#phaseStrDict1 = {0: "J1"}

phaseStrDict_rev = {"J1": 0, "J2":1, "J3":2, "J4":3, "J5":4, "J6":5, "J7":6, "J8":7}
phaseAndGreenStatePairs = {"J1": [0,1,2], "J2": [13,14], "J3": [15,16,17], "J4": [8,9], "J5": [10,11,12], "J6": [3,4], "J7": [5,6,7], "J8": [18,19]}

# 車道參數
# Nj = {"J1": 2, "J2": 1, "J3": 2, "J4": 1, "J5": 2, "J6": 1, "J7": 2, "J8": 1}
Nj = {0: 2, 1: 1, 2: 2, 3: 1,
        4: 2, 5: 1, 6: 2, 7: 1}
# 車道速限
Vlim = 13 # m/s

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
toleranceFactor = 0.2
R = 5  # Yellow + allred
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

# phaseEndBinaryVar 用於指出該時相是否已結束
phaseEndBinaryVar = [0 for x in range(0, 8)]
# currentPhase 指出當下正在(或即將轉換至)運作時相
currentPhase = [0, 4]
# phasePendingCounter 指出該時相是否正在轉換階段，轉換階段 = Yellow + AllRed
phasePendingCounter = {0: R, 1: R, 2: R, 3: R,
                       4: R, 5: R, 6: R, 7: R}

accumulatedIIS = 0
def monitorGijkLength():
    def checkAllPhasesEnd():
        check = 0
        for num in phaseIsEnd:  # 確認是否全部時相皆已結束
            if (phaseIsEnd[num]):
                check = check + 1
        if check == 8:  # 全部時相都結束了，將相關list設定回原始預設值
            global CycleAccumulated
            for num in range(0,4):  # cycle結果累計
                CycleAccumulated = CycleAccumulated + GijkResult[num]
            CycleAccumulated += R*4
            print("CycleAccumulated = ", CycleAccumulated)

            for num in range(0, 8):
                phaseIsEnd[num] = False
                GijkLengthCal[num] = 0
                GijkResult[num] = 0

            return True
        else:
            return False

    def checkGijkExist(j):
        currentState = traci.trafficlight.getRedYellowGreenState('I1')
        print("currentSTATE = ", currentState)
        check = False
        str_j = phaseStrDict[j]
        for num in phaseAndGreenStatePairs[str_j]:
            if (currentState[num] == 'G'):
                check = True
            else:
                check = False
        if check == True:
            return True
        else:
            return False


    # 先檢查是否全部時相皆已結束(全部為True)
    checkAllPhasesEnd()

    for num in range(0, len(currentPhase)):
        j = currentPhase[num]
        if phasePendingCounter[j] == R:  #  clearence time
            result = checkGijkExist(j)  # 檢查時相j是否還在currentState ?
            if (result):   # 是，該時相累積綠燈長度+1
                GijkLengthCal[j] = GijkLengthCal[j] + 1
            else:  # 否，該時相已經結束

                phaseIsEnd[j] = True  # 標記該時相結束
                GijkResult[j] = GijkLengthCal[j]  # 將時相總累計綠燈長度交給 GijkResult

                if (currentPhase[num] == 7):  # 已經到ring2的底，再次計算由時相4開始
                    currentPhase[num] = 4
                elif (currentPhase[num] == 3):  # 已經到ring1的底，再次計算由時相0開始
                    currentPhase[num] = 0
                else:
                    TijkResult[j + 1] = TijkResult[j] + GijkResult[j] + R  #下個時相的起始時間 = 本時相起始時間 + 綠燈時間 + 清道時間
                    currentPhase[num] = currentPhase[num] + 1  # 沒有到底，直接+1
                phasePendingCounter[currentPhase[num]] = phasePendingCounter[currentPhase[num]] - 1  #下個時相計數-1

        else:
            phasePendingCounter[j] = phasePendingCounter[j] - 1
            if (phasePendingCounter[j] == 0):
                phasePendingCounter[j] = R  #計時結束

    print("----GijkLengthCal---- ")
    print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
          % (GijkLengthCal[0], GijkLengthCal[1], GijkLengthCal[2], GijkLengthCal[3], GijkLengthCal[4], GijkLengthCal[5],
             GijkLengthCal[6], GijkLengthCal[7]))
    print("----phasePendingCounter---- ")
    print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
          % (phasePendingCounter[0], phasePendingCounter[1], phasePendingCounter[2], phasePendingCounter[3], phasePendingCounter[4], phasePendingCounter[5],
             phasePendingCounter[6], phasePendingCounter[7]))
    print("currentPhase = ", currentPhase)

def updateGreenMin():
    currentState = traci.trafficlight.getRedYellowGreenState('I1')
    currentexephase = []  # 找到當下執行的時相(可能不只一個)
    for j in phaseAndGreenStatePairs:
        check = False
        for num in phaseAndGreenStatePairs[j]:
            if (currentState[num] == 'G'):
                check = True
            else:
                check = False
        if check == True:
            currentexephase.append(j)

    #nowSimtime = traci.simulation.getTime()
    if len(currentexephase) > 0:
        for j in currentexephase:
            numeric_j = phaseStrDict_rev[j]
            Gmin[numeric_j] = Gmin[numeric_j] - 1 #更新綠燈範圍

    else:
        return False
    print("new Gmin = ",Gmin)

def checkNowStateYorAR():
    currentState = traci.trafficlight.getRedYellowGreenState('I1')
    currentexephase = []  # 找到當下執行的時相(可能不只一個)
    for j in phaseAndGreenStatePairs:
        check = False
        for num in phaseAndGreenStatePairs[j]:
            if (currentState[num] == 'G'):
                check = True
            else:
                check = False
        if check == True:
            currentexephase.append(j)

    if len(currentexephase) == 0:
        return True
    else:
        return False

def EXE_GUROBI():
    ################## GUROBI ##################
    vehQueueList = []
    vehNoneQueueList = []

    # if (updateGreenMin() == False):
    #     return False #在黃燈或全紅時間，無法號誌執行最佳化，直接結束
    if checkNowStateYorAR():
        return False  #在黃燈或全紅時間，無法號誌執行最佳化，直接結束

    # Big M
    M = 999999
    # constant
    s = 0.5
    Ls = 4
    vlim = 13

    IQj = {0: len(vehQueue['J1']), 1: len(vehQueue['J2']), 2: len(vehQueue['J3']), 3: len(vehQueue['J4']),
           4: len(vehQueue['J5']), 5: len(vehQueue['J6']), 6: len(vehQueue['J7']), 7: len(vehQueue['J8'])}

    ###### GUROBI ######

    try:
        # Create a new model
        m = gp.Model(" mip1 ")

        Ojx = [[None for x in range(1 + len(vehQueue[phaseStrDict[j]]) + len(vehNoneQueue[phaseStrDict[j]]))] for j in phaseStrDict]
        ##print("Ojx = ",Ojx)
        TPjx = [[None for x in range(1 + len(vehQueue[phaseStrDict[j]]) + len(vehNoneQueue[phaseStrDict[j]]))] for j in phaseStrDict]
        ##print("TPjx = ",TPjx)

        for j in phaseStrDict:
            phaseStr = phaseStrDict[j]
            #分別取出每個時相內的車輛資訊
            for vehItem in vehQueue[phaseStr]:
                x = vehItem['order']
                vehQueueList.append((j, x))  #
                Ojx[j][x] = vehItem['occupancy']
                #print("Ojx[", j, ",", x, "] = ", Ojx[j][x])  # Test

            for vehItem in vehNoneQueue[phaseStr]:
                x = vehItem['order']
                vehNoneQueueList.append((j, x))  #
                #print("###### x = ",x)
                TPjx[j][x] = vehItem['ProjectArrTime(TPxj)']
                #print("TPjx[", j, ",", x, "] = ", TPjx[j][x])
                Ojx[j][x] = vehItem['occupancy']
                #print("Ojx[", j, ",", x, "] = ", Ojx[j][x])  # Test

        # vehQueue
        DQjx = m.addVars(vehQueueList, vtype=GRB.CONTINUOUS, name="DQjx")

        # vehNoneQueue
        Trjx = m.addVars(vehNoneQueueList, vtype=GRB.CONTINUOUS, name="Trjx")
        Djx = m.addVars(vehNoneQueueList, vtype=GRB.CONTINUOUS, name="Djx")
        DEjx = m.addVars(vehNoneQueueList, vtype=GRB.CONTINUOUS, name="DEjx")
        Qjx = m.addVars(vehNoneQueueList, vtype=GRB.INTEGER, name="Qjx")

        #Traffic Signal
        Tijk = m.addVars(phaseList, vtype=GRB.INTEGER, name="Tijk")
        Gijk = m.addVars(phaseList, vtype=GRB.INTEGER, name="Gijk")
        Tijk_plus_1 = m.addVars(phaseList, vtype=GRB.INTEGER, name="Tijk_plus_1")
        C = m.addVar(vtype=GRB.INTEGER, name="CYCLE")
        #Tauijk = m.addVars(phaseList, vtype=GRB.INTEGER, name="Tauijk")  # = GijkLengthCal

        # Binary Variables
        Ykjx = m.addVars(vehNoneQueueList, vtype=GRB.BINARY, name="Ykjx")
        Thetakjx = m.addVars(vehNoneQueueList, vtype=GRB.BINARY, name="Thetakjx")
        Sigmakjx = m.addVars(vehNoneQueueList, vtype=GRB.BINARY, name="Sigmakjx")

        Rhoijk = m.addVars(phaseList, vtype=GRB.BINARY, name="Rhoijk")
        Deltaijk = m.addVars(phaseList, vtype=GRB.BINARY, name="Deltaijk")
        Phiijk = m.addVars(phaseList, vtype=GRB.BINARY, name="Phiijk")

        m.update()

        # 設定目標式
        objectiveFunction = gp.quicksum(Ojx[j][x] * Djx[j, x] for j in phaseStrDict for x in
                                        range(IQj[j]+1, IQj[j]+ 1 + len(vehNoneQueue[phaseStrDict[j]]))) \
                            + gp.quicksum(Ojx[j][x] * DQjx[j, x] for j in phaseStrDict for x in range(1,IQj[j]+1))
        #print("Set Obj Function: ", objectiveFunction)
        m.setObjective(objectiveFunction, sense=GRB.MINIMIZE)

        for j in phaseStrDict:
            ceil_IQj_Nj = math.ceil(IQj[j] / Nj[j])  # 純計算
            #m.addConstr(Gijk[j] <= Gmax[j])  # 最大綠限制
            #m.addConstr(Gijk[j] >= Gmin[j])  # 最小綠限制
            m.addConstr(Gijk[j] >= 0, 'cGijk[min]')  # 最小綠限制

            m.addConstr(GijkLengthCal[j] - Gmin[j] <= (1 - Deltaijk[j]) * M - 0.001, 'cGijk[0]')
            m.addConstr(GijkLengthCal[j] - Gmin[j] >= (-M) * Deltaijk[j], 'cGijk[1]')

            m.addConstr(1 + M * (1 - Deltaijk[j]) >= Rhoijk[j], 'cGijk[2]')
            m.addConstr(Rhoijk[j] >= 1 - M * (1 - Deltaijk[j]), 'cGijk[3]')
            m.addConstr(M * Deltaijk[j] >= Rhoijk[j], 'cGijk[4]')
            m.addConstr(Rhoijk[j] >= (-M) * Deltaijk[j], 'cGijk[5]')

            # Rhoijk = 0 表示 時相已經超過其最短綠燈時間 -> Gijk[j] >= 0
            # Rhoijk = 1 表示 時相尚未超過其最短綠燈時間 -> Gijk[j] >= Gmin[j] - GijkLengthCal[j]
            m.addConstr(Gijk[j] >= Gmin[j] - GijkLengthCal[j] - (1 - Rhoijk[j]) * M, 'cGijk[6]')
            m.addConstr(Gijk[j] >= (-M) * Rhoijk[j], 'cGijk[7]')

            # m.addConstr(Gijk[j] >= Gmin[j] - GijkLengthCal[j] - (1 - Rhoijk[j]) * M, 'cGijk[1]')
            # m.addConstr(Gijk[j] >= GijkLengthCal[j] - Rhoijk[j] * M - (1 - Phiijk[j]) * M, 'cGijk[2]')
            # m.addConstr(Gijk[j] <= Rhoijk[j] * M + Phiijk[j] * M, 'cGijk[3]')
            #
            # m.addConstr(GijkLengthCal[j] - Gmin[j] <= (1 - Deltaijk[j]) * M - 0.001, 'cGijk[4]')
            # m.addConstr(GijkLengthCal[j] - Gmin[j] >= (-M) * Deltaijk[j], 'cGijk[5]')
            # m.addConstr(1 + M * (1 - Deltaijk[j]) >= Rhoijk[j], 'cGijk[6]')
            # m.addConstr(Rhoijk[j] >= 1 - M * (1 - Deltaijk[j]), 'cGijk[7]')
            # m.addConstr(M * Deltaijk[j] >= Rhoijk[j], 'cGijk[8]')
            # m.addConstr(Rhoijk[j] >= (-M) * Deltaijk[j], 'cGijk[9]')

            m.addConstr(Gijk[j] >= ceil_IQj_Nj / s - M * phaseEndBinaryVar[j], 'cGijk[undersaturated]')  #最小綠限制 (至少能清除原停等車輛，確保undersaturated)

            for x in range(1, IQj[j] + 1):
                ceil_X_Nj = math.ceil(x - 1 / Nj[j])  # 純計算
                # Queued Vehicle Delay
                m.addConstr(DQjx[j, x] >= Tijk[j] + ceil_X_Nj / s)

            for x in range(IQj[j] + 1, IQj[j] + 1 + len(vehNoneQueue[phaseStrDict[j]])):
                # print("TPjx[", j ,"][",x," ] = ", TPjx[j][x]) # 印出TPjx[j][x]
                m.addConstr(TPjx[j][x] >= Tijk[j] + Gijk[j] - Ykjx[j, x] * M + 0.00001)
                m.addConstr(TPjx[j][x] <= Tijk[j] + Gijk[j] + (1 - Ykjx[j, x]) * M)
                m.addConstr(Thetakjx[j, x] <= Ykjx[j, x])

                m.addConstr(Trjx[j, x] <= Tijk[j] + (1 - Sigmakjx[j, x]) * M)
                m.addConstr(Trjx[j, x] >= Tijk[j] - Sigmakjx[j, x] * M + 0.00001)

                ceil_X_Nj = math.ceil(x - 1 / Nj[j])  # 純計算
                m.addConstr(Qjx[j, x] >= ceil_X_Nj - (1 - Sigmakjx[j, x]) * M)
                m.addConstr(Qjx[j, x] >= ceil_X_Nj - s * (Trjx[j, x] - Tijk[j]) - Sigmakjx[j, x] * M)
                m.addConstr(Qjx[j, x] >= 0)

                AAA = Qjx[j, x] * Ls / vlim
                BBB = (Qjx[j, x] + IQj[j]) * Ls / vlim
                m.addConstr(Qjx[j, x] / s + AAA <= Gijk[j] + (1 - Sigmakjx[j, x]) * M + (1 - Thetakjx[j, x]) * M)
                m.addConstr(Qjx[j, x] / s + AAA >= Gijk[j] - (1 - Sigmakjx[j, x]) * M - Thetakjx[j, x] * M + 0.00001)
                m.addConstr(Qjx[j, x] / s + Trjx[j, x] + BBB <= Tijk[j] + Gijk[j] + Sigmakjx[j, x] * M + (1 - Thetakjx[j, x]) * M)
                m.addConstr(Qjx[j, x] / s + Trjx[j, x] + BBB >= Tijk[j] + Gijk[j] - Sigmakjx[j, x] * M - Thetakjx[j, x] * M + 0.00001)

                # Non-Queued Vehicle Delay
                m.addConstr(Djx[j, x] >= Qjx[j, x] / s + Tijk[j] - Trjx[j, x] - (1 - Sigmakjx[j, x]) * M - (1 - Thetakjx[j, x]) * M)
                m.addConstr(Djx[j, x] >= Qjx[j, x] / s + Tijk[j] - Trjx[j, x] + DEjx[j, x] - (1 - Sigmakjx[j, x]) * M -Thetakjx[j, x] * M)
                m.addConstr(Djx[j, x] >= Qjx[j, x] / s - Sigmakjx[j, x] * M - (1 - Thetakjx[j, x]) * M)
                m.addConstr(Djx[j, x] >= Qjx[j, x] / s + DEjx[j, x] - Sigmakjx[j, x] * M - Thetakjx[j, x] * M)

                # Equality Constraint
                m.addConstr(Trjx[j, x] == TPjx[j][x] - (Qjx[j, x] * Ls / vlim))
                m.addConstr(DEjx[j, x] == Tijk_plus_1[j] - (Tijk[j] + Gijk[j]))

        # k週期的號誌參數
        # 檢查若已經有時相結束，則把該時相有關的變數變成常數
        #print("phaseIsEnd = ", phaseIsEnd)
        for j in phaseIsEnd:
            if (phaseIsEnd[j]):
                print("時相 ", j, " 已經結束了!")
                print("Tijk[",j,"] = ", Tijk[j])
                print("TijkResult[",j,"] = ", TijkResult[j])
                phaseEndBinaryVar[j] = 1
                m.addConstr(Tijk[j] == int(TijkResult[j]), 'cTijkResult')
                print("Gijk[", j, "] = ", Gijk[j])
                print("GijkResult[", j, "] = ", GijkResult[j])
                m.addConstr(Gijk[j] == int(GijkResult[j]), 'cGijkResult')


        m.addConstr(Tijk[0] == 0, 'ct1')
        m.addConstr(Tijk[4] == 0, 'ct2')

        m.addConstr(Tijk[0] == Tijk[4], 'ct3')
        m.addConstr(Tijk[2] == Tijk[6], 'ct4')  # Rhoijk = 0 表示 時相已經超過其最短綠燈時間 ->需要加上已經經過的時間
        m.addConstr(Tijk[1] == Tijk[5], 'ct4_1')  # 限制不可早開遲閉
        m.addConstr(Tijk[3] == Tijk[7], 'ct4_2')  # 限制不可早開遲閉

        m.addConstr(Tijk[1] == Tijk[0] + Gijk[0] + (GijkLengthCal[0] * (1 - Rhoijk[0])) + R, 'ct5')
        m.addConstr(Tijk[2] == Tijk[1] + Gijk[1] + (GijkLengthCal[1] * (1 - Rhoijk[1])) + R, 'ct6')
        m.addConstr(Tijk[3] == Tijk[2] + Gijk[2] + (GijkLengthCal[2] * (1 - Rhoijk[2])) + R, 'ct7')
        m.addConstr(Tijk[5] == Tijk[4] + Gijk[4] + (GijkLengthCal[4] * (1 - Rhoijk[4])) + R, 'ct8')
        m.addConstr(Tijk[6] == Tijk[5] + Gijk[5] + (GijkLengthCal[5] * (1 - Rhoijk[5])) + R, 'ct9')
        m.addConstr(Tijk[7] == Tijk[6] + Gijk[6] + (GijkLengthCal[6] * (1 - Rhoijk[6])) + R, 'ct10')
        m.addConstr(C >= Cmin ,'cCmin')
        m.addConstr(C <= Cmax - 0.00001, 'cCmax')
        m.addConstr(Tijk[3] + Gijk[3] + (GijkLengthCal[3] * (1 - Rhoijk[3])) + R - Tijk[0] == C, 'cC1')
        m.addConstr(Tijk[7] + Gijk[7] + (GijkLengthCal[7] * (1 - Rhoijk[7])) + R - Tijk[4] == C, 'cC2')

        # k+1週期的時制內容
        m.addConstr(Tijk_plus_1[0] == Tijk[3] + Gijk[3] + R, 'Tijk_plus_1[0]')
        m.addConstr(Tijk_plus_1[1] == Tijk_plus_1[0] + BackgroundGreen[0] + R, 'Tijk_plus_1[1]')
        m.addConstr(Tijk_plus_1[2] == Tijk_plus_1[1] + BackgroundGreen[1] + R, 'Tijk_plus_1[2]')
        m.addConstr(Tijk_plus_1[3] == Tijk_plus_1[2] + BackgroundGreen[2] + R, 'Tijk_plus_1[3]')
        m.addConstr(Tijk_plus_1[4] == Tijk[7] + Gijk[7] + R, 'Tijk_plus_1[4]')
        m.addConstr(Tijk_plus_1[5] == Tijk_plus_1[4] + BackgroundGreen[4] + R, 'Tijk_plus_1[5]')
        m.addConstr(Tijk_plus_1[6] == Tijk_plus_1[5] + BackgroundGreen[5] + R, 'Tijk_plus_1[6]')
        m.addConstr(Tijk_plus_1[7] == Tijk_plus_1[6] + BackgroundGreen[6] + R, 'Tijk_plus_1[7]')

        # 執行最佳化
        m.Params.OutputFlag = 0  # 是否詳細印出最佳化過程 0:不印出 1:印出
        m.optimize()

        #取出參數值
        optSignalPlanForCycleK = [0 for i in range(0, 8)]  # 先初始化
        optSignalPlanForCycleK_plus_1 = []
        phaseStartTimeForCycleK = []
        phaseStartTimeForCycleK_plus_1 = []


        ### 設定週期k+1的內容 【開始】 ###
        optSignalPlanForCycleK_plus_1.append(BackgroundCycle)
        for g in BackgroundGreen:
            optSignalPlanForCycleK_plus_1.append(BackgroundGreen[g])
        ### 設定週期k+1的內容 【結束】 ###

        printGijk = {}
        printTijk = {}
        if (m.status == GRB.Status.OPTIMAL):
            optCycleK = m.getVarByName("CYCLE").x
            for v in m.getVars():
                if (v.varName[0:4] in ("Gijk")):
                    printGijk.update({v.varName: int(v.x)}) #print用       #print('% s % g' % (v.varName, v.x))
                    #optSignalPlanForCycleK.append(round(v.x))  #四捨五入取整數
                elif (v.varName[0:5] in ("Tijk[")):
                    printTijk.update({v.varName: int(v.x)})  # print用
                    phaseStartTimeForCycleK.append(round(v.x))  # 四捨五入取整數
                elif (v.varName[0:11] in ("Tijk_plus_1")):
                    phaseStartTimeForCycleK_plus_1.append(round(v.x))

            ### 設定週期k的內容 【開始】 暫時 ###
            for j in range(0, 8):
                # Gijk[j]為gurobi變數物件，Gijk[j].x 表示取出數值
                if (int(Gijk[j].x) == 0):
                    optSignalPlanForCycleK[j] = 0
                else:
                    if j in (0, 1, 2, 4, 5, 6):
                        optSignalPlanForCycleK[j] = phaseStartTimeForCycleK[j+1] - phaseStartTimeForCycleK[j] - R
                    elif j == 3:
                        # Tijk[3] + Gijk[3] + (GijkLengthCal[3] * (1 - Rhoijk[3])) + R - Tijk[0] == C
                        optSignalPlanForCycleK[j] = round(optCycleK - phaseStartTimeForCycleK[3] + phaseStartTimeForCycleK[0] - R)
                    elif j == 7:
                        # Tijk[7] + Gijk[7] + (GijkLengthCal[7] * (1 - Rhoijk[7])) + R - Tijk[4] == C
                        optSignalPlanForCycleK[j] = round(optCycleK - phaseStartTimeForCycleK[7] + phaseStartTimeForCycleK[4] - R)

            ### 設定週期k的內容 【結束】 暫時 ###

            print("----OPT_Tijk---- ")
            print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
                  % (printTijk['Tijk[0]'], printTijk['Tijk[1]'], printTijk['Tijk[2]'], printTijk['Tijk[3]'],
                     printTijk['Tijk[4]'], printTijk['Tijk[5]'], printTijk['Tijk[6]'], printTijk['Tijk[7]']))

            print("----GijkLengthCal---- ")
            print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
                  % (GijkLengthCal[0], GijkLengthCal[1], GijkLengthCal[2], GijkLengthCal[3], GijkLengthCal[4],
                     GijkLengthCal[5], GijkLengthCal[6], GijkLengthCal[7]))

            print("----OPT_Gijk---- ")
            print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
                  % (printGijk['Gijk[0]'], printGijk['Gijk[1]'], printGijk['Gijk[2]'], printGijk['Gijk[3]'], printGijk['Gijk[4]'],
                     printGijk['Gijk[5]'], printGijk['Gijk[6]'], printGijk['Gijk[7]']))

            print('Obj: % g' % m.objVal)
        else:
            m.computeIIS()
            m.write("model.ilp")
            global accumulatedIIS
            accumulatedIIS += 1
            print("******** accumulatedIIS = ", accumulatedIIS)
            print("********----GijkLengthCal---- ")
            print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
                  % (GijkLengthCal[0], GijkLengthCal[1], GijkLengthCal[2], GijkLengthCal[3], GijkLengthCal[4], GijkLengthCal[5], GijkLengthCal[6], GijkLengthCal[7]))

            return False

        print("Optimality ? ", m.status == GRB.Status.OPTIMAL)

    except gp.GurobiError as e:
        print('Error code ' + str(e.errno) + ':' + str(e))

    return optSignalPlanForCycleK,phaseStartTimeForCycleK,\
           optSignalPlanForCycleK_plus_1,phaseStartTimeForCycleK_plus_1

def getVehicleParameters(vehID):
    order = 9999 #暫時給予
    vehType = traci.vehicle.getTypeID(vehID)
    vehSpeed = traci.vehicle.getSpeed(vehID)
    position = traci.vehicle.getPosition(vehID)
    direction = vehID[4:8]
    try:
        nextTLSID = traci.vehicle.getNextTLS(vehID)[0][0]
        nextTLSIndex = traci.vehicle.getNextTLS(vehID)[0][1]
        dist = traci.vehicle.getNextTLS(vehID)[0][2]  # distance
    except IndexError as error:
        #print("IndexError: ",error)
        nextTLSID = None
        nextTLSIndex = 99999
        dist = 99999

    TPxj = dist/Vlim + traci.simulation.getTime() - CycleAccumulated

    if nextTLSIndex in (0, 1, 2):
        phase = 0
        phase = phaseStrDict[phase]
    elif nextTLSIndex in (3, 4):
        phase = 5
        phase = phaseStrDict[phase]
    elif nextTLSIndex in (5, 6, 7):
        phase = 6
        phase = phaseStrDict[phase]
    elif nextTLSIndex in (8, 9):
        phase = 3
        phase = phaseStrDict[phase]
    elif nextTLSIndex in (10, 11, 12):
        phase = 4
        phase = phaseStrDict[phase]
    elif nextTLSIndex in (13, 14):
        phase = 1
        phase = phaseStrDict[phase]
    elif nextTLSIndex in (15, 16, 17):
        phase = 2
        phase = phaseStrDict[phase]
    elif nextTLSIndex in (18, 19):
        phase = 7
        phase = phaseStrDict[phase]
    else:
        phase = None

    if traci.vehicle.getWaitingTime(vehID) > 1:
        isQueue = True
    else:
        isQueue = False

    if vehType == "Bus":
        occupancy = 30
    else:
        occupancy = 1.5

    vehPara = {"vehID":vehID,"order":order,"type":vehType,"isQueue":isQueue, "occupancy":occupancy,
               "vehSpeed":vehSpeed,"nextTLSID":nextTLSID,"phase":phase,"dist":dist,"position":position,
               "direction":direction,"ProjectArrTime(TPxj)":TPxj}
    return vehPara

def setQueue(vehX):
    if (vehX['nextTLSID'] != None): #確認是沒有離開路口的車輛
        if (vehX['phase'] == "J1"):
            if vehX['isQueue'] == True:
                vehQueue["J1"].append(vehX)
            else:
                vehNoneQueue["J1"].append(vehX)
        elif (vehX['phase'] == "J2"):
            if vehX['isQueue'] == True:
                vehQueue["J2"].append(vehX)
            else:
                vehNoneQueue["J2"].append(vehX)
        elif (vehX['phase'] == "J3"):
            if vehX['isQueue'] == True:
                vehQueue["J3"].append(vehX)
            else:
                vehNoneQueue["J3"].append(vehX)
        elif (vehX['phase'] == "J4"):
            if vehX['isQueue'] == True:
                vehQueue["J4"].append(vehX)
            else:
                vehNoneQueue["J4"].append(vehX)
        elif (vehX['phase'] == "J5"):
            if vehX['isQueue'] == True:
                vehQueue["J5"].append(vehX)
            else:
                vehNoneQueue["J5"].append(vehX)
        elif (vehX['phase'] == "J6"):
            if vehX['isQueue'] == True:
                vehQueue["J6"].append(vehX)
            else:
                vehNoneQueue["J6"].append(vehX)
        elif (vehX['phase'] == "J7"):
            if vehX['isQueue'] == True:
                vehQueue["J7"].append(vehX)
            else:
                vehNoneQueue["J7"].append(vehX)
        elif (vehX['phase'] == "J8"):
            if vehX['isQueue'] == True:
                vehQueue["J8"].append(vehX)
            else:
                vehNoneQueue["J8"].append(vehX)

def sortQueueList():

    for J in vehQueue:
        vehQueue[J].sort(key=lambda s: s['dist']) #依照離路口距離排序
        for index in range(len(vehQueue[J])): #填入對應的順序編號
            vehQueue[J][index]['order'] = index + 1 #從1開始編號

    for J in vehNoneQueue:
        vehNoneQueue[J].sort(key=lambda s: s['dist']) #依照離路口距離排序
        for index in range(len(vehNoneQueue[J])): #填入對應的順序編號
            vehNoneQueue[J][index]['order'] = len(vehQueue[J]) + index +1 ##0405再觀察

def cleanList():
    for J in vehNoneQueue:
        vehNoneQueue[J].clear()
    for J in vehQueue:
        vehQueue[J].clear()

    OBU_Dict.clear()
#Traffic Signal related functions

def setPhaseObject(i, optSignalPlan):
    for k in planHorizon:  # k = 0
        for j in phaseStrDict_rev:
            numeric_of_j = phaseStrDict_rev[j]
            if (k == 0):
                IntersectionSignal[i][k][j].setPhaseGreen(optSignalPlan[0][numeric_of_j])  # [0]是綠燈長度(Gijk)
                IntersectionSignal[i][k][j].setStartTime(optSignalPlan[1][numeric_of_j])  # [1]是起始時間(Tijk)
                IntersectionSignal[i][k][j].setClearenceTime(3, 2)
                IntersectionSignal[i][k][j].setPhaseOrder(numeric_of_j)
                #print("IntersectionSignal[", i, "][", k, "][", j, "] =", IntersectionSignal[i][k][j])
            elif (k == 1):
                IntersectionSignal[i][k][j].setPhaseGreen(optSignalPlan[2][numeric_of_j])  # [2]是綠燈長度(Gijk+1)
                IntersectionSignal[i][k][j].setStartTime(optSignalPlan[3][numeric_of_j])  # [3]是起始時間(Tijk+1)
                IntersectionSignal[i][k][j].setClearenceTime(3, 2)
                IntersectionSignal[i][k][j].setPhaseOrder(numeric_of_j)
                #print("IntersectionSignal[", i, "][", k, "][", j, "] =", IntersectionSignal[i][k][j])

def signalPlanInitialize():

    SignalPlan = ([9, 5, 18, 5, 9, 5, 18, 5], [0, 14, 24, 47, 0, 14, 24, 47],
                  [9, 5, 18, 5, 9, 5, 18, 5], [57, 71, 81, 104, 57, 71, 81, 104])
    i = 'I1'
    setPhaseObject(i, SignalPlan)

# contains TraCI control loop
def run():
    step = 0

    # 號誌設定初始化 SignalPlan Initialization
    signalPlanInitialize()
    nowPhase = 1

    while traci.simulation.getMinExpectedNumber() > 0:
        # 迴圈直到所有車輛都已離開路網
        traci.simulationStep()

        #清除VehQueue list和obu list
        cleanList()

        print("########################### step = ", step," ###########################")

        # Vehicle
        vehIDlist = traci.vehicle.getIDList()
        for veh in vehIDlist:
            vehX = getVehicleParameters(veh)
            setQueue(vehX) #將車輛依照分類加入對應的dictionary
            sortQueueList() #排序
            if (vehX['type'] == 'Bus'):
                # 找出車輛型態為公車者，加入OBU字典中，型態：
                # 車輛ID：駕駛建議(RecommendSpeed)物件
                OBU_Dict.update({vehX['vehID']: RS.RecommendSpeed(vehX['vehID'], vehX['type'], vehX['position'],
                                                                  vehX['vehSpeed'], vehX['direction'], vehX['nextTLSID'],
                                                                  vehX['phase'])})
        print("OBU list = ", OBU_Dict)

        passProbThreshold = 0.5  #路口通過機率
        speedFactor = 0.2  #速度上下限限制

        if (len(OBU_Dict) > 0):
            for obu in OBU_Dict:
                OBU_Dict[obu].CycleAccumulated = CycleAccumulated  # 將累計週期長度做引數傳入（權宜之計，之後架構要改）
                OBU_Dict[obu].calPassProb(IntersectionSignal)  # 計算路口通過機率
                passProbDict = OBU_Dict[obu].intersectionPassProb  # 取出路口通過機率結果 ex. intersectionPassProb = {'I1': 1}
                #print("passProbDict = ", passProbDict)
                for i in passProbDict:  # 依序取出每個路口通過機率數值
                    if (passProbDict[i] != False):  # 確認路口通過機率結果不是False
                        if (passProbDict[i] <= passProbThreshold):  # 若路口通過機率 <= 目標機率
                            ##### 計算駕駛建議 #####
                            maxPassProb = passProbDict[i]  # maxPassProb 初始值為以原始速度通過路口的機率
                            speedLimit = OBU_Dict[obu].maxSpeedLimit  # 取出obu的速度上限
                            maxSpeed = int((1 + speedFactor) * speedLimit)  # 設定建議速度上限
                            minSpeed = int((1 - speedFactor) * speedLimit)  # 設定建議速度下限

                            for v in range(minSpeed, maxSpeed):  # 從 minSpeed 到 maxSpeed 窮舉
                                OBU_Dict[obu].currentSpeed = v  # 將目前速度設為v
                                OBU_Dict[obu].calPassProb(IntersectionSignal)  # 以此速度計算路口通過機率
                                newPassProb = OBU_Dict[obu].intersectionPassProb[i]  # 取出計算結果
                                # print("v = ",v)
                                # print("newPassProb = ",newPassProb)
                                if (newPassProb > maxPassProb):  # 若新計算結果大於舊的，則取代之
                                    maxPassProb = newPassProb
                                    OBU_Dict[obu].recommendSpeed = v # 新速度v作為建議速度
                                    ##print("new speed = ", v)
                        else:
                            print("路口[ %s ]通過機率 = %f > 目標機率 %f，不用計算建議速度" % (i, passProbDict[i], passProbThreshold))
                    else:
                        print("passProbDict[ %s ] = False 公車即將離開路網，不用計算建議速度，將速度控制權還給SUMO" % i)
                        # 因不確定是否車輛還有受速度控制，統一下指令將控制權還給SUMO
                        traci.vehicle.setSpeed(obu, -1)  # 引數-1 表示將控制權還給SUMO

                if (OBU_Dict[obu].recommendSpeed != 0):
                    # recommendSpeed != 0 表示窮舉中有速度之通過路口機率有改善
                    optimalSpeed = OBU_Dict[obu].recommendSpeed
                    print("OBU ID = %s +++++++++ Optimal speed = %d m/s ++++++++" % (obu, optimalSpeed))
                    traci.vehicle.setSpeed(obu, optimalSpeed)
                else:
                    # 相較於原始速度之通過機率，窮舉後所有速度之通過機率皆沒有改善
                    # -> 表示所有速度下皆仍在紅燈範圍
                    # 此時應建議以「最慢速度」前進
                    print("所有建議速度均沒有比原速好，建議最小速度")
                    speedLimit = OBU_Dict[obu].maxSpeedLimit
                    minSpeed = (1 - speedFactor) * speedLimit
                    optimalSpeed = minSpeed
                    print("OBU ID = %s +++++++++ Optimal speed = %d m/s ++++++++" % (obu, optimalSpeed))
                    traci.vehicle.setSpeed(obu, optimalSpeed)

        if step in range(0, 7200, 1):
            monitorGijkLength() ### !!更新綠燈執行狀況!!

            optSignalPlan = EXE_GUROBI()
            print("optSignalPlan = ", optSignalPlan)
            if (optSignalPlan != False):

                for i in intersectionList:

                    setPhaseObject(i, optSignalPlan)  # 設定IntersectionSignal裡的phaseObject內容

                TLS_program = PhaseObject.makeLogicObject(IntersectionSignal['I1'][0])  # 產生LogicObject物件，用於控制SUMO號誌

                #### 把duration = 0的phase刪掉 ####
                # del_num = []
                # for num in range(0,len(TLS_program.phases)):
                #     if (TLS_program.phases[num].duration == 0.0):
                #         del_num.append(num)
                # for num in del_num:
                #     del TLS_program.phases[num]

                ##### 找setPhase正確的phase(nowPhase) 開始 #####
                num_of_G = []  # 用於紀錄當下(理應)正在運作的時相

                for ring in range(0, len(currentPhase)):  # len(currentPhase) = 2
                    phase = currentPhase[ring]  # 取出ring 1或2 紀錄正在運作的時相編號
                    if (phasePendingCounter[phase] == R):  # counter必須為R(=5)，代表該時相並非pending狀態(黃燈或全紅)
                        phase_str = phaseStrDict[phase]  # 找到該時相對應的str型態
                        for item in phaseAndGreenStatePairs[phase_str]:  # 把phase - state對應的值取出
                            num_of_G.append(item)
                    else:
                        # 若counter <R 代表該時相仍在轉換階段，不是已經在運行
                        print("時相", phasePendingCounter[phase], "仍在轉換階段，不加入num_of_G")

                #print("num_Of_G = ", num_of_G)  # 印出num_of_G內容

                if (len(num_of_G) == 0):  # len(num_of_G) = 0代表所有時相不是在黃燈就是全紅狀態，
                    # 但這個狀態會在checkNowStateYorAR時攔下來，所以不應該印出本行，若有印出要偵錯!!
                    print("num_Of_G = 0 !")

                allPhaseSet = set([x for x in range(0, 20)])
                noneG_num = allPhaseSet - set(num_of_G)  # noneG_num指不是當下運作的時相，它透過取差集方式取得
                #print("noneG_num = ", noneG_num)
                checkResultCount = 0

                for phaseIndex in range(0, len(TLS_program.phases)):
                    # 從logic物件中的phases集合裡找到一個時相，這個時相的state嚴格滿足num_of_G裡的要求 : 這個State的其他位置皆不能為'G'
                    check1 = False
                    check2 = False
                    for num in (list(noneG_num)):
                        # 從noneG list中取出不該是'G'的位置編號，帶入state測試，若找到有phase的state符合則結束
                        # print(TLS_program.phases[phaseIndex].state[num])
                        if TLS_program.phases[phaseIndex].state[num] != 'G':
                            check1 = True
                        else:
                            check1 = False
                            break
                    for num in num_of_G:
                        if TLS_program.phases[phaseIndex].state[num] in ('G'):
                            check2 = True
                        else:
                            check2 = False
                            break
                    if (check1 and check2):
                        nowPhase = phaseIndex
                        # return
                    else:
                        checkResultCount += 1

                if (checkResultCount == len(TLS_program.phases)):
                    # nowPhase = nowPhase + 1
                    print("*********嚴重錯誤********** 找不到符合的!!!! 啟動方案")
                    for j in currentPhase:  # 選累計綠燈長度小於最短綠的時相
                        num_of_G = []
                        if (GijkLengthCal[j] < Gmin[j]):  # 表示累計綠燈長度尚小於最短綠
                            print("j = ",j)
                            phase_str = phaseStrDict[j]  # 找到該時相對應的str型態
                            for item in phaseAndGreenStatePairs[phase_str]:  # 把phase - state對應的值取出
                                num_of_G.append(item)
                            for phaseIndex in range(0, len(TLS_program.phases)):
                                check = False
                                for num in num_of_G:
                                    if TLS_program.phases[phaseIndex].state[num] in ('G'):
                                        check = True
                                    else:
                                        check = False
                                if (check):
                                    nowPhase = phaseIndex
                                    break

                print("nowPhase (after cal) = ", nowPhase)
                ##### 找setPhase正確的phase(nowPhase) 結束 #####
                ##### 執行計畫 #####
                traci.trafficlight.setProgramLogic('I1', TLS_program)
                traci.trafficlight.setProgram('I1', '1')
                traci.trafficlight.setPhase('I1', nowPhase)


        print("----GijkResult---- ")
        print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
              % (GijkResult[0], GijkResult[1], GijkResult[2], GijkResult[3], GijkResult[4],
                 GijkResult[5], GijkResult[6], GijkResult[7]))

        print("----phaseIsEnd---- ")
        print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
              % (phaseIsEnd[0], phaseIsEnd[1], phaseIsEnd[2], phaseIsEnd[3], phaseIsEnd[4],
                 phaseIsEnd[5], phaseIsEnd[6], phaseIsEnd[7]))

        print("NowProgram = ", traci.trafficlight.getProgram('I1'),
              # "/ AllProgramLogic = ",traci.trafficlight.getAllProgramLogics('I1'),
              # "/ NowPhaseName = ", traci.trafficlight.getPhaseName('I1'),
              "/ NowPhase = ", traci.trafficlight.getPhase('I1'),
              "/ NowPhaseDuration = ", traci.trafficlight.getPhaseDuration('I1'),
              "/ NowState = ", traci.trafficlight.getRedYellowGreenState('I1'),
              "/ NextSwitch = ", traci.trafficlight.getNextSwitch('I1'),
              )
        program = traci.trafficlight.getAllProgramLogics('I1')[1]
        print("AllProgramLogic = ", program)
        index = 0
        for phase in program.phases:
            print("[%d] : %s %s" % (index, int(phase.duration), phase.state))
            index += 1

        if (step == 7200):
            print("end accumulatedIIS = ", accumulatedIIS)
        step += 1

    traci.close()
    sys.stdout.flush()


# main entry point
if __name__ == "__main__":
    options = get_options()

    # check binary
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # traci starts sumo as a subprocess and then this script connects and runs
    sumo_start = [sumoBinary, "-c", "thesis_single.sumocfg", "--tripinfo-output", "thesis_single_priority_tripInfo.xml", "--random", "--seed", "8"]
    traci.start(sumo_start)
    run()
