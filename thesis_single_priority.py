
import os
import sys
import optparse


#from thesis import PhaseObject
from packages import RSUObject
from packages import SignalPlanObject
from packages import OBUObject
from packages import SignalOptModule

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
TLS_index_pair = {0: {"phase": 'J1', "direction": 'South'}, 1: {"phase": 'J1', "direction": 'South'}, 2: {"phase": 'J1', "direction": 'South'},
                  3: {"phase": 'J6', "direction": 'South'}, 4: {"phase": 'J6', "direction": 'South'},
                  5: {"phase": 'J7', "direction": 'West'}, 6: {"phase": 'J7', "direction": 'West'}, 7: {"phase": 'J7', "direction": 'West'},
                  8: {"phase": 'J4', "direction": 'West'}, 9: {"phase": 'J4', "direction": 'West'},
                  10: {"phase": 'J5', "direction": 'North'}, 11: {"phase": 'J5', "direction": 'North'}, 12: {"phase": 'J5', "direction": 'North'},
                  13: {"phase": 'J2', "direction": 'North'}, 14: {"phase": 'J2', "direction": 'North'},
                  15: {"phase": 'J3', "direction": 'East'}, 16: {"phase": 'J3', "direction": 'East'}, 17: {"phase": 'J3', "direction": 'East'},
                  18: {"phase": 'J8', "direction": 'East'}, 19: {"phase": 'J8', "direction": 'East'}}

Plan = ([24, 8, 20, 13, 24, 8, 20, 13], [0, 29, 42, 67, 0, 29, 42, 67],
        [24, 8, 20, 13, 24, 8, 20, 13], [85, 114, 127, 152, 85, 114, 127, 152])

minGreen = ([10, 5, 10, 5, 10, 5, 10, 5], [10, 5, 10, 5, 10, 5, 10, 5])


# 有安裝OBU車輛列表
OBU_Dict = {}

#模擬設定(最佳化時段區間)
planHorizon = [0,1]

# 路口資料
RSUs = dict()
signalOPTs = dict()

