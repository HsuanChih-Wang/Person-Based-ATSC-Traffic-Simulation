import traci

ring1_state = ['GGGrrrrrrrrrrrrrrrrr','yyyrrrrrrrrrrrrrrrrr','rrrrrrrrrrrrrrrrrrrr', #0,1,2
                'rrrrrrrrrrrrrGGrrrrr','rrrrrrrrrrrrryyrrrrr','rrrrrrrrrrrrrrrrrrrr', #13,14
                'rrrrrrrrrrrrrrrGGGrr','rrrrrrrrrrrrrrryyyrr','rrrrrrrrrrrrrrrrrrrr', #15,16,17
                'rrrrrrrrGGrrrrrrrrrr','rrrrrrrryyrrrrrrrrrr','rrrrrrrrrrrrrrrrrrrr'] #8,9
ring2_state = ['rrrrrrrrrrGGGrrrrrrr','rrrrrrrrrryyyrrrrrrr','rrrrrrrrrrrrrrrrrrrr', #10,11,12
                'rrrGGrrrrrrrrrrrrrrr','rrryyrrrrrrrrrrrrrrr','rrrrrrrrrrrrrrrrrrrr', #3,4
                'rrrrrGGGrrrrrrrrrrrr','rrrrryyyrrrrrrrrrrrr','rrrrrrrrrrrrrrrrrrrr', #5,6,7
                'rrrrrrrrrrrrrrrrrrGG','rrrrrrrrrrrrrrrrrryy','rrrrrrrrrrrrrrrrrrrr'] #18,19

phaseAndGreenStatePairs = {"J1": [0,1,2], "J2": [13,14], "J3": [15,16,17], "J4": [8,9], "J5": [10,11,12], "J6": [3,4], "J7": [5,6,7], "J8": [18,19]}
phaseStrDict = {0: "J1", 1: "J2", 2: "J3", 3: "J4",4: "J5", 5: "J6", 6: "J7", 7: "J8"}
phaseStrDict_rev = {"J1": 0, "J2":1, "J3":2, "J4":3, "J5":4, "J6":5, "J7":6, "J8":7}

class Phase:
    phaseOrder = 0
    name = ""
    startTime = 0
    green = 0
    yellow = 0
    allRed = 0

    def setAllParameters(self,order,startTime,green,yellow,allRed):
        self.startTime = startTime
        self.green = green
        self.yellow = yellow
        self.allRed = allRed

    def setPhaseOrder(self,order):
        phaseOrderName = ["北往南直右", "南往北左轉", "西往東直右", "東往西左轉",
                          "南往北直右", "北往南左轉", "東往西直右", "西往東左轉", ]  # 8個分相
        self.phaseOrder = order
        self.name = phaseOrderName[order]

    def setStartTime(self,startTime):
        self.startTime = startTime
    # def setPhaseName(self,name):
    #     self.name = name
    def setPhaseGreen(self,green):
        self.green = green
    def setClearenceTime(self,yellow,allRed):
        self.yellow = yellow
        self.allRed = allRed

    def __str__(self):
        return 'PhaseObject(Order = {0}, name = {1}, startTime = {2}, green = {3}, yellow = {4}, allRed = {5})'\
            .format(self.phaseOrder, self.name, self.startTime, self.green, self.yellow, self.allRed)

