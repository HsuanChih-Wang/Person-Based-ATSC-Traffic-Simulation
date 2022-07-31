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

def arrive_intersections(busSpeed,intersectionOrder,positionDifference,intersectionPos,currentBusID,arrivalTime,arrivalPhase,arrivalPhaseRemainTime,arrivalPhasePassingTime,intersectionPhaseCycle,tls,encounterGreen,encounterRed):
    red = 0
    for i in intersectionOrder:
        encounterGreen[i] = 0
        encounterRed[i] = 0
        positionDifference[i] = intersectionPos[i] - traci.vehicle.getPosition(currentBusID)[0]
        arrivalTime[i] = math.ceil(traci.simulation.getTime() + positionDifference[i]/busSpeed) + red
        temp_time = arrivalTime[i] - traci.trafficlight.getNextSwitch(i)
        temp_phase = traci.trafficlight.getPhase(i)
        if(temp_phase == 0):
            encounterGreen[i] += 1
        elif(temp_phase == 3):
            encounterRed[i] += 1
        while(temp_time >= 0):
            temp_phase += 1
            if(temp_phase == 6):
                temp_phase -= 6
            if(temp_phase == 0):
                encounterGreen[i] += 1
            elif(temp_phase == 3):
                encounterRed[i] += 1
            temp_time = temp_time - intersectionPhaseCycle[i][temp_phase]
        arrivalPhase[i] = temp_phase
        arrivalPhaseRemainTime[i] = abs(temp_time)
        arrivalPhasePassingTime[i] = abs(tls[i].phases[temp_phase].duration) - arrivalPhaseRemainTime[i]
        if (arrivalPhase[i] == 3):
            red += arrivalPhaseRemainTime[i]

def pass_probability(passProbability,intersectionOrder,arrivalTimeDeviation,positionDifference,arrivalPhase,arrivalPhaseRemainTime,arrivalPhasePassingTime,tls):
    phase = {}
    for i in intersectionOrder:
        phase[i] = arrivalPhase[i]
    for i in intersectionOrder:
        if(positionDifference[i] < 0):
            continue
        arrivalTimeDeviation[i] = math.ceil((2 + positionDifference[i]/50)/3)
        if(arrivalPhase[i] == 0):
            right_inner = stats.norm.cdf(arrivalPhaseRemainTime[i]/arrivalTimeDeviation[i])
            left_inner = stats.norm.cdf(-arrivalPhasePassingTime[i]/arrivalTimeDeviation[i])
            passProbability[i] = right_inner - left_inner
        else:
            temp_phase = phase[i] + 1
            temp_time = 3*arrivalTimeDeviation[i] - arrivalPhaseRemainTime[i]
            while(temp_phase < 6):
                if(temp_time < 0):
                    break
                temp_time = temp_time - tls[i].phases[temp_phase].duration
                temp_phase += 1
            if(temp_phase == 6):
                right_outer = 1 - stats.norm.cdf((3*arrivalTimeDeviation[i] - temp_time)/arrivalTimeDeviation[i])
            else:
                right_outer = 0
            temp_phase = phase[i] - 1
            temp_time = 3*arrivalTimeDeviation[i] - arrivalPhasePassingTime[i]
            while(temp_phase > 0):
                if(temp_time < 0):
                    break
                temp_time = temp_time - tls[i].phases[temp_phase].duration
                temp_phase -= 1
            if(temp_phase == 0):
                left_outer = stats.norm.cdf(-(3*arrivalTimeDeviation[i] - temp_time)/arrivalTimeDeviation[i])
            else:
                left_outer = 0
            passProbability[i] = right_outer + left_outer

