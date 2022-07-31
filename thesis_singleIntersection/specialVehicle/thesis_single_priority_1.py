
import os
import sys
import optparse


#from thesis import PhaseObject
from thesis import RSUObject
from thesis import SignalPlanObject
from thesis import OBUObject
from thesis import SignalOptModule

# C:\Users\WangRabbit\AppData\Local\Programs\Python\Python37\Lib\thesis

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


# 有安裝OBU車輛列表
OBU_Dict = {}

#模擬設定(最佳化時段區間)
planHorizon = [0,1]

# 路口資料
RSUs = dict()
signalOPTs = dict()


def setPhaseObject(i, signalPlan):
    #I = RSU物件

    adaptivePlan = SignalPlanObject.SignalPlan()
    backPlan = SignalPlanObject.SignalPlan()  # 實體化

    for k in planHorizon:  # k = 0
        if (k == 0):  # [0]是綠燈長度(Gijk)  # [1]是起始時間(Tijk)
            J1 = SignalPlanObject.Phase(phaseID='J1', phaseOrder=0, startTime=signalPlan[1][0], green=signalPlan[0][0], yellow=3, allRed=2)
            J2 = SignalPlanObject.Phase(phaseID='J2', phaseOrder=1, startTime=signalPlan[1][1], green=signalPlan[0][1], yellow=3, allRed=2)
            J3 = SignalPlanObject.Phase(phaseID='J3', phaseOrder=2, startTime=signalPlan[1][2], green=signalPlan[0][2], yellow=3, allRed=2)
            J4 = SignalPlanObject.Phase(phaseID='J4', phaseOrder=3, startTime=signalPlan[1][3], green=signalPlan[0][3], yellow=3, allRed=2)
            J5 = SignalPlanObject.Phase(phaseID='J5', phaseOrder=4, startTime=signalPlan[1][4], green=signalPlan[0][4], yellow=3, allRed=2)
            J6 = SignalPlanObject.Phase(phaseID='J6', phaseOrder=5, startTime=signalPlan[1][5], green=signalPlan[0][5], yellow=3, allRed=2)
            J7 = SignalPlanObject.Phase(phaseID='J7', phaseOrder=6, startTime=signalPlan[1][6], green=signalPlan[0][6], yellow=3, allRed=2)
            J8 = SignalPlanObject.Phase(phaseID='J8', phaseOrder=7, startTime=signalPlan[1][7], green=signalPlan[0][7], yellow=3, allRed=2)
            R = J1.yellow + J1.allRed
            CYCLE = J1.green + J2.green + J3.green + J4.green + R * 4

            adaptivePlan.setAllParameters(planID='0', order='00', offset=0, cycle=CYCLE, phases={"J1": J1, "J2": J2, "J3": J3, "J4": J4,
                                                                                                 "J5": J5, "J6": J6, "J7": J7, "J8": J8})

            print("adaptivePlan = ", adaptivePlan)
        elif (k == 1):

            J1 = SignalPlanObject.Phase(phaseID='J1', phaseOrder=0, startTime=signalPlan[3][0],
                                          green=signalPlan[2][0], yellow=3, allRed=2)
            J2 = SignalPlanObject.Phase(phaseID='J2', phaseOrder=1, startTime=signalPlan[3][1],
                                          green=signalPlan[2][1], yellow=3, allRed=2)
            J3 = SignalPlanObject.Phase(phaseID='J3', phaseOrder=2, startTime=signalPlan[3][2],
                                          green=signalPlan[2][2], yellow=3, allRed=2)
            J4 = SignalPlanObject.Phase(phaseID='J4', phaseOrder=3, startTime=signalPlan[3][3],
                                          green=signalPlan[2][3], yellow=3, allRed=2)
            J5 = SignalPlanObject.Phase(phaseID='J5', phaseOrder=4, startTime=signalPlan[3][4],
                                          green=signalPlan[2][4], yellow=3, allRed=2)
            J6 = SignalPlanObject.Phase(phaseID='J6', phaseOrder=5, startTime=signalPlan[3][5],
                                          green=signalPlan[2][5], yellow=3, allRed=2)
            J7 = SignalPlanObject.Phase(phaseID='J7', phaseOrder=6, startTime=signalPlan[3][6],
                                          green=signalPlan[2][6], yellow=3, allRed=2)
            J8 = SignalPlanObject.Phase(phaseID='J8', phaseOrder=7, startTime=signalPlan[3][7],
                                          green=signalPlan[2][7], yellow=3, allRed=2)

            CYCLE = J1.green + J2.green + J3.green + J4.green + R * 4

            backPlan.setAllParameters(planID='0', order='00', offset=0, cycle=CYCLE,
                                          phases={"J1": J1, "J2": J2, "J3": J3, "J4": J4,
                                                  "J5": J5, "J6": J6, "J7": J7, "J8": J8})

            print("backPlan = ", backPlan)

    plan = [adaptivePlan, backPlan]  # 組成plan
    i.setPlan(plan)  # 設定RSU.plan