def splitDualRingtoTLS(SignalPlan):

    def splitRingTime(RING):
        ringIndex = 0
        combined_state_index = 0
        if RING == 'ring1':
            for item in ringSplitTime:
                if (item < ring1[ringIndex]):
                    combined_state[RING].append(ring1_state[ringIndex])
                elif (item == ring1[ringIndex]):
                    combined_state[RING].append(ring1_state[ringIndex])
                    ringIndex = ringIndex + 1
                else:
                    ringIndex = ringIndex + 1
                    combined_state[RING].append(ring1_state[ringIndex])
        else:
            for item in ringSplitTime:
                if (item < ring2[ringIndex]):
                    combined_state[RING].append(ring2_state[ringIndex])
                elif (item == ring2[ringIndex]):
                    combined_state[RING].append(ring2_state[ringIndex])
                    ringIndex = ringIndex + 1
                else:
                    ringIndex = ringIndex + 1
                    # print("ring2_state = ", ring2_state)
                    # print("len  = ",len(ring2_state))
                    # print("ringIndex = ", ringIndex)
                    try:
                        combined_state[RING].append(ring2_state[ringIndex])
                    except IndexError as e:
                        print("抓!PhaseObject 有IndexError例外錯誤! 記得內審完後來修我!")
                        print(e)
                        return True

        # for i in range(len(combined_state['ring1'])):
        #     print("i=",i," ",combined_state['ring1'][i])
        # print("length = ",len(combined_state['ring1']))

    ring1 = []
    ring2 = []
    for phase in SignalPlan:
        if (phase in ['J1','J2','J3','J4']):
            try:
                phaseList = [SignalPlan[phase].green,
                             SignalPlan[phase].yellow, SignalPlan[phase].allRed]
                ring1.extend(phaseList)
            except AttributeError as error:
                print("ring1. Attribute Error")

        else: #phase in J5 J6 J7 J8
            try:
                phaseList = [SignalPlan[phase].green,
                             SignalPlan[phase].yellow, SignalPlan[phase].allRed]
                ring2.extend(phaseList)
            except AttributeError as error:
                print("ring2. Attribute Error")

    combined_state = {"ring1":[],"ring2":[]}
    finalSignalPlan = {"state":[], "duration":[]}

    for index in range(1,len(ring1)):
        ring1[index] = ring1[index-1] + ring1[index]
        ring2[index] = ring2[index-1] + ring2[index]
    #print("ring1 = ",ring1)
    #print("ring2 = ",ring2)
    ringSplitTime = ring1+ring2
    ringSplitTime.sort()
    #print("ringSplitTime (before) = ",ringSplitTime)
    ringSplitTime = list(dict.fromkeys(ringSplitTime)) #去掉重複的
    #print("ringSplitTime (after) = ",ringSplitTime)

    splitRingTime('ring1')
    splitRingTime('ring2')

    #print("combinedState[ring1] = ",format(combined_state["ring1"]))
    #print("combinedState[ring2] = ", format(combined_state["ring2"]))

    #將ring1和ring2 結果合併
    for strIndex in range(len(ringSplitTime)):
        tempStr = ""

        if combined_state['ring1'][strIndex] != combined_state['ring2'][strIndex]:
            for charIndex in range(20): #len(phaseIndex) = 20
                if (combined_state['ring1'][strIndex][charIndex] !='r'):
                    tempStr = tempStr + combined_state['ring1'][strIndex][charIndex]
                elif (combined_state['ring2'][strIndex][charIndex] !='r'):
                    tempStr = tempStr + combined_state['ring2'][strIndex][charIndex]
                else:
                    tempStr = tempStr + 'r'
        else:
            tempStr = combined_state['ring1'][strIndex]

        finalSignalPlan['state'].append(tempStr) #將最終結果存入

    for index in range(len(ringSplitTime)):
        if (index > 0):
            duration = ringSplitTime[index] - ringSplitTime[index-1]
        else:
            duration = ringSplitTime[index]
        finalSignalPlan['duration'].append(duration)

    # print("finalSignalPlan = ",finalSignalPlan)
    return  finalSignalPlan