def transit_signal_priority(targetIntersection,targetProbability,arrivalTimeDeviation,arrivalPhase,arrivalPhaseRemainTime,arrivalPhasePassingTime,tls,intersectionGreenAdjustable,intersectionRedAdjustable,encounterGreen,encounterRed,greenCannotAdjust,redCannotAdjust):
    if (arrivalPhase[targetIntersection] == 0):
        if (arrivalPhasePassingTime[targetIntersection]>=arrivalPhaseRemainTime[targetIntersection]):
            if(math.ceil(stats.norm.ppf(targetProbability)*arrivalTimeDeviation[targetIntersection])-arrivalPhaseRemainTime[targetIntersection] < intersectionGreenAdjustable[targetIntersection]*encounterGreen[targetIntersection]):
                adjustment = math.ceil(stats.norm.ppf(targetProbability)*arrivalTimeDeviation[targetIntersection])-arrivalPhaseRemainTime[targetIntersection]
                green_adjustment(targetIntersection,intersectionGreenAdjustable,tls,encounterGreen,adjustment)
            else:
                if(greenCannotAdjust[targetIntersection] == 1):
                    redCannotAdjust[targetIntersection] = 1
                    return
                adjustment = intersectionGreenAdjustable[targetIntersection]*encounterGreen[targetIntersection]
                green_adjustment(targetIntersection,intersectionGreenAdjustable,tls,encounterGreen,adjustment)
                greenCannotAdjust[targetIntersection] = 1
        else:
            if(math.ceil(-(stats.norm.ppf(1-targetProbability)*arrivalTimeDeviation[targetIntersection]))-arrivalPhasePassingTime[targetIntersection] < intersectionRedAdjustable[targetIntersection]*encounterRed[targetIntersection]):
                adjustment = math.ceil(-(stats.norm.ppf(1-targetProbability)*arrivalTimeDeviation[targetIntersection]))-arrivalPhasePassingTime[targetIntersection]
                if(encounterRed[targetIntersection] == 0):
                    redCannotAdjust[targetIntersection] = 1
                    return
                red_adjustment(targetIntersection,intersectionRedAdjustable,encounterRed,tls,adjustment)
            else:
                if(redCannotAdjust[targetIntersection] == 1):
                    greenCannotAdjust[targetIntersection] = 1
                    return
                if(encounterRed[targetIntersection] == 0):
                    encounterRed[targetIntersection] = 1
                adjustment = intersectionRedAdjustable[targetIntersection]*encounterRed[targetIntersection]
                red_adjustment(targetIntersection,intersectionRedAdjustable,encounterRed,tls,adjustment)
                redCannotAdjust[targetIntersection] = 1
    elif (arrivalPhase[targetIntersection] == 1):
        if(math.ceil(stats.norm.ppf(targetProbability)*arrivalTimeDeviation[targetIntersection])+arrivalPhasePassingTime[targetIntersection] < intersectionGreenAdjustable[targetIntersection]*encounterGreen[targetIntersection]):
            adjustment = math.ceil(stats.norm.ppf(targetProbability)*arrivalTimeDeviation[targetIntersection])+arrivalPhasePassingTime[targetIntersection]
            if(encounterGreen[targetIntersection] == 0):
                greenCannotAdjust[targetIntersection] = 1
                return
            green_adjustment(targetIntersection,intersectionGreenAdjustable,tls,encounterGreen,adjustment)
        else:
            if(greenCannotAdjust[targetIntersection] == 1):
                redCannotAdjust[targetIntersection] = 1
                return
            adjustment = intersectionGreenAdjustable[targetIntersection]*encounterGreen[targetIntersection]
            if(encounterGreen[targetIntersection] == 0):
                greenCannotAdjust[targetIntersection] = 1
                return
            green_adjustment(targetIntersection,intersectionGreenAdjustable,tls,encounterGreen,adjustment)
            greenCannotAdjust[targetIntersection] = 1
    elif (arrivalPhase[targetIntersection] == 2):
        if(math.ceil(stats.norm.ppf(targetProbability)*arrivalTimeDeviation[targetIntersection])+3+arrivalPhasePassingTime[targetIntersection] < intersectionGreenAdjustable[targetIntersection]*encounterGreen[targetIntersection]):
            adjustment = math.ceil(stats.norm.ppf(targetProbability)*arrivalTimeDeviation[targetIntersection])+3+arrivalPhasePassingTime[targetIntersection]
            if(encounterGreen[targetIntersection] == 0):
                greenCannotAdjust[targetIntersection] = 1
                return
            green_adjustment(targetIntersection,intersectionGreenAdjustable,tls,encounterGreen,adjustment)
        else:
            if(greenCannotAdjust[targetIntersection] == 1):
                redCannotAdjust[targetIntersection] = 1
                return
            adjustment = intersectionGreenAdjustable[targetIntersection]*encounterGreen[targetIntersection]
            if(encounterGreen[targetIntersection] == 0):
                greenCannotAdjust[targetIntersection] = 1
                return
            green_adjustment(targetIntersection,intersectionGreenAdjustable,tls,encounterGreen,adjustment)
            greenCannotAdjust[targetIntersection] = 1
    elif (arrivalPhase[targetIntersection] == 5):
        if(math.ceil(-(stats.norm.ppf(1-targetProbability)*arrivalTimeDeviation[targetIntersection]))+arrivalPhaseRemainTime[targetIntersection] < intersectionRedAdjustable[targetIntersection]*encounterRed[targetIntersection]):
            adjustment = math.ceil(-(stats.norm.ppf(1-targetProbability)*arrivalTimeDeviation[targetIntersection]))+arrivalPhaseRemainTime[targetIntersection]
            if(encounterRed[targetIntersection] == 0):
                redCannotAdjust[targetIntersection] = 1
                return
            red_adjustment(targetIntersection,intersectionRedAdjustable,encounterRed,tls,adjustment)
        else:
            if(redCannotAdjust[targetIntersection] == 1):
                greenCannotAdjust[targetIntersection] = 1
                return
            if(encounterRed[targetIntersection] == 0):
                encounterRed[targetIntersection] = 1
            adjustment = intersectionRedAdjustable[targetIntersection]*encounterRed[targetIntersection]
            red_adjustment(targetIntersection,intersectionRedAdjustable,encounterRed,tls,adjustment)
            redCannotAdjust[targetIntersection] = 1
    elif (arrivalPhase[targetIntersection] == 4):
        if(math.ceil(-(stats.norm.ppf(1-targetProbability)*arrivalTimeDeviation[targetIntersection]))+1+arrivalPhaseRemainTime[targetIntersection] < intersectionRedAdjustable[targetIntersection]*encounterRed[targetIntersection]):
            adjustment = math.ceil(-(stats.norm.ppf(1-targetProbability)*arrivalTimeDeviation[targetIntersection]))+1+arrivalPhaseRemainTime[targetIntersection]
            if(encounterRed[targetIntersection] == 0):
                redCannotAdjust[targetIntersection] = 1
                return
            red_adjustment(targetIntersection,intersectionRedAdjustable,encounterRed,tls,adjustment)
        else:
            if(redCannotAdjust[targetIntersection] == 1):
                greenCannotAdjust[targetIntersection] = 1
                return
            if(encounterRed[targetIntersection] == 0):
                encounterRed[targetIntersection] += 1
            adjustment = intersectionRedAdjustable[targetIntersection]*encounterRed[targetIntersection]
            red_adjustment(targetIntersection,intersectionRedAdjustable,encounterRed,tls,adjustment)
            redCannotAdjust[targetIntersection] = 1
    else:
        #紅燈狀況
        if(math.ceil(stats.norm.ppf(0.5+targetProbability/2)*arrivalTimeDeviation[targetIntersection])+4+arrivalPhasePassingTime[targetIntersection] < intersectionGreenAdjustable[targetIntersection]*encounterGreen[targetIntersection]):
            adjustment = math.ceil(stats.norm.ppf(0.5+targetProbability/2)*arrivalTimeDeviation[targetIntersection])+4+arrivalPhasePassingTime[targetIntersection]
            if(encounterGreen[targetIntersection] == 0):
                greenCannotAdjust[targetIntersection] = 1
                return
            green_adjustment(targetIntersection,intersectionGreenAdjustable,tls,encounterGreen,adjustment)
        elif(math.ceil(-(stats.norm.ppf(1-targetProbability)*arrivalTimeDeviation[targetIntersection]))+4+arrivalPhaseRemainTime[targetIntersection] < intersectionRedAdjustable[targetIntersection]*encounterRed[targetIntersection]):
            adjustment = math.ceil(-(stats.norm.ppf(1-targetProbability)*arrivalTimeDeviation[targetIntersection]))+4+arrivalPhaseRemainTime[targetIntersection]
            red_adjustment(targetIntersection,intersectionRedAdjustable,encounterRed,tls,adjustment)
        else:
            if(redCannotAdjust[targetIntersection] == 1):
                greenCannotAdjust[targetIntersection] = 1
                return
            adjustment = intersectionRedAdjustable[targetIntersection]*encounterRed[targetIntersection]
            red_adjustment(targetIntersection,intersectionRedAdjustable,encounterRed,tls,adjustment)
            redCannotAdjust[targetIntersection] = 1

