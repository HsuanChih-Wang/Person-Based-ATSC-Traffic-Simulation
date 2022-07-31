
import os
import sys
import optparse
from argparse import ArgumentParser

import math
import thesis.PhaseObject as PhaseObject
import thesis.RecommendSpeed as RS
# C:\Users\WangRabbit\AppData\Local\Programs\Python\Python37\Lib\thesis

#from thesis import PhaseObject
from thesis import RSUObject
from thesis import SignalPlanObject
from thesis import OBUObject
from thesis import SignalOptModule

from scipy import stats

# we need to import some python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # Checks for the binary in environ vars
import traci

# 有安裝OBU車輛列表
OBU_Dict = {}

# 路口資料
RSUs = dict()
signalOPTs = dict()

#模擬設定(最佳化時段區間)
planHorizon = [0,1]

def setPhaseObject(i, signalPlan):
    #I = RSU物件

    adaptivePlan = SignalPlanObject.SignalPlan()
    backPlan = SignalPlanObject.SignalPlan()  # 實體化

    for k in planHorizon:  # k = 0
        if (k == 0):  # [0]是綠燈長度(Gijk)  # [1]是起始時間(Tijk)
            J1 = SignalPlanObject.Phase(phaseID='J1', phaseOrder=0, startTime=signalPlan[2][0], green=signalPlan[0][0], Gmin=signalPlan[1][0], Gmax=200, yellow=3, allRed=2)
            J2 = SignalPlanObject.Phase(phaseID='J2', phaseOrder=1, startTime=signalPlan[2][1], green=signalPlan[0][1], Gmin=signalPlan[1][0], Gmax=200, yellow=3, allRed=2)
            J3 = SignalPlanObject.Phase(phaseID='J3', phaseOrder=2, startTime=signalPlan[2][2], green=signalPlan[0][2], Gmin=signalPlan[1][0], Gmax=200, yellow=3, allRed=2)
            J4 = SignalPlanObject.Phase(phaseID='J4', phaseOrder=3, startTime=signalPlan[2][3], green=signalPlan[0][3], Gmin=signalPlan[1][0], Gmax=200, yellow=3, allRed=2)
            J5 = SignalPlanObject.Phase(phaseID='J5', phaseOrder=4, startTime=signalPlan[2][4], green=signalPlan[0][4], Gmin=signalPlan[1][0], Gmax=200, yellow=3, allRed=2)
            J6 = SignalPlanObject.Phase(phaseID='J6', phaseOrder=5, startTime=signalPlan[2][5], green=signalPlan[0][5], Gmin=signalPlan[1][0], Gmax=200, yellow=3, allRed=2)
            J7 = SignalPlanObject.Phase(phaseID='J7', phaseOrder=6, startTime=signalPlan[2][6], green=signalPlan[0][6], Gmin=signalPlan[1][0], Gmax=200, yellow=3, allRed=2)
            J8 = SignalPlanObject.Phase(phaseID='J8', phaseOrder=7, startTime=signalPlan[2][7], green=signalPlan[0][7], Gmin=signalPlan[1][0], Gmax=200, yellow=3, allRed=2)
            R = J1.yellow + J1.allRed
            CYCLE = J1.green + J2.green + J3.green + J4.green + R * 4

            adaptivePlan.setAllParameters(planID='0', order='00', offset=0, cycle=CYCLE, phases={"J1": J1, "J2": J2, "J3": J3, "J4": J4,
                                                                                                 "J5": J5, "J6": J6, "J7": J7, "J8": J8})

            print("adaptivePlan = ", adaptivePlan)
        elif (k == 1):

            J1 = SignalPlanObject.Phase(phaseID='J1', phaseOrder=0, startTime=signalPlan[5][0], green=signalPlan[3][0], Gmin=signalPlan[4][0], Gmax=200, yellow=3, allRed=2)
            J2 = SignalPlanObject.Phase(phaseID='J2', phaseOrder=1, startTime=signalPlan[5][1], green=signalPlan[3][1], Gmin=signalPlan[4][1], Gmax=200, yellow=3, allRed=2)
            J3 = SignalPlanObject.Phase(phaseID='J3', phaseOrder=2, startTime=signalPlan[5][2], green=signalPlan[3][2], Gmin=signalPlan[4][2], Gmax=200, yellow=3, allRed=2)
            J4 = SignalPlanObject.Phase(phaseID='J4', phaseOrder=3, startTime=signalPlan[5][3], green=signalPlan[3][3], Gmin=signalPlan[4][3], Gmax=200, yellow=3, allRed=2)
            J5 = SignalPlanObject.Phase(phaseID='J5', phaseOrder=4, startTime=signalPlan[5][4], green=signalPlan[3][4], Gmin=signalPlan[4][4], Gmax=200, yellow=3, allRed=2)
            J6 = SignalPlanObject.Phase(phaseID='J6', phaseOrder=5, startTime=signalPlan[5][5], green=signalPlan[3][5], Gmin=signalPlan[4][5], Gmax=200, yellow=3, allRed=2)
            J7 = SignalPlanObject.Phase(phaseID='J7', phaseOrder=6, startTime=signalPlan[5][6], green=signalPlan[3][6], Gmin=signalPlan[4][6], Gmax=200, yellow=3, allRed=2)
            J8 = SignalPlanObject.Phase(phaseID='J8', phaseOrder=7, startTime=signalPlan[5][7], green=signalPlan[3][7], Gmin=signalPlan[4][7], Gmax=200, yellow=3, allRed=2)
            R = J1.yellow + J1.allRed
            CYCLE = J1.green + J2.green + J3.green + J4.green + R * 4

            backPlan.setAllParameters(planID='0', order='00', offset=0, cycle=CYCLE,
                                          phases={"J1": J1, "J2": J2, "J3": J3, "J4": J4,
                                                  "J5": J5, "J6": J6, "J7": J7, "J8": J8})

            print("backPlan = ", backPlan)

    plan = [adaptivePlan, backPlan]  # 組成plan
    i.setPlan(plan)  # 設定RSU.plan


