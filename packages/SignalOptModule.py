import traci
import math
from thesis.RSUObject import RSU
import gurobipy as gp
from gurobipy import GRB
import datetime

phaseAndGreenStatePairs = {"J1": [0,1,2], "J2": [13,14], "J3": [15,16,17], "J4": [8,9], "J5": [10,11,12], "J6": [3,4], "J7": [5,6,7], "J8": [18,19]}
phaseList = [0, 1, 2, 3, 4, 5, 6, 7]

phaseStrDict = {0: "J1", 1: "J2", 2: "J3", 3: "J4",4: "J5", 5: "J6", 6: "J7", 7: "J8"}
phaseStrDict_rev = {"J1": 0, "J2":1, "J3":2, "J4":3, "J5":4, "J6":5, "J7":6, "J8":7}

outputFileName = "signalResult001.csv"
outputFile_StepThr = 0
TOLERANCE_FACTOR = 0.5

class SignalOPT():

    def __init__(self, RSU):  # 傳入RSU物件
        self.RSU = RSU
        # 各時相停等車輛總數 (IQj)
        #IQj = {"J1": 0, "J2": 0, "J3": 0, "J4": 0, "J5": 0, "J6": 0, "J7": 0, "J8": 0}

        # 車道參數
        self.Nj = {0: 2, 1: 1, 2: 2, 3: 1,
                   4: 2, 5: 1, 6: 2, 7: 1}

        # 時相是否已結束標籤
        self.phaseIsEnd = {0: False, 1: False, 2: False, 3: False,
                      4: False, 5: False, 6: False, 7: False}

        # phaseEndBinaryVar 用於指出該時相是否已結束
        self.phaseEndBinaryVar = [0 for x in range(0, 8)]

        # currentPhase 指出當下正在(或即將轉換至)運作時相
        self.currentPhase = [0, 4]

        # phasePendingCounter 指出該時相是否正在轉換階段，轉換階段 = Yellow + AllRed
        self.R = 5
        self.phasePendingCounter = {0: self.R, 1: self.R, 2: self.R, 3: self.R,
                               4: self.R, 5: self.R, 6: self.R, 7: self.R}

        self.accumulatedIIS = 0

        # Tijk 計算結果
        self.TijkResult = {0: 0, 1: 0, 2: 0, 3: 0,
                      4: 0, 5: 0, 6: 0, 7: 0}

        # Gijk 計算結果
        self.GijkResult = {0: 0, 1: 0, 2: 0, 3: 0,
                      4: 0, 5: 0, 6: 0, 7: 0}

        # 各時相累計時間長度
        self.GijkLengthCal = {0: 0, 1: 0, 2: 0, 3: 0,
                         4: 0, 5: 0, 6: 0, 7: 0}

    def monitorGijkLength(self):
        def checkAllPhasesEnd(self):
            check = 0
            totalPhaseLength = 0
            for num in self.phaseIsEnd:  # 確認是否全部時相皆已結束
                if (self.phaseIsEnd[num]):
                    check = check + 1
            if check == 8:  # 全部時相都結束了，將相關list設定回原始預設值
                for num in range(0, 4):  # cycle結果累計 1. 綠燈長度
                    #greenTotal = self.GijkResult[num]
                    self.RSU.CycleAccumulated = self.RSU.CycleAccumulated + self.GijkResult[num]
                    #寫入用
                    totalPhaseLength += self.GijkResult[num]
                self.RSU.CycleAccumulated += self.R * 4  # cycle結果累計 2. 黃燈 + 全紅
                print("CycleAccumulated = ", self.RSU.CycleAccumulated)
                file = open("signalResult003.csv", "a")
                file.write(str(traci.simulation.getTime())+","+str(totalPhaseLength + 20)+"\n")


                # 寫入txt檔案
                # file = open("signalResult_"+ str(datetime.datetime.now().time().hour) + "_"
                #             + str(datetime.datetime.now().time().minute) + "_" + str(datetime.datetime.now().time().second) + ".txt", "a")
                # if (traci.simulation.getTime() >= outputFile_StepThr):
                #     file = open(outputFileName, "a")
                #     file.write("\n [CYCLE END] \n")
                #     file.write("\n[ Step = "+ str(traci.simulation.getTime()) + "]\n")
                #     file.write("----GijkLengthCal(tau)----\n")
                #     file.write("[0]: %s [1]: %s [2]: %s [3]: %s \n[4]: %s [5]: %s [6]: %s [7]: %s \n"
                #           % (str(self.GijkLengthCal[0]), str(self.GijkLengthCal[1]), str(self.GijkLengthCal[2]), str(self.GijkLengthCal[3]),
                #              str(self.GijkLengthCal[4]), str(self.GijkLengthCal[5]), str(self.GijkLengthCal[6]), str(self.GijkLengthCal[7])))
                #
                #
                #     # 關閉檔案
                #     file.close()

                for num in range(0, 8):  # 回復各欄位原始設定值
                    self.phaseIsEnd[num] = False
                    self.GijkLengthCal[num] = 0
                    self.GijkResult[num] = 0
                    self.phaseEndBinaryVar[num] = 0

                return True
            else:
                return False

        def checkGijkExist(self, j):
            currentState = traci.trafficlight.getRedYellowGreenState(self.RSU.RSU_ID)
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
        checkAllPhasesEnd(self)

        for num in range(0, len(self.currentPhase)):
            j = self.currentPhase[num]
            if self.phasePendingCounter[j] == self.R:  # clearence time
                result = checkGijkExist(self,j)  # 檢查時相j是否還在currentState ?
                if (result):  # 是，該時相累積綠燈長度+1
                    self.GijkLengthCal[j] = self.GijkLengthCal[j] + 1
                else:  # 否，該時相已經結束

                    self.phaseIsEnd[j] = True  # 標記該時相結束
                    self.GijkResult[j] = self.GijkLengthCal[j]  # 將時相總累計綠燈長度交給 GijkResult

                    if (self.currentPhase[num] == 7):  # 已經到ring2的底，再次計算由時相4開始
                        self.currentPhase[num] = 4
                    elif (self.currentPhase[num] == 3):  # 已經到ring1的底，再次計算由時相0開始
                        self.currentPhase[num] = 0
                    else:
                        self.TijkResult[j + 1] = self.TijkResult[j] + self.GijkResult[j] + self.R  # 下個時相的起始時間 = 本時相起始時間 + 綠燈時間 + 清道時間
                        self.currentPhase[num] = self.currentPhase[num] + 1  # 沒有到底，直接+1
                    self.phasePendingCounter[self.currentPhase[num]] = self.phasePendingCounter[self.currentPhase[num]] - 1  # 下個時相計數-1

            else:
                self.phasePendingCounter[j] = self.phasePendingCounter[j] - 1
                if (self.phasePendingCounter[j] == 0):
                    self.phasePendingCounter[j] = self.R  # 計時結束

        print("----GijkLengthCal---- ")
        print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
              % (self.GijkLengthCal[0], self.GijkLengthCal[1], self.GijkLengthCal[2], self.GijkLengthCal[3], self.GijkLengthCal[4],
                 self.GijkLengthCal[5], self.GijkLengthCal[6], self.GijkLengthCal[7]))
        print("----phasePendingCounter---- ")
        print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
              % (self.phasePendingCounter[0], self.phasePendingCounter[1], self.phasePendingCounter[2], self.phasePendingCounter[3],
                 self.phasePendingCounter[4], self.phasePendingCounter[5],
                 self.phasePendingCounter[6], self.phasePendingCounter[7]))
        print("currentPhase = ", self.currentPhase)

    def checkNowStateYorAR(self):
        currentState = traci.trafficlight.getRedYellowGreenState(self.RSU.RSU_ID) #取得RSU ID (父類別)
        currentexephase = []  # 找到當下執行的時相(可能不只一個)
        for j in phaseAndGreenStatePairs:
            # phaseAndGreenStatePairs = {"J1": [0,1,2], "J2": [13,14], "J3": [15,16,17] ... }
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


    def EXE_GUROBI(self):

        # 號誌參數
        toleranceFactor = TOLERANCE_FACTOR
        BackgroundGreen = {0: self.RSU.plan[1].phases['J1'].green, 1: self.RSU.plan[1].phases['J2'].green,
                           2: self.RSU.plan[1].phases['J3'].green, 3: self.RSU.plan[1].phases['J4'].green,
                           4: self.RSU.plan[1].phases['J5'].green, 5: self.RSU.plan[1].phases['J6'].green,
                           6: self.RSU.plan[1].phases['J7'].green, 7: self.RSU.plan[1].phases['J8'].green}

        print("BackgroundGreen = ", BackgroundGreen)

        yellow = 3
        allRed = 2
        R: int = yellow + allRed  # Yellow + allred

        # Gmin = {0: round(BackgroundGreen[0] * (1 - toleranceFactor)),
        #         1: round(BackgroundGreen[1] * (1 - toleranceFactor)),
        #         2: round(BackgroundGreen[2] * (1 - toleranceFactor)),
        #         3: round(BackgroundGreen[3] * (1 - toleranceFactor)),
        #         4: round(BackgroundGreen[4] * (1 - toleranceFactor)),
        #         5: round(BackgroundGreen[5] * (1 - toleranceFactor)),
        #         6: round(BackgroundGreen[6] * (1 - toleranceFactor)),
        #         7: round(BackgroundGreen[7] * (1 - toleranceFactor))}

        Gmin = {0: max(round(BackgroundGreen[0] * (1 - toleranceFactor)), self.RSU.plan[1].phases['J1'].Gmin),
                1: max(round(BackgroundGreen[1] * (1 - toleranceFactor)), self.RSU.plan[1].phases['J2'].Gmin),
                2: max(round(BackgroundGreen[2] * (1 - toleranceFactor)), self.RSU.plan[1].phases['J3'].Gmin),
                3: max(round(BackgroundGreen[3] * (1 - toleranceFactor)), self.RSU.plan[1].phases['J4'].Gmin),
                4: max(round(BackgroundGreen[4] * (1 - toleranceFactor)), self.RSU.plan[1].phases['J5'].Gmin),
                5: max(round(BackgroundGreen[5] * (1 - toleranceFactor)), self.RSU.plan[1].phases['J6'].Gmin),
                6: max(round(BackgroundGreen[6] * (1 - toleranceFactor)), self.RSU.plan[1].phases['J7'].Gmin),
                7: max(round(BackgroundGreen[7] * (1 - toleranceFactor)), self.RSU.plan[1].phases['J8'].Gmin)}

        # Gmin = {0: self.RSU.plan[1].phases['J1'].Gmin, 1: self.RSU.plan[1].phases['J2'].Gmin,
        #         2: self.RSU.plan[1].phases['J3'].Gmin, 3: self.RSU.plan[1].phases['J4'].Gmin,
        #         4: self.RSU.plan[1].phases['J5'].Gmin, 5: self.RSU.plan[1].phases['J6'].Gmin,
        #         6: self.RSU.plan[1].phases['J7'].Gmin, 7: self.RSU.plan[1].phases['J8'].Gmin}

        BackgroundCycle = self.RSU.plan[1].cycle
        C_opt = BackgroundCycle
        Cmin = 50
        Cmax = round(C_opt * (1 + toleranceFactor)) + 1
        print("Cmax =", Cmax)

        ################## GUROBI ##################
        vehQueueList = []
        vehNoneQueueList = []
        vehAllList = []

        self.monitorGijkLength()  # 1. 更新綠燈執行狀態
        if self.checkNowStateYorAR():  # 2. 檢查所有時相是否在黃燈or全紅時間
            return False  # 在黃燈或全紅時間，無法號誌執行最佳化，直接結束

        # Big M
        M = 999999
        # constant
        s = 0.5
        Ls = 4
        vlim = 13 # m/s

        IQj = {0: len(self.RSU.vehQueue['J1']), 1: len(self.RSU.vehQueue['J2']), 2: len(self.RSU.vehQueue['J3']), 3: len(self.RSU.vehQueue['J4']),
               4: len(self.RSU.vehQueue['J5']), 5: len(self.RSU.vehQueue['J6']), 6: len(self.RSU.vehQueue['J7']), 7: len(self.RSU.vehQueue['J8'])}

        ###### GUROBI ######

        try:
            # Create a new model
            m = gp.Model(" mip1 ")

            Ojx = [[None for x in range(1 + len(self.RSU.vehQueue[phaseStrDict[j]]) + len(self.RSU.vehNoneQueue[phaseStrDict[j]]))] for j in phaseStrDict]
            ##print("Ojx = ",Ojx)
            TPjx = [[None for x in range(1 + len(self.RSU.vehQueue[phaseStrDict[j]]) + len(self.RSU.vehNoneQueue[phaseStrDict[j]]))] for j in phaseStrDict]
            ##print("TPjx = ",TPjx)

            for j in phaseStrDict:  # phaseStrDict = {0: "J1", 1: "J2", 2: "J3" ... }
                phaseStr = phaseStrDict[j]
                # 分別取出每個時相內的車輛資訊
                for vehItem in self.RSU.vehQueue[phaseStr]:
                    x = vehItem['order']
                    vehQueueList.append((j, x))
                    vehAllList.append((j, x))
                    Ojx[j][x] = vehItem['occupancy']
                    # print("Ojx[", j, ",", x, "] = ", Ojx[j][x])  # Test

                for vehItem in self.RSU.vehNoneQueue[phaseStr]:
                    x = vehItem['order']
                    vehNoneQueueList.append((j, x))
                    vehAllList.append((j, x))
                    TPjx[j][x] = vehItem['ProjectArrTime(TPxj)']
                    # print("TPjx[", j, ",", x, "] = ", TPjx[j][x])
                    Ojx[j][x] = vehItem['occupancy']
                    if (vehItem['occupancy'] == 30):  # Debug
                        print("bus")
                        print("TPjx =", TPjx[j][x])
                    # print("Ojx[", j, ",", x, "] = ", Ojx[j][x])

            # vehQueue
            DQjx = m.addVars(vehQueueList, vtype=GRB.CONTINUOUS, name="DQjx")

            # vehNoneQueue
            Djx = m.addVars(vehNoneQueueList, vtype=GRB.CONTINUOUS, name="Djx")
            DEjx = m.addVars(vehNoneQueueList, vtype=GRB.CONTINUOUS, name="DEjx")
            Qjx = m.addVars(vehNoneQueueList, vtype=GRB.INTEGER, name="Qjx")
            TAjx = m.addVars(vehNoneQueueList, vtype=GRB.INTEGER, name="TAjx")

            # vehAll
            Trjx = m.addVars(vehAllList, vtype=GRB.CONTINUOUS, name="Trjx")

            # Traffic Signal
            Tijk = m.addVars(phaseList, vtype=GRB.INTEGER, name="Tijk")
            tijk = m.addVars(phaseList, vtype=GRB.INTEGER, name="tijk")
            Gijk = m.addVars(phaseList, vtype=GRB.INTEGER, name="Gijk")
            Tijk_plus_1 = m.addVars(phaseList, vtype=GRB.INTEGER, name="Tijk_plus_1")
            C = m.addVar(vtype=GRB.INTEGER, name="CYCLE")

            # Binary Variables
            Ykjx = m.addVars(vehNoneQueueList, vtype=GRB.BINARY, name="Ykjx")
            Thetakjx = m.addVars(vehNoneQueueList, vtype=GRB.BINARY, name="Thetakjx")
            Sigmakjx = m.addVars(vehNoneQueueList, vtype=GRB.BINARY, name="Sigmakjx")

            Rhoijk = m.addVars(phaseList, vtype=GRB.BINARY, name="Rhoijk")
            # Deltaijk = m.addVars(phaseList, vtype=GRB.BINARY, name="Deltaijk")
            # Phiijk = m.addVars(phaseList, vtype=GRB.BINARY, name="Phiijk")

            m.update()

            # 設定目標式
            objectiveFunction = gp.quicksum(Ojx[j][x] * Djx[j, x] for j in phaseStrDict for x in
                                            range(IQj[j] + 1, IQj[j] + 1 + len(self.RSU.vehNoneQueue[phaseStrDict[j]]))) \
                                + gp.quicksum( Ojx[j][x] * DQjx[j, x] for j in phaseStrDict for x in range(1, IQj[j] + 1))
            # print("Set Obj Function: ", objectiveFunction)
            m.setObjective(objectiveFunction, sense=GRB.MINIMIZE)

            # k週期的號誌參數
            # 檢查是否已經有時相結束，有則將phaseEndBinaryVar[j]設為1
            for j in self.phaseIsEnd:
                if (self.phaseIsEnd[j]):
                    print("時相 %d 已經結束" % j)
                    self.phaseEndBinaryVar[j] = 1
                    print("phaseEndBinaryVar[%d] = %d" % (j, self.phaseEndBinaryVar[j]))
                else:
                    print("時相 %d 還沒結束" % j)
                    print("phaseEndBinaryVar[%d] = %d" % (j, self.phaseEndBinaryVar[j]))

            for j in phaseStrDict:

                floor_IQj_Nj = math.floor(IQj[j] / self.Nj[j])  # 純計算
                # m.addConstr(Gijk[j] <= Gmax[j])  # 最大綠限制
                # m.addConstr(Gijk[j] >= Gmin[j])  # 最小綠限制

                m.addConstr(tijk[j] == Gijk[j] * (1 - self.phaseEndBinaryVar[j]) + self.GijkLengthCal[j] * self.phaseEndBinaryVar[j],'eq2')

                m.addConstr(Gijk[j] >= 0, 'cGijk[min]')  # 最小綠限制

                m.addConstr(self.GijkLengthCal[j] - Gmin[j] <= Rhoijk[j] * M - 0.001, 'cGijk[0]')
                m.addConstr(self.GijkLengthCal[j] - Gmin[j] >= (-M) * (1 - Rhoijk[j]), 'cGijk[1]')

                # Rhoijk = 1 表示 時相已經超過其最短綠燈時間 -> Gijk[j] >= 0
                # Rhoijk = 0 表示 時相尚未超過其最短綠燈時間 -> Gijk[j] >= Gmin[j] - self.GijkLengthCal[j]
                m.addConstr(Gijk[j] >= Gmin[j] - self.GijkLengthCal[j] - (Rhoijk[j] * M), 'cGijk[2]')
                m.addConstr(Gijk[j] >= (-M) * (1 - Rhoijk[j]), 'cGijk[3]')

                m.addConstr(Gijk[j] >= floor_IQj_Nj / s - M * self.phaseEndBinaryVar[j], 'cGijk[undersaturated]')  # 最小綠限制 (至少能清除原停等車輛，確保undersaturated)

                # Constraints for queueing vehicles
                for x in range(1, IQj[j] + 1):
                    floor_X_Nj = math.floor((x - 1) / self.Nj[j])  # 純計算
                    nowRelativeSimTime = traci.simulation.getTime() - self.RSU.CycleAccumulated # 取得相對模擬時間
                    # Queued Vehicle Delay
                    m.addConstr(DQjx[j, x] >= Tijk_plus_1[j] + (floor_X_Nj / s) - nowRelativeSimTime)  # - Trjx[j, x]

                # Constraints for non-queueing vehicles
                for x in range(IQj[j] + 1, IQj[j] + 1 + len(self.RSU.vehNoneQueue[phaseStrDict[j]])):
                    # Ykjx = 0 ->  TPjx[j][x] > Tijk[j] + tijk[j]  車輛預計抵達停止線時間已經是紅燈
                    # Ykjx = 1 ->  TPjx[j][x] <= Tijk[j] + tijk[j] 車輛預計抵達停止線時間仍是綠燈

                    ## 一組
                    m.addConstr(TPjx[j][x] >= Tijk[j] + self.GijkLengthCal[j] * (1 - self.phaseEndBinaryVar[j]) + tijk[j] - Ykjx[j, x] * M + 0.00001, 'NQC_1')
                    m.addConstr(TPjx[j][x] <= Tijk[j] + self.GijkLengthCal[j] * (1 - self.phaseEndBinaryVar[j]) + tijk[j] + (1 - Ykjx[j, x]) * M, 'NQC_2')
                    # m.addConstr(TPjx[j][x] >= Tijk[j]  + tijk[j] - Ykjx[j, x] * M + 0.00001, 'NQC_1')
                    # m.addConstr(TPjx[j][x] <= Tijk[j] + tijk[j] + (1 - Ykjx[j, x]) * M, 'NQC_2')
                    ## 一組

                    m.addConstr(Thetakjx[j, x] <= Ykjx[j, x], 'NQC_3')

                    m.addConstr(Trjx[j, x] <= Tijk[j] + (1 - Sigmakjx[j, x]) * M, 'NQC_4')
                    m.addConstr(Trjx[j, x] >= Tijk[j] - Sigmakjx[j, x] * M + 0.00001, 'NQC_5')

                    floor_X_Nj = math.floor((x - 1) / self.Nj[j])  # 純計算

                    m.addConstr(Qjx[j, x] >= floor_X_Nj - (1 - Sigmakjx[j, x]) * M, 'NQC_6')
                    m.addConstr(Qjx[j, x] >= floor_X_Nj - s * (Trjx[j, x] - Tijk[j]) - Sigmakjx[j, x] * M, 'NQC_7')
                    m.addConstr(Qjx[j, x] >= 0, 'NQC_8')

                    AAA = Qjx[j, x] * Ls / vlim
                    BBB = (Qjx[j, x] + IQj[j]) * Ls / vlim

                    ## 一組
                    m.addConstr(Qjx[j, x] / s + AAA <= self.GijkLengthCal[j] * (1 - self.phaseEndBinaryVar[j]) + tijk[j] + (1 - Sigmakjx[j, x]) * M + (1 - Thetakjx[j, x]) * M,'NQC_9')
                    m.addConstr(Qjx[j, x] / s + AAA >= self.GijkLengthCal[j] * (1 - self.phaseEndBinaryVar[j]) + tijk[j] - (1 - Sigmakjx[j, x]) * M - Thetakjx[j, x] * M + 0.00001,'NQC_10')
                    m.addConstr(Qjx[j, x] / s + Trjx[j, x] + BBB <= Tijk[j] + self.GijkLengthCal[j] * (1 - self.phaseEndBinaryVar[j]) + tijk[j] + Sigmakjx[j, x] * M + (1 - Thetakjx[j, x]) * M, 'NQC_11')
                    m.addConstr(Qjx[j, x] / s + Trjx[j, x] + BBB >= Tijk[j] + self.GijkLengthCal[j] * (1 - self.phaseEndBinaryVar[j]) + tijk[j] - Sigmakjx[j, x] * M - Thetakjx[j, x] * M + 0.00001, 'NQC_12')

                    # m.addConstr(Qjx[j, x] / s + AAA <= tijk[j] + (1 - Sigmakjx[j, x]) * M + (1 - Thetakjx[j, x]) * M,'NQC_9')
                    # m.addConstr(Qjx[j, x] / s + AAA >= tijk[j] - (1 - Sigmakjx[j, x]) * M - Thetakjx[j, x] * M + 0.00001,'NQC_10')
                    # m.addConstr(Qjx[j, x] / s + Trjx[j, x] + BBB <= Tijk[j] + tijk[j] + Sigmakjx[j, x] * M + (1 - Thetakjx[j, x]) * M, 'NQC_11')
                    # m.addConstr(Qjx[j, x] / s + Trjx[j, x] + BBB >= Tijk[j] + tijk[j] - Sigmakjx[j, x] * M - Thetakjx[j, x] * M + 0.00001, 'NQC_12')
                    ##一組

                    # Non-Queued Vehicle Delay
                    m.addConstr(Djx[j, x] >= Qjx[j, x] / s + Tijk[j] - Trjx[j, x] - (1 - Sigmakjx[j, x]) * M - (1 - Thetakjx[j, x]) * M, 'NQC_13')
                    m.addConstr(Djx[j, x] >= Qjx[j, x] / s + Tijk[j] - Trjx[j, x] + DEjx[j, x] - (1 - Sigmakjx[j, x]) * M - Thetakjx[j, x] * M, 'NQC_14')
                    m.addConstr(Djx[j, x] >= Qjx[j, x] / s - Sigmakjx[j, x] * M - (1 - Thetakjx[j, x]) * M, 'NQC_15')
                    m.addConstr(Djx[j, x] >= Qjx[j, x] / s + DEjx[j, x] - Sigmakjx[j, x] * M - Thetakjx[j, x] * M, 'NQC_16')

                    # Equality Constraint
                    m.addConstr(Trjx[j, x] == TPjx[j][x] - (Qjx[j, x] * Ls / vlim), 'EQ_1')
                    m.addConstr(DEjx[j, x] == Tijk_plus_1[j] - TAjx[j, x], 'EQ_2')
                    # m.addConstr(TAjx[j, x] == (Tijk[j] + self.GijkLengthCal[j] * (1 - self.phaseEndBinaryVar[j]) + tijk[j]))

                    m.addConstr(TAjx[j, x] <= Trjx[j, x] + (Qjx[j, x] / s) + Tijk[j] - Trjx[j, x] + (Qjx[j, x] * Ls / vlim)
                                + M * Thetakjx[j, x] + M * (1 - Sigmakjx[j, x]), 'TAjx_D2')
                    m.addConstr(TAjx[j, x] <= (Qjx[j, x] / s) + Tijk[j] + (Qjx[j, x] * Ls / vlim) + M * Thetakjx[j, x] + M * (1 - Sigmakjx[j, x]), 'TAjx_D2')
                    m.addConstr(TAjx[j, x] <= Trjx[j, x] + (Qjx[j, x] / s) + ((Qjx[j, x] + IQj[j]) * Ls / vlim) + M * Thetakjx[j, x] + M * Sigmakjx[j, x], 'TAjx_D4')

                    # m.addConstr(TAjx[j, x] <= Trjx[j, x] + (Qjx[j, x] / s + Tijk[j] - Trjx[j, x]) + (Qjx[j, x] * Ls / vlim)
                    #             + M * Thetakjx[j, x] + M * (1 - Sigmakjx[j, x]) + M * Ykjx[j, x], 'TAjx2_1')
                    # m.addConstr(TAjx[j, x] <= Trjx[j, x] + Qjx[j, x] / s + (Qjx[j, x] + IQj[j]) * Ls / vlim
                    #             + M * Thetakjx[j, x] + M * Sigmakjx[j, x] + M * Ykjx[j, x], 'TAjx2_2')
                    # m.addConstr(TAjx[j, x] <= Trjx[j, x] + Qjx[j, x] / s + Tijk[j] - Trjx[j, x] + (Qjx[j, x] * Ls / vlim)
                    #             + M * Thetakjx[j, x] + M * (1 - Sigmakjx[j, x]) + M * (1 - Ykjx[j, x]), 'TAjx2_4')
                    # m.addConstr(TAjx[j, x] <= Trjx[j, x] + Qjx[j, x] / s + (Qjx[j, x] + IQj[j]) * Ls / vlim
                    #             + M * Thetakjx[j, x] + M * Sigmakjx[j, x] + M * (1 - Ykjx[j, x]), 'TAjx2_6')


            m.addConstr(Tijk[0] == 0, 'ct1')
            m.addConstr(Tijk[4] == 0, 'ct2')

            m.addConstr(Tijk[0] == Tijk[4], 'ct3')
            m.addConstr(Tijk[2] == Tijk[6], 'ct4')
            # m.addConstr(Tijk[1] == Tijk[5], 'ct4_1')  # 限制不可早開遲閉
            # m.addConstr(Tijk[3] == Tijk[7], 'ct4_2')  # 限制不可早開遲閉

            m.addConstr(Tijk[1] == Tijk[0] + tijk[0] + R + (self.GijkLengthCal[0] * (1 - self.phaseEndBinaryVar[0])), 'ct5')  # Rhoijk[0]
            m.addConstr(Tijk[2] == Tijk[1] + tijk[1] + R + (self.GijkLengthCal[1] * (1 - self.phaseEndBinaryVar[1])), 'ct6')  # Rhoijk[1]
            m.addConstr(Tijk[3] == Tijk[2] + tijk[2] + R + (self.GijkLengthCal[2] * (1 - self.phaseEndBinaryVar[2])), 'ct7')  # Rhoijk[2]
            m.addConstr(Tijk[5] == Tijk[4] + tijk[4] + R + (self.GijkLengthCal[4] * (1 - self.phaseEndBinaryVar[4])), 'ct8')  # Rhoijk[4]
            m.addConstr(Tijk[6] == Tijk[5] + tijk[5] + R + (self.GijkLengthCal[5] * (1 - self.phaseEndBinaryVar[5])), 'ct9')  # Rhoijk[5]
            m.addConstr(Tijk[7] == Tijk[6] + tijk[6] + R + (self.GijkLengthCal[6] * (1 - self.phaseEndBinaryVar[6])), 'ct10')  # Rhoijk[6]
            m.addConstr(C >= Cmin, 'cCmin')
            m.addConstr(C <= Cmax - 0.00001, 'cCmax')
            m.addConstr(Tijk[3] + tijk[3] + R + (self.GijkLengthCal[3] * (1 - self.phaseEndBinaryVar[3])) - Tijk[0] == C, 'cC1')  # Rhoijk[3]
            m.addConstr(Tijk[7] + tijk[7] + R + (self.GijkLengthCal[7] * (1 - self.phaseEndBinaryVar[3])) - Tijk[4] == C, 'cC2')  # Rhoijk[7]

            # k+1週期的時制內容
            m.addConstr(Tijk_plus_1[0] == Tijk[3] + tijk[3] + (self.GijkLengthCal[3] * (1 - self.phaseEndBinaryVar[3])) + R, 'Tijk_plus_1[0]')  #(self.GijkLengthCal[3] * (1 - self.phaseEndBinaryVar[3]))
            m.addConstr(Tijk_plus_1[1] == Tijk_plus_1[0] + BackgroundGreen[0] + R, 'Tijk_plus_1[1]')
            m.addConstr(Tijk_plus_1[2] == Tijk_plus_1[1] + BackgroundGreen[1] + R, 'Tijk_plus_1[2]')
            m.addConstr(Tijk_plus_1[3] == Tijk_plus_1[2] + BackgroundGreen[2] + R, 'Tijk_plus_1[3]')
            m.addConstr(Tijk_plus_1[4] == Tijk[7] + tijk[7] + (self.GijkLengthCal[7] * (1 - self.phaseEndBinaryVar[7])) + R, 'Tijk_plus_1[4]') # (self.GijkLengthCal[7] * (1 - self.phaseEndBinaryVar[7]))
            m.addConstr(Tijk_plus_1[5] == Tijk_plus_1[4] + BackgroundGreen[4] + R, 'Tijk_plus_1[5]')
            m.addConstr(Tijk_plus_1[6] == Tijk_plus_1[5] + BackgroundGreen[5] + R, 'Tijk_plus_1[6]')
            m.addConstr(Tijk_plus_1[7] == Tijk_plus_1[6] + BackgroundGreen[6] + R, 'Tijk_plus_1[7]')

            # 執行最佳化
            m.Params.OutputFlag = 0  # 是否詳細印出最佳化過程 0:不印出 1:印出
            m.optimize() #最佳化

            # 取出參數值
            optSignalPlanForCycleK = [0 for i in range(0, 8)]  # 先初始化
            optSignalPlanForCycleK_plus_1 = []
            phaseStartTimeForCycleK = []
            phaseStartTimeForCycleK_plus_1 = []

            ### 設定週期k+1的內容 【開始】 ###

            for g in BackgroundGreen: #　self.plan[1] = BackgroundGreen
                optSignalPlanForCycleK_plus_1.append(BackgroundGreen[g])
            ### 設定週期k+1的內容 【結束】 ###

            print_tijk = {}
            printTijk = {}
            if (m.status == GRB.Status.OPTIMAL):
                optCycleK = m.getVarByName("CYCLE").x
                for v in m.getVars():
                    if (v.varName[0:4] in ("tijk")):
                        print_tijk.update({v.varName: int(v.x)})  # print用       #print('% s % g' % (v.varName, v.x))

                        # optSignalPlanForCycleK.append(round(v.x))  #四捨五入取整數
                    elif (v.varName[0:5] in ("Tijk[")):
                        printTijk.update({v.varName: int(v.x)})  # print用
                        phaseStartTimeForCycleK.append(round(v.x))  # 四捨五入取整數
                    elif (v.varName[0:11] in ("Tijk_plus_1")):
                        phaseStartTimeForCycleK_plus_1.append(round(v.x))

                tijkResult = []
                ### 設定週期k的內容 【開始】 暫時 ###
                for j in range(0, 8):
                    # tijk[j]為gurobi變數物件，tijk[j].x 表示取出數值
                    tijkResult.append(round(tijk[j].x))
                    if (int(tijk[j].x) == 0):
                        optSignalPlanForCycleK[j] = 0
                    else:
                        if j in (0, 1, 2, 4, 5, 6):
                            # 由時相起始時間去回推出每個時相的綠燈長度
                            # print("phaseStartTimeForCycleK[%d] = %d" % (j+1, phaseStartTimeForCycleK[j+1]))
                            # print("phaseStartTimeForCycleK[%d] = %d" % (j, phaseStartTimeForCycleK[j]))
                            # print("R = %d" % R)
                            optSignalPlanForCycleK[j] = phaseStartTimeForCycleK[j + 1] - phaseStartTimeForCycleK[j] - R
                            # print("optSignalPlanForCycleK[%d] = %d" % (j, optSignalPlanForCycleK[j]))

                        elif j == 3:
                            # Tijk[3] + tijk[3] + (self.GijkLengthCal[3] * (1 - Rhoijk[3])) + R - Tijk[0] == C
                            optSignalPlanForCycleK[j] = round(
                                optCycleK - phaseStartTimeForCycleK[3] + phaseStartTimeForCycleK[0] - R)
                        elif j == 7:
                            # Tijk[7] + tijk[7] + (self.GijkLengthCal[7] * (1 - Rhoijk[7])) + R - Tijk[4] == C
                            optSignalPlanForCycleK[j] = round(
                                optCycleK - phaseStartTimeForCycleK[7] + phaseStartTimeForCycleK[4] - R)

                ### 設定週期k的內容 【結束】 暫時 ###
                print("----- RSU ID = %s ----- " %(self.RSU.RSU_ID))
                print("----GijkLengthCal(tau)---- ")
                print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
                      % (self.GijkLengthCal[0], self.GijkLengthCal[1], self.GijkLengthCal[2], self.GijkLengthCal[3], self.GijkLengthCal[4],
                         self.GijkLengthCal[5], self.GijkLengthCal[6], self.GijkLengthCal[7]))

                print("----Gmin---- ")
                print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
                      % (Gmin[0], Gmin[1], Gmin[2], Gmin[3], Gmin[4],
                         Gmin[5], Gmin[6], Gmin[7]))

                print("----Rhoijk 0:時相未超過最小綠 1:時相已超過最小綠---- ")
                print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
                      % (Rhoijk[0].x, Rhoijk[1].x, Rhoijk[2].x, Rhoijk[3].x, Rhoijk[4].x, Rhoijk[5].x, Rhoijk[6].x,
                         Rhoijk[7].x))

                print("----OPT_Tijk---- ")
                print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
                      % (printTijk['Tijk[0]'], printTijk['Tijk[1]'], printTijk['Tijk[2]'], printTijk['Tijk[3]'],
                         printTijk['Tijk[4]'], printTijk['Tijk[5]'], printTijk['Tijk[6]'], printTijk['Tijk[7]']))

                print("----OPT_tijk---- ")
                print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
                      % (print_tijk['tijk[0]'], print_tijk['tijk[1]'], print_tijk['tijk[2]'], print_tijk['tijk[3]'],
                         print_tijk['tijk[4]'], print_tijk['tijk[5]'], print_tijk['tijk[6]'], print_tijk['tijk[7]']))

                print("----optSignalPlanForCycleK---- ")
                print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
                      % (optSignalPlanForCycleK[0], optSignalPlanForCycleK[1], optSignalPlanForCycleK[2],
                         optSignalPlanForCycleK[3], optSignalPlanForCycleK[4],
                         optSignalPlanForCycleK[5], optSignalPlanForCycleK[6], optSignalPlanForCycleK[7]))

                print("----optSignalPlanForCycleK_plus_1---- ")
                print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
                      % (optSignalPlanForCycleK_plus_1[0], optSignalPlanForCycleK_plus_1[1],
                         optSignalPlanForCycleK_plus_1[2], optSignalPlanForCycleK_plus_1[3],
                         optSignalPlanForCycleK_plus_1[4],
                         optSignalPlanForCycleK_plus_1[5], optSignalPlanForCycleK_plus_1[6],
                         optSignalPlanForCycleK_plus_1[7]))

                print("----phaseStartTimeForCycleK_plus_1---- ")
                print("[0]: %d [1]: %d [2]: %d [3]: %d \n[4]: %d [5]: %d [6]: %d [7]: %d"
                      % (phaseStartTimeForCycleK_plus_1[0], phaseStartTimeForCycleK_plus_1[1],
                         phaseStartTimeForCycleK_plus_1[2], phaseStartTimeForCycleK_plus_1[3],
                         phaseStartTimeForCycleK_plus_1[4],
                         phaseStartTimeForCycleK_plus_1[5], phaseStartTimeForCycleK_plus_1[6],
                         phaseStartTimeForCycleK_plus_1[7]))

                print('Obj: % g' % m.objVal)

                if (traci.simulation.getTime() >= outputFile_StepThr):
                    file = open(outputFileName, "a")
                    file.write(str(traci.simulation.getTime())+",")
                    file.write("%g,%g\n"% (m.objVal,m.getVarByName("CYCLE").x))
                    #file.write("\n[ Step = " + str(traci.simulation.getTime()) + "]\n")
                    # file.write("Obj: % g\n" % m.objVal)
                    # file.write("Cycle: % g \n" % m.getVarByName("CYCLE").x)
                    # file.write("----GijkLengthCal(tau)----\n")
                    # file.write("[0]: %s [1]: %s [2]: %s [3]: %s \n[4]: %s [5]: %s [6]: %s [7]: %s\n"
                    #            % (str(self.GijkLengthCal[0]), str(self.GijkLengthCal[1]), str(self.GijkLengthCal[2]),str(self.GijkLengthCal[3]),
                    #               str(self.GijkLengthCal[4]), str(self.GijkLengthCal[5]), str(self.GijkLengthCal[6]),str(self.GijkLengthCal[7])))
                    # file.write("----OPT_Tijk----\n")
                    # file.write("[0]: %s [1]: %s [2]: %s [3]: %s \n[4]: %s [5]: %s [6]: %s [7]: %s\n"
                    #           % (str(printTijk['Tijk[0]']), str(printTijk['Tijk[1]']), str(printTijk['Tijk[2]']), str(printTijk['Tijk[3]']),
                    #              str(printTijk['Tijk[4]']), str(printTijk['Tijk[5]']), str(printTijk['Tijk[6]']), str(printTijk['Tijk[7]'])))
                    # file.write("----OPT_tijk----\n")
                    # file.write("[0]: %s [1]: %s [2]: %s [3]: %s \n[4]: %s [5]: %s [6]: %s [7]: %s\n"
                    #           % (str(print_tijk['tijk[0]']), str(print_tijk['tijk[1]']), str(print_tijk['tijk[2]']),str(print_tijk['tijk[3]']),
                    #              str(print_tijk['tijk[4]']), str(print_tijk['tijk[5]']), str(print_tijk['tijk[6]']),str(print_tijk['tijk[7]'])))
                    # file.write("----optSignalPlanForCycleK----\n")
                    # file.write("[0]: %s [1]: %s [2]: %s [3]: %s \n[4]: %s [5]: %s [6]: %s [7]: %s\n"
                    #           % (str(optSignalPlanForCycleK[0]), str(optSignalPlanForCycleK[1]), str(optSignalPlanForCycleK[2]), str(optSignalPlanForCycleK[3]),
                    #              str(optSignalPlanForCycleK[4]), str(optSignalPlanForCycleK[5]), str(optSignalPlanForCycleK[6]),str(optSignalPlanForCycleK[7])))

                    file.close()

            else:
                m.computeIIS()
                m.write(self.RSU.RSU_ID + "_INFEASIBLE_ERROR.ilp")
                self.accumulatedIIS += 1
                print("******** accumulatedIIS = ", self.accumulatedIIS)
                print(1/0) #程式強制中止

                return False

            print("Optimality ? ", m.status == GRB.Status.OPTIMAL)

        except gp.GurobiError as e:
            print('Error code ' + str(e.errno) + ':' + str(e))

        return optSignalPlanForCycleK, phaseStartTimeForCycleK, \
               optSignalPlanForCycleK_plus_1, phaseStartTimeForCycleK_plus_1, tijkResult