def green_adjustment(targetIntersection,intersectionGreenAdjustable,tls,encounterGreen,adjustment):
    tls[targetIntersection].phases[0].duration = tls[targetIntersection].phases[0].duration + math.ceil(adjustment/encounterGreen[targetIntersection])
    currentPhaseIndex = traci.trafficlight.getPhase(targetIntersection)
    tls[targetIntersection].currentPhaseIndex = currentPhaseIndex
    traci.trafficlight.setCompleteRedYellowGreenDefinition(targetIntersection,tls[targetIntersection])
    if (currentPhaseIndex == 0 ):
        traci.trafficlight.setPhaseDuration(targetIntersection,traci.trafficlight.getNextSwitch(targetIntersection) - traci.simulation.getTime() + math.ceil(adjustment/encounterGreen[targetIntersection]))
    intersectionGreenAdjustable[targetIntersection] -= math.ceil(adjustment/encounterGreen[targetIntersection])
    print("路口 ",targetIntersection," 綠燈延長 ",math.ceil(adjustment/encounterGreen[targetIntersection])," 秒")

def red_adjustment(targetIntersection,intersectionRedAdjustable,encounterRed,tls,adjustment):
    tls[targetIntersection].phases[3].duration = tls[targetIntersection].phases[3].duration - math.ceil(adjustment/encounterRed[targetIntersection])
    currentPhaseIndex = traci.trafficlight.getPhase(targetIntersection)
    tls[targetIntersection].currentPhaseIndex = currentPhaseIndex
    traci.trafficlight.setCompleteRedYellowGreenDefinition(targetIntersection,tls[targetIntersection])
    if (currentPhaseIndex == 3 ):
        traci.trafficlight.setPhaseDuration(targetIntersection,traci.trafficlight.getNextSwitch(targetIntersection) - traci.simulation.getTime() - math.ceil(adjustment/encounterRed[targetIntersection]))
    intersectionRedAdjustable[targetIntersection] -= math.ceil(adjustment/encounterRed[targetIntersection])
    print("路口 ",targetIntersection," 紅燈切斷 ",math.ceil(adjustment/encounterRed[targetIntersection])," 秒")