def initialization():
    # 初始化: 新增RSU
    I1 = RSUObject.RSU(ID='I1', location=[500, 0], detectionRange=200)
    I2 = RSUObject.RSU(ID='I2', location=[700, 0], detectionRange=200)

    RSUs.update({'I1': I1})
    RSUs.update({'I2': I2})
    # Green length / Gmin / StartTime
    I1_Plan = ([38, 12, 36, 14, 38, 12, 36, 14], [10, 10, 10, 10, 10, 10, 10, 10], [0, 43, 60, 101, 0, 43, 60, 101],
              [38, 12, 36, 14, 38, 12, 36, 14], [10, 10, 10, 10, 10, 10, 10, 10], [120, 163, 180, 221, 120, 163, 180, 221])
    I2_Plan = ([32, 0, 68, 0, 0, 0, 68, 5], [10, 0, 10, 0, 0, 0, 10, 3], [0, 37, 37, 110, 0, 37, 37, 110],
              [32, 0, 68, 0, 0, 0, 68, 5], [10, 0, 10, 0, 0, 0, 10, 3], [120, 157, 157, 230, 120, 157, 157, 230])

    setPhaseObject(RSUs['I1'], I1_Plan)
    setPhaseObject(RSUs['I2'], I2_Plan)

    OPT1 = SignalOptModule.SignalOPT(RSU=I1)
    OPT2 = SignalOptModule.SignalOPT(RSU=I2)
    signalOPTs.update({'I1': OPT1})
    signalOPTs.update({'I2': OPT2})