def NEWmakeLogicObject(currentPhase, tijkResult, phasePendingStatus):
    # expect: currentPhase = [0,4] / tijkResult = [1,4,14,7,0,5,17,4]
    # phasePendingStatus = {0: R, 1: R, 2: R, 3: R,
    #                       4: R, 5: R, 6: R, 7: R}

    # 1. 找出
    num_Of_G = []
    num_Of_y = []
    num_Of_r = []
    for phase in currentPhase:
        if (phasePendingStatus[phase] in [5]):
            phaseStr = phaseStrDict[phase]  # 轉成字串形式
            if (tijkResult[phase] > 0):
                for num in phaseAndGreenStatePairs[phaseStr]:
                    num_Of_G.append(num)
            else: # tijkResult[phase] = 0
                for num in phaseAndGreenStatePairs[phaseStr]:
                    num_Of_y.append(num)
        elif (phasePendingStatus[phase] in [3,4]):
            if phase == 0:
                previousPhase = 3
            elif phase == 4:
                previousPhase = 7
            else:
                previousPhase = phase - 1
            phaseStr = phaseStrDict[previousPhase]  # 這個phasePending -> 代表前一個phase還在清道時間，要設定前一個phase的state
            for num in phaseAndGreenStatePairs[phaseStr]:
                num_Of_y.append(num)
        elif (phasePendingStatus[phase] in [1,2]):
            if phase == 0: previousPhase = 3
            elif phase == 4: previousPhase = 7
            else: previousPhase = phase - 1
            phaseStr = phaseStrDict[previousPhase]  # 這個phasePending -> 代表前一個phase還在清道時間，要設定前一個phase的state
            for num in phaseAndGreenStatePairs[phaseStr]:
                num_Of_r.append(num)
        else:
            print("例外錯誤: phasePendingStstus 輸入不合預期")

    # 2.產生state
    state = ''
    for item in range(0, 20):
        if item in num_Of_G:
            state = state + 'G'
        elif item in num_Of_y:
            state = state + 'y'
        elif item in num_Of_r:
            state = state + 'r'
        else:
            state = state + 'r'
    print("state = ", state)

    phaseResult = []
    phaseResult.append(traci.trafficlight.Phase(duration=1, state=state, minDur=1, maxDur=1, next=()))

    # 一組program就是一個logic物件
    LogicObject = traci.trafficlight.Logic(programID='1', type=0, currentPhaseIndex=0,
                                           phases=phaseResult)
    print("LogicObject = ", LogicObject)
    return LogicObject

def __makeLogicObject(plan):
    #接受一個完整計畫內容:
    # IntersectionSignal[路口編號][週期編號] = {"J1":J1(Phase物件, 以此類推), "J2":J2, "J3":J3, "J4":J4, "J5":J5, "J6":J6, "J7":J7, "J8":J8}
    TLS_result = splitDualRingtoTLS(plan)
    print("TLS_result = ", TLS_result)

    phaseResult = []
    for index in range(len(TLS_result['state'])):
        STATE = TLS_result['state'][index]
        DURATION = TLS_result['duration'][index]
        phaseResult.append(
            traci.trafficlight.Phase(duration=DURATION, state=STATE, minDur=DURATION, maxDur=DURATION, next=()))

    # 一組program就是一個logic物件
    LogicObject = traci.trafficlight.Logic(programID='1', type=0, currentPhaseIndex=0, phases=phaseResult) #phases不一定要tuple
    print("LogicObject = ", LogicObject)

    return LogicObject

