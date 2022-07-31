import os
import sys
import optparse
import math

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

# contains TraCI control loop
def run():
    step=0
    remainTime = {"J1":99,"J2":99,"J3":99,"J4":99} #四個路口剩餘秒數
    remainTimeMSG = {"J1":99,"J2":99,"J3":99,"J4":99}
    originVehicleID = "9999";
    phaseOrderName = ["幹道綠燈", "幹道黃燈", "幹道全紅", "支道綠燈", "支道黃燈", "支道全紅"]  #六個分相
    intersectionOrder = ["J1","J2","J3","J4"]
    nowPhase = {"J1":0,"J2":0,"J3":0,"J4":0} #各路口當下時相
    intersectionRedTime = {"J1":30,"J2":40,"J3":45,"J4":35}
    priorityStatus = {"J1": [False,99], "J2": [False,99], "J3": [False,99], "J4": [False,99]}  # 四個路口優先狀態
    # {路口ID {狀態,優先的時相代號}}

    #道路與車輛參數
    vehicleID = "0"
    busSpeed = 11 # 單位: m/s
    edgeLength = {"L1":100,"L2":300,"L3":160,"L4":200,"L5":120} #5段edge的長度 單位:m
    intersectionPos = {"J1":100,"J2":400,"J3":560,"J4":880}
    busStopWaitingTime = 20 #原設定20秒
    busStopLostTime = 5

    #號誌參數
    priorityMaxTime = 10

    Emg_vehicle = ["",0,0]
    nextTLS = ["",0,0,""]
    tls_origin = {"J1": "", "J2": "", "J3": "", "J4": ""}
    tls_origin_LOCK = False

    while traci.simulation.getMinExpectedNumber() > 0:
        #迴圈直到所有車輛都已離開路網
        traci.simulationStep()

        vehicleID_2 = traci.inductionloop.getLastStepVehicleIDs("02")

        if len(vehicleID_2) > 0 and ("Emg_vehicle" in vehicleID_2[0]):
            Emg_vehicle[0] = vehicleID_2[0]
            print("Emg_vehicle[0] = ", Emg_vehicle[0])
            traci.vehicle.changeLane(Emg_vehicle[0], 0, 100)  # 強迫換車道

        # Returns the index of the current phase within the list of all phases of the current program.
        newPhase = {"J1": 99, "J2": 99, "J3": 99, "J4": 99}
        newPhase["J1"] = traci.trafficlight.getPhase("J1")
        newPhase["J2"] = traci.trafficlight.getPhase("J2")
        newPhase["J3"] = traci.trafficlight.getPhase("J3")
        newPhase["J4"] = traci.trafficlight.getPhase("J4")

        for i in intersectionOrder:

            remainTime[i] = traci.trafficlight.getNextSwitch(i) - traci.simulation.getTime()

            if (newPhase[i] == 0):
                remainTimeMSG[i] = phaseOrderName[0] + str(remainTime[i])
            elif (newPhase[i] == 1):
                remainTimeMSG[i] = phaseOrderName[1] + str(remainTime[i])
            elif (newPhase[i] == 2):
                remainTimeMSG[i] = phaseOrderName[2] + str(remainTime[i])
            elif (newPhase[i] == 3):
                remainTimeMSG[i] = phaseOrderName[3] + str(remainTime[i])
            elif (newPhase[i] == 4):
                remainTimeMSG[i] = phaseOrderName[4] + str(remainTime[i])
            elif (newPhase[i] == 5):
                remainTimeMSG[i] = phaseOrderName[5] + str(remainTime[i])
            elif (newPhase[i] == 6):
                remainTimeMSG[i] = phaseOrderName[6] + str(remainTime[i])

        print("RemainTime: ", remainTimeMSG)  # 顯示剩餘秒數

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
    sumo_start = [sumoBinary, "-c", "competition.sumocfg","--tripinfo-output","tripInfo.xml"]
    traci.start(sumo_start)
    run()