def initialization():
    # 初始化: 新增RSU
    I1 = RSUObject.RSU(ID='I1', location=[500, 0])

    RSUs.update({'I1': I1})

    Plan = ([38, 12, 36, 14, 38, 12, 36, 14], [0, 43, 60, 101, 0, 43, 60, 101],
            [38, 12, 36, 14, 38, 12, 36, 14], [120, 163, 180, 221, 120, 163, 180, 221])

    for rsu in RSUs:
        setPhaseObject(RSUs[rsu], Plan)

    OPT1 = SignalOptModule.SignalOPT(RSU=I1)
    signalOPTs.update({'I1': OPT1})

# contains TraCI control loop
def run():
    step = 0

    # 號誌設定初始化 SignalPlan Initialization
    initialization()
    nowPhase = 0

    while traci.simulation.getMinExpectedNumber() > 0:
        # 迴圈直到所有車輛都已離開路網
        traci.simulationStep()

        print("########################### step = ", step, " ###########################")

        #清除obu list
        OBU_Dict.clear()
        for rsu in RSUs:  # RSUs = ['rsu':'RSU object']
            RSUs[rsu].cleanQueueList()  # 清除veh queue list

            # Vehicle
            vehIDlist = traci.vehicle.getIDList()  # 取出路網中所有車輛ID
            for veh in vehIDlist:  # 個別抽出車輛ID

                # 取得該車輛ID的詳細參數  getVehicleParameters
                # Input: VehicleID (String) / Output:  {"vehID": vehID, "order": order, "type": vehType ... }
                vehX = RSUs[rsu].getVehicleParameters(veh)
                # print("vehID = %s speed = %f TPxj = %f dist = %d nextTLSID = %s" % (
                # vehX['vehID'], vehX['vehSpeed'], vehX['ProjectArrTime(TPxj)'], vehX['dist'], vehX['nextTLSID']))

                if vehX['dist'] <= 300: #進入辨識範圍的車輛才加入
                    RSUs[rsu].setQueue(vehX)  # 將車輛依照分類加入對應的dictionary
                else:
                    pass

                if (vehX['type'] == 'Bus' or vehX['type'] == 'Special'):
                    # 找出車輛型態為公車者，加入OBU字典中，型態：
                    # 車輛ID：駕駛建議(RecommendSpeed)物件

                    OBU_Dict.update({vehX['vehID']: OBUObject.OBU(ID=vehX['vehID'], vehType=vehX['type'], pos=vehX['position'], currentSpeed=vehX['vehSpeed'], direction=vehX['direction'],
                                         nextTLS=vehX['nextTLSID'], targetPhase=vehX['phase'])})

            RSUs[rsu].sortQueueList()  # 排序Queuelist 和 noneQueuelist: 將車輛依離路口距離編號(order x)

        # 號誌最佳化
        if step in range(0, 7500, 1):
            for opt in signalOPTs:
                optSignalPlan = signalOPTs[opt].EXE_GUROBI()
                print("optSignalPlan = ", optSignalPlan)

                if (optSignalPlan != False):
                    tijkResult = optSignalPlan[4]  #tijk為 optSinglPlan[4]
                    for rsu in RSUs:
                        setPhaseObject(RSUs[rsu], optSignalPlan)  # 設定IntersectionSignal裡的phaseObject內容
                else:  # optSignalPlan = False
                    print("optSignalPlan = False !")
                    tijkResult = [1, 1, 1, 1, 1, 1, 1, 1]  #tijk設定為[1,1,1,1,1,1,1,1] 使logic object設定為綠燈
                    print("tijkResult = ", tijkResult)

                currentPhase = signalOPTs[opt].currentPhase
                phasePendingCounter = signalOPTs[opt].phasePendingCounter

                TLS_program = SignalPlanObject.makeLogicObject(currentPhase, tijkResult, phasePendingCounter)
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
        # 駕駛建議
        if (len(OBU_Dict) > 0):
            print("OBU_DICT = ", OBU_Dict)
            for obu in OBU_Dict:
                OBU_Dict[obu].start(RSUs)  # input: RSU物件 #啟動計算駕駛建議

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
    sumo_start = [sumoBinary, "-c", "thesis_single_peakHour_vc0.9.sumocfg", "--tripinfo-output", "thesis_single_priority_tripInfo_1.xml", "--random", "--seed", "8"] #"--random", "--seed", "8"
    traci.start(sumo_start)
    run()