def print_state(intersectionOrder,positionDifference,arrivalTime,phaseOrderName,arrivalPhase,passProbability):
    print("　　　　路口：",end="")
    for i in range(4):
        print('{:<11s}'.format(intersectionOrder[i]),end="")
    print()
    print("預計抵達時間：",end="")
    for i in intersectionOrder:
        if(positionDifference[i] <= 0):
            print('已通過　　　',end="")
        else:
            print('{:<11.1f}'.format(abs(arrivalTime[i] - traci.simulation.getTime())),end="")
    print('秒後')
    print("　抵達時燈號：",end="")
    for i in intersectionOrder:
        if(positionDifference[i] <= 0):
            print('已通過　　　',end="")
        else:
            print(phaseOrderName[arrivalPhase[i]]+'　　',end="")
    print()
    print("通過路口機率：",end="")
    for i in intersectionOrder:
        if(positionDifference[i] <= 0):
            print('已通過　　　',end="")
        else:
            print("{:<11.2%}".format(passProbability[i]),end="")
    print()

def print_current_phase(intersectionOrder,remainTime,remainTimeMSG,phaseOrderName):
    # Returns the index of the current phase within the list of all phases of the current program.
    newPhase = {"C2":99,"C3":99,"C4":99,"C5":99}
    newPhase["C2"] = traci.trafficlight.getPhase("C2")
    newPhase["C3"] = traci.trafficlight.getPhase("C3")
    newPhase["C4"] = traci.trafficlight.getPhase("C4")
    newPhase["C5"] = traci.trafficlight.getPhase("C5")

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

    print("RemainTime: ", remainTimeMSG)

