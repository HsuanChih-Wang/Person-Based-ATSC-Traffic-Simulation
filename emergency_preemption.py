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

        if (tls_origin_LOCK == False): #確認是否有鎖住
            for i in intersectionOrder:
                tls_origin[i] = traci.trafficlight.getCompleteRedYellowGreenDefinition(i)[0] #先記錄下原本的時制計畫
            tls_origin_LOCK = True

        vehicleID_2 = traci.inductionloop.getLastStepVehicleIDs("02")

        if len(vehicleID_2) > 0 and ("Emg_vehicle" in vehicleID_2[0]) :
            Emg_vehicle[0] = vehicleID_2[0]
            print("Emg_vehicle[0] = ",Emg_vehicle[0])
            traci.vehicle.changeLane(Emg_vehicle[0],0,100) #強迫換車道

        if Emg_vehicle[0] != "": #確認有緊急車輛存在於路網儲存目前緊急車輛位置
            Emg_vehicle[1] = traci.vehicle.getPosition(Emg_vehicle[0])[0] #X座標
            Emg_vehicle[2] = traci.vehicle.getPosition(Emg_vehicle[0])[1] #Y座標
            print(Emg_vehicle[1])

            try:
                nextTLS[0] = traci.vehicle.getNextTLS(Emg_vehicle[0])[0][0]
                nextTLS[1] = traci.vehicle.getNextTLS(Emg_vehicle[0])[0][1]
                nextTLS[2] = traci.vehicle.getNextTLS(Emg_vehicle[0])[0][2]
                nextTLS[3] = traci.vehicle.getNextTLS(Emg_vehicle[0])[0][3]
            except:
                print("例外!")

            nowPhase = traci.trafficlight.getPhase(nextTLS[0])  # 取得前方路口當下號誌狀態


            if (priorityStatus[nextTLS[0]][0] != True): #還沒執行過優先

                priorityStatus[nextTLS[0]][0] = True  # 已執行過優先
                print("nowPhase =",nowPhase)

                if (nowPhase == 0): #前方是綠燈
                    traci.trafficlight.setPhaseDuration(nextTLS[0],200) #綠燈延長200秒
                    priorityStatus[nextTLS[0]][1] = 0 #登記實施優先的PHASE為0

                elif (nowPhase == 3): #前方是紅燈
                    traci.trafficlight.setPhaseDuration(nextTLS[0], 5)  # 紅燈切斷(紅燈直接切至剩5秒)
                    tls = traci.trafficlight.getCompleteRedYellowGreenDefinition(nextTLS[0])[0]  # 儲存前方號誌完整內容
                    tls.phases[0].duration = 200  #  #綠燈延長200秒
                    traci.trafficlight.setCompleteRedYellowGreenDefinition(nextTLS[0], tls)  # 寫入新秒數

                    priorityStatus[nextTLS[0]][1] = 0 #登記實施優先的PHASE為0

                elif (nowPhase == 1 or nowPhase == 2 ):  # 前方是黃燈或全紅
                    tls = traci.trafficlight.getCompleteRedYellowGreenDefinition(nextTLS[0])[0]  # 儲存前方號誌完整內容
                    tls.phases[3].duration = 10 #紅燈切至最短
                    traci.trafficlight.setCompleteRedYellowGreenDefinition(nextTLS[0], tls)  # 寫入新秒數
                    priorityStatus[nextTLS[0]][1] = 3 #登記實施優先的PHASE為0
                else:
                    tls = traci.trafficlight.getCompleteRedYellowGreenDefinition(nextTLS[0])[0]  # 儲存前方號誌完整內容
                    tls.phases[0].duration = 200 #綠燈延長200秒
                    traci.trafficlight.setCompleteRedYellowGreenDefinition(nextTLS[0], tls)  # 寫入新秒數
                    priorityStatus[nextTLS[0]][1] = 0  # 登記實施優先的PHASE為0

            #print("priorityStatus = ",priorityStatus[nextTLS[0]][0])

        if (Emg_vehicle[1] > 90 and priorityStatus["J1"][0] == True):  # 已過第一個路口 交還控制權
            priorityStatus["J1"][0] = False  # 清除優先

            if (priorityStatus["J1"][1] == 0): #若是實施綠燈延長
                traci.trafficlight.setPhase("J1", 1)  #直接結束綠燈

            traci.trafficlight.setCompleteRedYellowGreenDefinition("J1", tls_origin["J1"]) #把原本的時制計畫寫回去

        if (Emg_vehicle[1] > 270 and priorityStatus["J2"][0] == True) :
            priorityStatus["J2"][0] = False  # 清除優先
            if (priorityStatus["J2"][1] == 0): #若是實施綠燈延長
                traci.trafficlight.setPhaseDuration("J2", 1) # 直接結束綠燈

            traci.trafficlight.setCompleteRedYellowGreenDefinition("J2", tls_origin["J2"]) #把原本的時制計畫寫回去

        if (Emg_vehicle[1] > 355 and priorityStatus["J3"][0] == True) :
            priorityStatus["J3"][0] = False  # 清除優先
            if (priorityStatus["J3"][1] == 0): #若是實施綠燈延長
                traci.trafficlight.setPhaseDuration("J3", 1) # 直接結束綠燈

            traci.trafficlight.setCompleteRedYellowGreenDefinition("J3", tls_origin["J3"]) #把原本的時制計畫寫回去


        if (Emg_vehicle[1] > 450 and priorityStatus["J4"][0] == True) : #已過第四個路口 視為離開路網
            priorityStatus["J4"][0] = False  # 清除優先
            if (priorityStatus["J4"][1] == 0): #若是實施綠燈延長
                traci.trafficlight.setPhaseDuration("J4", 1) # 直接結束綠燈

            traci.trafficlight.setCompleteRedYellowGreenDefinition("J4", tls_origin["J4"]) #把原本的時制計畫寫回去

            Emg_vehicle = ["", 0, 0]

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
