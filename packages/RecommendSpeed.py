import traci
import math
import thesis.PhaseObject as PhaseObject
from scipy.stats import norm

intersectionList = ['I1']
intersectionAbsolutePos = {'I1':200}

class simTime_less_accCycle_error(Exception):
    def __init__(self,msg):
        self.message=msg

class RecommendSpeed:
    vehID = ''
    vehType = ''
    position = 0
    currentSpeed = 0
    direction = '' #E or W or None
    nextTLS = ''
    targetPhase = ''
    intersectionPassProb = {'I1': 1}  # 紀錄路口i的通過機率，初始值為100%
    recommendSpeed = 0
    maxSpeedLimit = 15 #約 54 km/hr
    CycleAccumulated = 0 #累積週期長度，權宜之計在此設置，之後架構要改

    def __init__(self,vehID,vehType,pos,currentSpeed,direction,nextTLS,targetPhase):
        self.vehID = vehID
        self.vehType = vehType
        self.position = pos
        self.currentSpeed = currentSpeed
        self.direction = direction
        self.nextTLS = nextTLS
        self.targetPhase = targetPhase

    def calPassProb(self,signalPlan):  # 傳入路口完整計畫內容 (有點怪, 之後架構應該再修改)
        # 每次計算前需先重設路口通過機率，否則會重複計算，使通過機率不斷減少
        def resetPassProb():
            for i in ['I1']:
                self.intersectionPassProb[i] = 1
        resetPassProb()

        #  1. 確認公車是否仍有下一個路口
        if (self.nextTLS != None):
            # 若有，紀錄為計算路口群組之起始路口(startIntersectionIndex)
            startIntersectionIndex = intersectionList.index(self.nextTLS) #取出該路口編號之index標籤
        else:  # 若無，則代表公車即將離開路網，不需要計算駕駛建議
            self.intersectionPassProb['I1'] = False # 紀錄為False後再return
            return False

        def passProb_of_i(self, i_Str, dist):

            try:
                travelTime = round(dist / self.currentSpeed)  # 至路口旅行時間
            except ZeroDivisionError as zeroDivision:
                print("公車已經停止(除0速度錯誤)，不需要計算駕駛建議")
                # 公車已經停止，不需要計算駕駛建議
                self.intersectionPassProb[i_Str] = False
                return False  # 紀錄為False後再return

            # (模擬絕對時間 - 累計週期長度) = 本周期起始時間
            try:
                if (self.CycleAccumulated > traci.simulation.getTime()):
                    raise simTime_less_accCycle_error('注意! 例外錯誤: simTime < CycleAccumulated')
                else:
                    # 抵達路口絕對時間 = 至路口旅行時間 + (模擬絕對時間 - 累計週期長度)
                    arrivalTime = travelTime + traci.simulation.getTime() - self.CycleAccumulated
            except simTime_less_accCycle_error as err:
                print(err.message)
                arrivalTime = travelTime + traci.simulation.getTime() - self.CycleAccumulated

            print("arrival time = ", arrivalTime)
            deviation = math.ceil((2 + dist / 50) / 3)  # 標準差
            upBound = round(arrivalTime + 3 * deviation)  # 抵達時間上界
            lowBound = round(arrivalTime - 3 * deviation)  # 抵達時間下界
            arrivalBound = [b for b in range(lowBound, upBound + 1)]  # 列出預計抵達時間離散化範圍

            # 計算未來時制計畫紅燈與綠燈時間點(phaseSplitTime)
            # PhaseObject.calSpecificPhaseTimeSplit 回傳 [0].時間分割點 [1].是否為起頭時相
            phaseTimeSplitResult = PhaseObject.calSpecificPhaseTimeSplit(i_Str, signalPlan[i_Str], self.targetPhase)
            phaseSplitTime = [round(time) for time in phaseTimeSplitResult[0]]  # 轉換為整數
            currentPhaseGreen = phaseTimeSplitResult[1]
            print("currentPhaseGreen = ", currentPhaseGreen)
            print("phaseSplitTime = ", phaseSplitTime)

            ### 指出紅燈區段是哪些時間點 ###
            redBound = []

            # phaseSplit兩兩一組，各自產生離散化範圍
            for n in range(0, len(phaseSplitTime), 2):
                redBound.extend([time for time in range(phaseSplitTime[n], phaseSplitTime[n + 1] + 1)])  # 列出紅燈的時間範圍
            # print("離散化的紅燈秒數區間 = ", redBound)

            ### 計算路口i的通過機率 ###
            # 計算紅燈區段和抵達時間區段之交集
            intersectResult = list(set(arrivalBound).intersection(set(redBound)))
            intersectResult.sort()  # 因為SET取交集可能使其沒有排序好
            redTimeRange = []  # 紀錄取交集後之紅燈時間長度
            redProbSet = []  # 紀錄紅燈機率

            # 交集後可能包含區間橫跨兩個時相，因此需要個別指出
            for num in range(1, len(intersectResult)):  # 比較在取交集之集合中，後一個數字是否是前一個+1
                if (intersectResult[num] == intersectResult[num - 1] + 1):
                    # 若是，則表示還在原本的切割範圍，繼續加至紅燈時間長度
                    redTimeRange.append(intersectResult[num - 1])
                else:
                    # 若否，表示num已經是新的切割區域
                    redTimeRange.append(intersectResult[num - 1])  # 先將num-1加至舊的切割區域
                    # 計算舊的切割區域之(紅燈)機率
                    redProb = norm.cdf(x=max(redTimeRange), loc=arrivalTime, scale=deviation) \
                              - norm.cdf(x=min(redTimeRange), loc=arrivalTime, scale=deviation)
                    redProbSet.append(redProb)  # 將計算結果apped到redProbSet
                    redTimeRange.clear()  # 清除紅燈計算範圍

                if (num == len(intersectResult) - 1 and len(redTimeRange) > 0):
                    # 最後一部分: 若已經到intersectionResult底 且 redTimeRange還有沒被清空的部分
                    redTimeRange.append(intersectResult[num])
                    redProb = norm.cdf(x=max(redTimeRange), loc=arrivalTime, scale=deviation) \
                              - norm.cdf(x=min(redTimeRange), loc=arrivalTime, scale=deviation)
                    redProbSet.append(redProb)

            # 通過機率 = 1 - (紅燈機率) #
            for prob in redProbSet:
                self.intersectionPassProb[i_Str] = self.intersectionPassProb[i_Str] - prob

        # 2. 識別公車方向
        if self.direction == 'East':
            print("公車方向: 向東，計算通過機率!")
            for i in range(startIntersectionIndex, len(intersectionList)): #從群組之起始路口開始往後算，列舉出每個路口

                i_Str = intersectionList[i]  # 取出路口str型態名稱 ex. I1 I2
                # 公車距離路口距離，取絕對值(公車可能從東西向兩邊來)
                dist = round(abs(intersectionAbsolutePos[i_Str] - self.position[0]))  # self.position[0] 取x座標並轉換為整數型態
                passProb_of_i(self, i_Str, dist)

        elif self.direction == 'West':
            print("公車方向: 向西，計算通過機率!")
            for i in range(startIntersectionIndex, -1, -1):
                i_Str = intersectionList[i]  # 取出路口str型態名稱 ex. I1 I2
                dist = round(abs(intersectionAbsolutePos[i_Str] - self.position[0]))  # self.position[0] 取x座標並轉換為整數型態
                passProb_of_i(self, i_Str, dist)

        elif self.direction == 'Nort': #因為veh type擷取只有前4位字元
            print("公車方向: 向北，計算通過機率!")
            i_Str = self.nextTLS
             # self.position[1] = -200 -> -188 -> -165 ...
            dist = round(abs(self.position[1]))  # self.position[1] 取y座標並轉換為整數型態
            passProb_of_i(self, i_Str, dist)
        elif self.direction == 'Sout':
            print("公車方向: 向南，計算通過機率!")
            i_Str = self.nextTLS
            # self.position[1] = 200 -> 188 -> 165 ...
            dist = round(abs(self.position[1]))
            passProb_of_i(self, i_Str, dist)

        else:
            print("例外錯誤! 公車方向不屬於任何一方")

    def __str__(self):
        return 'RecommendSpeed(ID = {0}, type = {1}, pos = {2}, speed = {3}, direction = {4}, nextTLS = {5}, targetPhase = {6})'.format(
             self.vehID, self.vehType, self.position, self.currentSpeed, self.direction, self.nextTLS, self.targetPhase)