# contains TraCI control loop
def run():
    step=0
    remainTime = {"C2":99,"C3":99,"C4":99,"C5":99} #四個路口剩餘秒數
    remainTimeMSG = {"C2":99,"C3":99,"C4":99,"C5":99}
    phaseOrderName = ["幹道綠燈", "幹道黃燈", "幹道全紅", "支道綠燈", "支道黃燈", "支道全紅"]  #六個分相
    intersectionOrder = ["C2","C3","C4","C5"]
    positionDifference = {"C2":0,"C3":0,"C4":0,"C5":0}
    arrivalTime = {"C2":0,"C3":0,"C4":0,"C5":0}
    arrivalTimeDeviation = {"C2":0,"C3":0,"C4":0,"C5":0}
    arrivalPhase = {"C2":0,"C3":0,"C4":0,"C5":0}
    arrivalPhaseRemainTime = {"C2":0,"C3":0,"C4":0,"C5":0}
    arrivalPhasePassingTime = {"C2":0,"C3":0,"C4":0,"C5":0}
    passProbability = {"C2":0,"C3":0,"C4":0,"C5":0}
    greenCannotAdjust = {"C2":0,"C3":0,"C4":0,"C5":0}
    redCannotAdjust = {"C2":0,"C3":0,"C4":0,"C5":0}
    alreadyPass = {"C2":0,"C3":0,"C4":0,"C5":0}
    intersectionPos = {"C2":70,"C3":270,"C4":355,"C5":435}
    intersectionPhaseCycle = {"C2":[35,3,1,45,3,1],"C3":[35,3,1,45,3,1],"C4":[45,3,1,35,3,1],"C5":[35,3,1,45,3,1]}
    intersectionMaxGreen = {"C2":0,"C3":0,"C4":0,"C5":0}
    intersectionMinRed = {"C2":0,"C3":0,"C4":0,"C5":0}
    intersectionGreenAdjustable = {"C2":0,"C3":0,"C4":0,"C5":0}
    intersectionRedAdjustable = {"C2":0,"C3":0,"C4":0,"C5":0}
    temp = {"C2":0,"C3":0,"C4":0,"C5":0}
    original_tls = {}
    tls = {}

    currentBusID = "9999"
    originVehicleID_01 = "9999"
    originVehicleID_02 = "9999"
    encounterGreen = {}
    encounterRed = {}

    for i in intersectionOrder:
        original_tls[i] = traci.trafficlight.getCompleteRedYellowGreenDefinition(i)[0]
        tls[i] = traci.trafficlight.getCompleteRedYellowGreenDefinition(i)[0]

    for i in intersectionOrder:
        intersectionMaxGreen[i] = round(intersectionPhaseCycle[i][0]*1.2)
        intersectionMinRed[i] = round(intersectionPhaseCycle[i][3]*0.8)
        intersectionGreenAdjustable[i] = intersectionMaxGreen[i] - intersectionPhaseCycle[i][0]
        intersectionRedAdjustable[i] = intersectionPhaseCycle[i][3] - intersectionMinRed[i]

    while traci.simulation.getMinExpectedNumber() > 0:
        #迴圈直到所有車輛都已離開路網
        traci.simulationStep()
        if ( traci.inductionloop.getLastStepVehicleNumber("01") > 0):
            vehicleID_01 = traci.inductionloop.getLastStepVehicleIDs("01")
            if (vehicleID_01 != originVehicleID_01):
                originVehicleID_01 = vehicleID_01 ##避免重複計算
                a = traci.inductionloop.getVehicleData("01")
                if("ArterialBus" in a[0][4]):
                    currentBusID = a[0][0]
                    print("======================================================")
                    print("================公車優先觸動（偵測器01）================")
                    print("======================================================")
                    busSpeed = traci.vehicle.getSpeed(currentBusID)
                    usedtimes = 0
                    abletimes = 1
                    arrive_intersections(busSpeed,intersectionOrder,positionDifference,intersectionPos,currentBusID,arrivalTime,arrivalPhase,arrivalPhaseRemainTime,arrivalPhasePassingTime,intersectionPhaseCycle,tls,encounterGreen,encounterRed)
                    pass_probability(passProbability,intersectionOrder,arrivalTimeDeviation,positionDifference,arrivalPhase,arrivalPhaseRemainTime,arrivalPhasePassingTime,tls)
                    print_state(intersectionOrder,positionDifference,arrivalTime,phaseOrderName,arrivalPhase,passProbability)

        if ( traci.inductionloop.getLastStepVehicleNumber("02") > 0):
            vehicleID_02 = traci.inductionloop.getLastStepVehicleIDs("02")
            if (vehicleID_02 != originVehicleID_02):
                originVehicleID_02 = vehicleID_02 ##避免重複計算
                b = traci.inductionloop.getVehicleData("02")
                if("ArterialBus" in b[0][4]):
                    currentBusID = b[0][0]
                    print("======================================================")
                    print("================公車優先觸動（偵測器02）================")
                    print("======================================================")
                    busSpeed = traci.vehicle.getSpeed(currentBusID)
                    usedtimes = 0
                    abletimes = 1
                    arrive_intersections(busSpeed,intersectionOrder,positionDifference,intersectionPos,currentBusID,arrivalTime,arrivalPhase,arrivalPhaseRemainTime,arrivalPhasePassingTime,intersectionPhaseCycle,tls,encounterGreen,encounterRed)
                    pass_probability(passProbability,intersectionOrder,arrivalTimeDeviation,positionDifference,arrivalPhase,arrivalPhaseRemainTime,arrivalPhasePassingTime,tls)
                    print_state(intersectionOrder,positionDifference,arrivalTime,phaseOrderName,arrivalPhase,passProbability)

        for i in intersectionOrder:
            temp[i] = 0

        while (currentBusID != "9999") :
            busSpeed = traci.vehicle.getSpeed(currentBusID)
            if(busSpeed < 6.0):
                break
            arrive_intersections(busSpeed,intersectionOrder,positionDifference,intersectionPos,currentBusID,arrivalTime,arrivalPhase,arrivalPhaseRemainTime,arrivalPhasePassingTime,intersectionPhaseCycle,tls,encounterGreen,encounterRed)
            pass_probability(passProbability,intersectionOrder,arrivalTimeDeviation,positionDifference,arrivalPhase,arrivalPhaseRemainTime,arrivalPhasePassingTime,tls)
            if (traci.vehicle.getPosition(currentBusID)[0] > 435):
                currentBusID = "9999"
                for i in intersectionOrder:
                    currentPhaseIndex = traci.trafficlight.getPhase(i)
                    traci.trafficlight.setCompleteRedYellowGreenDefinition(i,original_tls[i])
                    tls[i]=traci.trafficlight.getCompleteRedYellowGreenDefinition(i)[0]
                    tls[i].currentPhaseIndex=currentPhaseIndex
                    traci.trafficlight.setCompleteRedYellowGreenDefinition(i,tls[i])
                    intersectionGreenAdjustable[i] = intersectionMaxGreen[i] - intersectionPhaseCycle[i][0]
                    intersectionRedAdjustable[i] = intersectionPhaseCycle[i][3] - intersectionMinRed[i]
                    greenCannotAdjust[i] = 0
                    redCannotAdjust[i] = 0
                    alreadyPass[i] = 0
                print("======================================================")
                print("=============== 公 車 優 先 結 束 實 施 ===============")
                print("======================================================")
                break
            elif (traci.vehicle.getPosition(currentBusID)[0] > 355):
                abletimes = 4
            elif (traci.vehicle.getPosition(currentBusID)[0] > 270):
                abletimes = 3
            elif (traci.vehicle.getPosition(currentBusID)[0] > 70):
                abletimes = 2
            for i in intersectionOrder:
                positionDifference[i] = intersectionPos[i] - traci.vehicle.getPosition(currentBusID)[0]
                if (alreadyPass[i] == 1):
                    continue
                if (positionDifference[i] > 0 ):
                    if(usedtimes < abletimes):
                        targetProbability = 1 - positionDifference[i]/2300
                        while(passProbability[i] < targetProbability):
                            if (greenCannotAdjust[i] == 1 and redCannotAdjust[i] == 1):
                                temp[i] = 1
                                break
                            transit_signal_priority(i,targetProbability,arrivalTimeDeviation,arrivalPhase,arrivalPhaseRemainTime,arrivalPhasePassingTime,tls,intersectionGreenAdjustable,intersectionRedAdjustable,encounterGreen,encounterRed,greenCannotAdjust,redCannotAdjust)
                            arrive_intersections(busSpeed,intersectionOrder,positionDifference,intersectionPos,currentBusID,arrivalTime,arrivalPhase,arrivalPhaseRemainTime,arrivalPhasePassingTime,intersectionPhaseCycle,tls,encounterGreen,encounterRed)
                            pass_probability(passProbability,intersectionOrder,arrivalTimeDeviation,positionDifference,arrivalPhase,arrivalPhaseRemainTime,arrivalPhasePassingTime,tls)
                            if(passProbability[i] >= targetProbability):
                                temp[i] = 1
                                print("======================================================")
                                print("=============== 路 口 通 過 機 率 不 足 ===============")
                                print("=============== 執 行 公 車 優 先 控 制 ===============")
                                print("=============== 執 行 後 之 結 果 如 下 ===============")
                                print("======================================================")
                                print_state(intersectionOrder,positionDifference,arrivalTime,phaseOrderName,arrivalPhase,passProbability)
                                break
                else:
                    alreadyPass[i] = 1
                    currentPhaseIndex = traci.trafficlight.getPhase(i)
                    traci.trafficlight.setCompleteRedYellowGreenDefinition(i,original_tls[i])
                    tls[i]=traci.trafficlight.getCompleteRedYellowGreenDefinition(i)[0]
                    tls[i].currentPhaseIndex=currentPhaseIndex
                    traci.trafficlight.setCompleteRedYellowGreenDefinition(i,tls[i])
                    greenCannotAdjust[i] = 0
                    redCannotAdjust[i] = 0
            break
        if(temp["C2"] == 1 and temp["C3"] == 1 and temp["C4"] == 1 and temp["C5"] == 1 ):
            usedtimes += 1
        print_current_phase(intersectionOrder,remainTime,remainTimeMSG,phaseOrderName)
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