def setPhaseObject(i, signalPlan, minGreen):
    #I = RSU物件

    adaptivePlan = SignalPlanObject.SignalPlan()
    backPlan = SignalPlanObject.SignalPlan()  # 實體化

    for k in planHorizon:  # k = 0
        if (k == 0):  # [0]是綠燈長度(Gijk)  # [1]是起始時間(Tijk)
            J1 = SignalPlanObject.Phase(phaseID='J1', phaseOrder=0, startTime=signalPlan[1][0], green=signalPlan[0][0], Gmin=minGreen[0][0], Gmax=200, yellow=3, allRed=2)
            J2 = SignalPlanObject.Phase(phaseID='J2', phaseOrder=1, startTime=signalPlan[1][1], green=signalPlan[0][1], Gmin=minGreen[0][1], Gmax=200, yellow=3, allRed=2)
            J3 = SignalPlanObject.Phase(phaseID='J3', phaseOrder=2, startTime=signalPlan[1][2], green=signalPlan[0][2], Gmin=minGreen[0][2], Gmax=200, yellow=3, allRed=2)
            J4 = SignalPlanObject.Phase(phaseID='J4', phaseOrder=3, startTime=signalPlan[1][3], green=signalPlan[0][3], Gmin=minGreen[0][3], Gmax=200, yellow=3, allRed=2)
            J5 = SignalPlanObject.Phase(phaseID='J5', phaseOrder=4, startTime=signalPlan[1][4], green=signalPlan[0][4], Gmin=minGreen[0][4], Gmax=200, yellow=3, allRed=2)
            J6 = SignalPlanObject.Phase(phaseID='J6', phaseOrder=5, startTime=signalPlan[1][5], green=signalPlan[0][5], Gmin=minGreen[0][5], Gmax=200, yellow=3, allRed=2)
            J7 = SignalPlanObject.Phase(phaseID='J7', phaseOrder=6, startTime=signalPlan[1][6], green=signalPlan[0][6], Gmin=minGreen[0][6], Gmax=200, yellow=3, allRed=2)
            J8 = SignalPlanObject.Phase(phaseID='J8', phaseOrder=7, startTime=signalPlan[1][7], green=signalPlan[0][7], Gmin=minGreen[0][7], Gmax=200, yellow=3, allRed=2)
            R = J1.yellow + J1.allRed
            CYCLE = J1.green + J2.green + J3.green + J4.green + R * 4

            adaptivePlan.setAllParameters(planID='0', order='00', offset=0, cycle=CYCLE, phases={"J1": J1, "J2": J2, "J3": J3, "J4": J4,
                                                                                                 "J5": J5, "J6": J6, "J7": J7, "J8": J8})

            print("adaptivePlan = ", adaptivePlan)
        elif (k == 1):

            J1 = SignalPlanObject.Phase(phaseID='J1', phaseOrder=0, startTime=signalPlan[3][0], green=signalPlan[2][0], Gmin=minGreen[1][0], Gmax=200, yellow=3, allRed=2)
            J2 = SignalPlanObject.Phase(phaseID='J2', phaseOrder=1, startTime=signalPlan[3][1], green=signalPlan[2][1], Gmin=minGreen[1][1], Gmax=200, yellow=3, allRed=2)
            J3 = SignalPlanObject.Phase(phaseID='J3', phaseOrder=2, startTime=signalPlan[3][2], green=signalPlan[2][2], Gmin=minGreen[1][2], Gmax=200, yellow=3, allRed=2)
            J4 = SignalPlanObject.Phase(phaseID='J4', phaseOrder=3, startTime=signalPlan[3][3], green=signalPlan[2][3], Gmin=minGreen[1][3], Gmax=200, yellow=3, allRed=2)
            J5 = SignalPlanObject.Phase(phaseID='J5', phaseOrder=4, startTime=signalPlan[3][4], green=signalPlan[2][4], Gmin=minGreen[1][4], Gmax=200, yellow=3, allRed=2)
            J6 = SignalPlanObject.Phase(phaseID='J6', phaseOrder=5, startTime=signalPlan[3][5], green=signalPlan[2][5], Gmin=minGreen[1][5], Gmax=200, yellow=3, allRed=2)
            J7 = SignalPlanObject.Phase(phaseID='J7', phaseOrder=6, startTime=signalPlan[3][6], green=signalPlan[2][6], Gmin=minGreen[1][6], Gmax=200, yellow=3, allRed=2)
            J8 = SignalPlanObject.Phase(phaseID='J8', phaseOrder=7, startTime=signalPlan[3][7], green=signalPlan[2][7], Gmin=minGreen[1][7], Gmax=200, yellow=3, allRed=2)
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

    I1 = RSUObject.RSU(ID='I1', location=[500, 0], detectionRange=300)

    RSUs.update({'I1': I1})

    setPhaseObject(i=RSUs['I1'], signalPlan=Plan, minGreen=minGreen)

    OPT1 = SignalOptModule.SignalOPT(RSU=I1)
    signalOPTs.update({'I1': OPT1})