# contains TraCI control loop
def run():
    step = 0
    initialization()
    while traci.simulation.getMinExpectedNumber() > 0:
        # 迴圈直到所有車輛都已離開路網
        traci.simulationStep()
        print("########################### step = ", step, " ###########################")
        # 清除obu list
        OBU_Dict.clear()

        vehIDlist = traci.vehicle.getIDList()  # 取出路網中所有車輛ID
        for veh in vehIDlist:  # 個別抽出車輛ID
            for rsu in ['I2']: #RSUs
                RSUs[rsu].cleanQueueList()  # 清除veh queue list
                # 取得該車輛ID的詳細參數  getVehicleParameters
                # Input: VehicleID (String) / Output:  {"vehID": vehID, "order": order, "type": vehType ... }
                vehX = RSUs[rsu].getVehicleParameters(veh)
                if (vehX['nextTLSID'] == rsu and vehX['dist'] <= RSUs[rsu].detectionRange):
                    print("vehX = %s nextTLSID = %s dist = %s" %(vehX['vehID'], vehX['nextTLSID'], vehX['dist']))
                    RSUs[rsu].setQueue(vehX)  # 將車輛依照分類加入對應的dictionary

                if (vehX['type'] == 'Bus'):
                    # 找出車輛型態為公車者，加入OBU字典中，型態：
                    # 車輛ID：駕駛建議(RecommendSpeed)物件

                    OBU_Dict.update({vehX['vehID']: OBUObject.OBU(ID=vehX['vehID'], vehType=vehX['type'], pos=vehX['position'], currentSpeed=vehX['vehSpeed'], direction=vehX['direction'],
                                         nextTLS=vehX['nextTLSID'], targetPhase=vehX['phase'])})
                    print("OBU_Dict = ", OBU_Dict)

                RSUs[rsu].sortQueueList()  # 排序Queuelist 和 noneQueuelist: 將車輛依離路口距離編號(order x)

        # 號誌最佳化
        if step in range(0, 7500, 1):
            for opt in ['I2']: #signalOPTs
                optSignalPlan = signalOPTs[opt].EXE_GUROBI()
                print("optSignalPlan = ", optSignalPlan)

                if (optSignalPlan != False):
                    tijkResult = optSignalPlan[6]  # tijk為 optSinglPlan[6]
                    # for rsu in ['I2']:
                    #     setPhaseObject(RSUs[rsu], optSignalPlan)  # 設定IntersectionSignal裡的phaseObject內容
                else:  # optSignalPlan = False
                    print("optSignalPlan = False !")
                    tijkResult = [1, 1, 1, 1, 1, 1, 1, 1]  # tijk設定為[1,1,1,1,1,1,1,1] 使logic object設定為綠燈
                    print("tijkResult = ", tijkResult)

                currentPhase = signalOPTs[opt].currentPhase
                phasePendingCounter = signalOPTs[opt].phasePendingCounter

                TLS_program = SignalPlanObject.makeLogicObject(signalOPTs[opt].RSU.RSU_ID, currentPhase, tijkResult, phasePendingCounter)
                print("TLS_program = ", TLS_program)

                ##### 執行計畫 #####
                traci.trafficlight.setProgramLogic(signalOPTs[opt].RSU.RSU_ID, TLS_program)
                traci.trafficlight.setProgram(signalOPTs[opt].RSU.RSU_ID, '1')  # '1' = 適應性時制計畫
                traci.trafficlight.setPhase(signalOPTs[opt].RSU.RSU_ID, 0)  # logicObject 只有一個phase(編號=0) 所以 phase = 0

                print("NowProgram = ", traci.trafficlight.getProgram('I1'),
                      # "/ AllProgramLogic = ",traci.trafficlight.getAllProgramLogics('I1'),
                      # "/ NowPhaseName = ", traci.trafficlight.getPhaseName('I1'),
                      "/ NowPhase = ", traci.trafficlight.getPhase('I1'),
                      "/ NowPhaseDuration = ", traci.trafficlight.getPhaseDuration('I1'),
                      "/ NowState = ", traci.trafficlight.getRedYellowGreenState('I1'),
                      "/ NextSwitch = ", traci.trafficlight.getNextSwitch('I1'), )


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
    sumo_start = [sumoBinary, "-c", "thesis_multiple_vc0.9.sumocfg", "--tripinfo-output", "thesis_single_noPriority_tripInfo.xml"] #"--random", "--seed", "8"
                # random 使SUMO隨機挑選seed，會覆蓋--seed效果

    traci.start(sumo_start)
    run()