def calSpecificPhaseTimeSplit(targetIntersection,plan,targetPhase): #未來應構建父類別PlanObject, 由PhaseObject類別繼承

    # 引數說明：
    # 1. targetIntersection: 要計算的路口編號(str)
    # 2. plan: 傳入該路口完整計畫內容(plan)(包含k和k+1週期)
    # 3. targetPhase: 指定要計算的phase編號(str)
    # 路口完整計畫內容(plan)支援格式: [{j:Phase() for j in ['J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8']},
    #                           {j:Phase() for j in ['J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8']}]

    #目前TLS執行的phase編號 (logic物件內的!!!! 不是8時相的!!!)
    #nowPhaseIndex = traci.trafficlight.getPhase(targetIntersection)

    # LogicObject = traci.trafficlight.getAllProgramLogics(targetIntersection)
    # # 確認k週期該用哪種時制計畫
    # # Expect: len(LogicObject) = 1 or 2
    # if (len(LogicObject) == 2): #若已經計算出動態時制
    #     LogicObject = traci.trafficlight.getAllProgramLogics(targetIntersection)[1] #取得 program[1] -> 動態計畫內容
    #                                                                                 #取得 program[0] -> 原固定時制計畫內容
    # elif (len(LogicObject) == 1): #若沒有計算出動態時制，則用原固定時制內容
    #     LogicObject = traci.trafficlight.getAllProgramLogics(targetIntersection)[0]
    # else: # 例外錯誤
    #     print("例外錯誤:　len(LogicObject) = ", len(LogicObject))

    phaseTimeSplit = [] #紀錄時相切割時間點

    # 確認時相是否為起頭時相
    if targetPhase in ['J1','J5']: # 時相編號為1或5是週期起頭時相
        IsHeadPhase = True
        # 起頭時相 phaseSplit = [(0) 紅燈起始, (1) 紅燈結束, (2)紅燈起始,..., (n)紅燈結束]

        #### 計算週期K ####
        # Expect: plan[0][targetPhase].startTime = 0
        targetPhaseEndTime = plan[0][targetPhase].startTime + plan[0][targetPhase].green
        phaseTimeSplit.append(targetPhaseEndTime) #加入 時相結束時間 = (0) 紅燈起始

        #### 計算週期K+n ####
        # Expect: cycle = 57
        cycle = (plan[1]['J4'].startTime + plan[1]['J4'].green + plan[1]['J4'].yellow + plan[1]['J4'].allRed) -  (plan[1]['J1'].startTime)  # 計算k+1週期長度

        for num in range(1,4): #這裡修改可設定一次產生幾個週期(k+1 k+2 k+3...)後的時間
            if (num == 1):
                phaseTimeSplit.append(plan[1][targetPhase].startTime) # 時相在週期k+1的起始時間 = (1) 紅燈結束
                startPoint = plan[1][targetPhase].startTime
            phaseTimeSplit.append(startPoint + plan[1][targetPhase].green) # 時相在週期k+n的結束時間 = (2) 紅燈起始
            startPoint = startPoint + cycle # 再加一個週期 -> 時相在k+n的起始時間 = (n) 紅燈結束
            phaseTimeSplit.append(startPoint)

    elif targetPhase in ['J2', 'J3', 'J4', 'J6', 'J7', 'J8']: # 其他時相編號 (非起頭時相)
        IsHeadPhase = False
        phaseTimeSplit.append(0) # 在最開始處新增0 (表示由0秒處紅燈起始)
        # 非起頭時相 phaseSplit = [(0) 0, (1) 紅燈結束, (2) 紅燈起始, (3)紅燈結束, (4)紅燈起始, ... , (n)紅燈結束]
        #### 計算週期K ####0
        startPoint = plan[0][targetPhase].startTime # targetPhase的起始時間 ( = (1) 紅燈結束時間)
        phaseTimeSplit.append(startPoint)
        phaseTimeSplit.append(startPoint + plan[0][targetPhase].green)  # targetPhase結束時間 ( = (2) 紅燈起始時間)

        #### 計算週期K+n ####
        # 計算k+1週期長度 Expect: cycle = 57
        cycle = (plan[1]['J4'].startTime + plan[1]['J4'].green + plan[1]['J4'].yellow + plan[1]['J4'].allRed) - (plan[1]['J1'].startTime)

        for num in range(1, 4):  # 這裡修改可設定一次產生幾個週期(k+1 k+2 k+3...)後的時間
            if (num == 1):
                startPoint = plan[1][targetPhase].startTime  # k+1週期的targetPhase起始時間 = (3) 紅燈結束
                phaseTimeSplit.append(startPoint)
            phaseTimeSplit.append(startPoint + plan[1][targetPhase].green) # k+1週期的targetPhase結束時間 = (4) 紅燈起始
            startPoint = startPoint + cycle  # k+2週期targetPhase的起始時間 = (n) 紅燈結束
            phaseTimeSplit.append(startPoint)
    else:  # 例外錯誤
        print("例外錯誤:　targetPhase = ", targetPhase)

    return phaseTimeSplit, IsHeadPhase #回傳 [0] 時間分割點 [1] 是否為起頭時相


# def activateProgramLogic(intersectionOrder, LogicObject):
#     traci.trafficlight.setProgramLogic(intersectionOrder, LogicObject)
#     #traci.trafficlight.setProgram(intersectionOrder,programID)