# contains TraCI control loop
def run():
    step = 0

    # 號誌設定初始化 SignalPlan Initialization
    initialization()

    while traci.simulation.getMinExpectedNumber() > 0:
        # 迴圈直到所有車輛都已離開路網
        traci.simulationStep()

        print("########################### step = ", step, " ###########################")

        #### 路口RSU設定 ####

        for rsu in RSUs:
            RSUs[rsu].start()

        ########## 公車OBU設定 ##########
        # 清除obu list
        OBU_Dict.clear()

        vehIDlist = traci.vehicle.getIDList()  # 取出路網中所有車輛ID

        for veh in vehIDlist:
            vehXtype = traci.vehicle.getTypeID(veh)

            if (vehXtype == 'Bus'):
                # 找出車輛型態為公車者，加入OBU字典中，型態：
                # 車輛ID：駕駛建議(RecommendSpeed)物件

                try:
                    nextTLSID = traci.vehicle.getNextTLS(veh)[0][0]  # String: 'I1', 'I2', 'I3'....
                    nextTLSIndex = traci.vehicle.getNextTLS(veh)[0][1]  # Int
                    dist = traci.vehicle.getNextTLS(veh)[0][2]  # distance
                    phase = TLS_index_pair[nextTLSIndex]['phase']
                    direction = TLS_index_pair[nextTLSIndex]['direction']
                except IndexError as error:
                    nextTLSID = None
                    nextTLSIndex = 99999
                    dist = 99999
                    phase = None
                    direction = 'None'

                vehType = traci.vehicle.getTypeID(veh)
                vehSpeed = traci.vehicle.getSpeed(veh)
                position = traci.vehicle.getPosition(veh)

                OBU_Dict.update({veh: OBUObject.OBU(ID=veh, vehType=vehType, pos=position,
                                                    currentSpeed=vehSpeed, direction=direction,
                                                    nextTLS=nextTLSID, targetPhase=phase)})
            else:
                # 非公車，不用加入
                pass

        print("OBU_Dict = ", OBU_Dict)

        # 號誌最佳化
        #if step in range(0, 7500, 1):
        for opt in signalOPTs:
            # opt = 'I1' or 'I2'
            optSignalPlan = signalOPTs[opt].EXE_GUROBI()
            print("optSignalPlan = ", optSignalPlan)

            if (optSignalPlan != False):
                tijkResult = optSignalPlan[4]  #tijk為 optSinglPlan[4]
                print("tijkResult = ", tijkResult)

                #　０ = optSignalPlanForCycleK, 1 = phaseStartTimeForCycleK, 2 = optSignalPlanForCycleK_plus_1, 3 = phaseStartTimeForCycleK_plus_1, 4 = tijkResult
                Plan = (optSignalPlan[0], optSignalPlan[1], optSignalPlan[2], optSignalPlan[3])
                # 把結果塞回plan
                setPhaseObject(i=RSUs[opt], signalPlan=Plan, minGreen=minGreen)

                # RSUs[opt].plan[0].phases['J1'].setPhaseGreen(optSignalPlanForCycleK[0])
                # RSUs[opt].plan[0].phases['J2'].setPhaseGreen(optSignalPlanForCycleK[1])
                # RSUs[opt].plan[0].phases['J3'].setPhaseGreen(optSignalPlanForCycleK[2])
                # RSUs[opt].plan[0].phases['J4'].setPhaseGreen(optSignalPlanForCycleK[3])
                # RSUs[opt].plan[0].phases['J5'].setPhaseGreen(optSignalPlanForCycleK[4])
                # RSUs[opt].plan[0].phases['J6'].setPhaseGreen(optSignalPlanForCycleK[5])
                # RSUs[opt].plan[0].phases['J7'].setPhaseGreen(optSignalPlanForCycleK[6])
                # RSUs[opt].plan[0].phases['J8'].setPhaseGreen(optSignalPlanForCycleK[7])


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

        outputFile_StepThr = 890
        outputFileName = "signalResult.txt"

        # 駕駛建議
        if (len(OBU_Dict) > 0):
            print("OBU_DICT = ", OBU_Dict)
            for obu in OBU_Dict:
                OBU_Dict[obu].start(RSUs)  # input: RSU物件 #啟動計算駕駛建議
                # if (traci.simulation.getTime() >= outputFile_StepThr):
                #     file = open(outputFileName, "a")
                #     file.write("OBU_ID =  %s / speed = %f\n"
                #                % (OBU_Dict[obu].OBU_ID, traci.vehicle.getSpeed(OBU_Dict[obu].OBU_ID)))

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

    # traci starts sumo as a subprocess and then this script connects and runs # --tripinfo-output
    sumo_start = [sumoBinary, "-c", "thesis_single_peakHour_vc0.9.sumocfg",
                  "--tripinfo-output", "thesis_single_priority_tripInfo.xml",
                  "--seed", "8",
                  "--start"] #"--random", "--seed", "8"
    traci.start(sumo_start)
    run()
