import xml.etree.ElementTree as ET

f1 = 'thesis_single_priority_tripInfo_1.xml'
f2 = 'thesis_single_priority_tripInfo_2.xml'
f3 = 'thesis_single_priority_tripInfo_3.xml'
f4 = 'thesis_single_priority_tripInfo_4.xml'
f5 = 'thesis_single_priority_tripInfo_5.xml'

f0_1 = 'thesis_single_noPriority_tripInfo_1.xml'
f0_2 = 'thesis_single_noPriority_tripInfo_2.xml'
f0_3 = 'thesis_single_noPriority_tripInfo_3.xml'
f0_4 = 'thesis_single_noPriority_tripInfo_4.xml'
f0_5 = 'thesis_single_noPriority_tripInfo_5.xml'

fileName0 = [f0_1, f0_2, f0_3, f0_4, f0_5]
fileName1 = [f1, f2, f3, f4, f5]

#for child in root:
    # print(child.tag, child.attrib)  # 印出tag和屬性

id_AutoFlow = "Phase"
id_BusFlow = "Bus"
id_SpecialVehicle = "Special"

#乘載人數
bus_Occupancy = 30
auto_Occupancy = 1.5

D_TP_result = []
D_TV_result = []
D_SV_result = []
D_AP_result = []
D_BP_result = []

for file in fileName1:
    tree = ET.ElementTree(file=file)
    root = tree.getroot()

    delay_AutoCar = 0  # 計算一般車延滯(waiting time)
    delay_Bus = 0  # 計算公車延滯
    delay_SpecialVehicle = 0  # 計算特殊車輛延滯

    numOfAuto = 0  # 計數一般車數量
    numOfBus = 0  # 計數公車數量
    numOfSpecialVehicle = 0  # 計數特殊車輛數量
    numOfTotalVehicle = 0  # 所有車數量

    for tripinfo in root.findall('tripinfo'):  # 找tag叫做tripinfo者
        id = tripinfo.get('id')  # 取得標籤 id 的值
        waitingTime = tripinfo.get('waitingTime')  # 取得標籤 waitingTime 的值
        #print("%s, %s" % (id, waitingTime))  # 印出兩者
        #print(tripinfo.get('depart'))
        if float(tripinfo.get('depart')) >= 300 and float(tripinfo.get('depart')) <= 7300:
            if id.find(id_AutoFlow) is not -1: #若該列id標籤為"Phase"
                WaitingTime_Auto = waitingTime
                #print("WaitingTime_Auto=", WaitingTime_Auto)
                delay_AutoCar = delay_AutoCar + float(WaitingTime_Auto) # 累加一般車延滯
                numOfAuto = numOfAuto + 1  # 一般車數量+1
                #print("numOfAuto = ", numOfAuto)

            if id.find(id_BusFlow) is not -1:
                WaitingTime_Bus = waitingTime
                #print("WaitingTime_Bus=", WaitingTime_Bus )
                delay_Bus = delay_Bus + float(WaitingTime_Bus) #累加公車延滯
                numOfBus = numOfBus + 1  #公車數量+1
                #print("numOfBus = ", numOfBus)

            if id.find(id_SpecialVehicle) is not -1:
                WaitingTime_SpecialVehicle = waitingTime
                #print("WaitingTime_Bus=", WaitingTime_Bus )
                delay_SpecialVehicle = delay_SpecialVehicle + float(WaitingTime_SpecialVehicle) #特殊車延滯
                numOfSpecialVehicle = numOfSpecialVehicle + 1  #特殊車數量+1
                #print("numOfBus = ", numOfBus)

    totalDelay = delay_AutoCar + delay_Bus + delay_SpecialVehicle
    numOfTotalVehicle = numOfAuto + numOfBus + numOfSpecialVehicle
    numOfTotalPassenger = (auto_Occupancy * numOfAuto) + (bus_Occupancy * numOfBus)

    D_TP = round((totalDelay / numOfTotalPassenger), 2)
    D_TV = round((totalDelay / numOfTotalVehicle), 2)
    D_SV = round((delay_SpecialVehicle / numOfSpecialVehicle), 2)
    D_AP = round((delay_AutoCar / (numOfAuto * auto_Occupancy)), 2)
    D_BP = round((delay_Bus / (numOfBus * bus_Occupancy)), 2)


    print("--- ", file, " --- ")
    print("------------------------------")
    print("delay_AutoCar = ", delay_AutoCar)
    print("delay_Bus = ", delay_Bus)
    print("delay_SpecialVehicle = ", delay_SpecialVehicle)
    print("totalDelay = ", totalDelay)
    print("numOfAuto = ", numOfAuto)
    print("numOfBus = ", numOfBus)
    print("numOfSpecailVehicle = ", numOfSpecialVehicle)
    print("numOfTotalVehicle = ", numOfTotalVehicle)
    print("numOfTotalPassenger = ", numOfTotalPassenger)

    print("Average delay of auto passengers (D-AP) =", D_AP)
    print("Average delay of bus passengers (D-BP) =", D_BP)
    print("Average delay of total passengers (D-TP) =", D_TP)
    print("Average delay of total vehicle (D-TV) =", D_TV)
    print("Average delay of special vehicle (D-SV) =", D_SV)


    D_TP_result.append(D_TP)
    D_TV_result.append(D_TV)
    D_SV_result.append(D_SV)
    D_AP_result.append(D_AP)
    D_BP_result.append(D_BP)

sD_TP_result = [str(a) for a in D_TP_result]
sD_TV_result = [str(a) for a in D_TV_result]
sD_SV_result = [str(a) for a in D_SV_result]
sD_AP_result = [str(a) for a in D_AP_result]
sD_BP_result = [str(a) for a in D_BP_result]

print(','.join(sD_AP_result))
print(','.join(sD_BP_result))
print(','.join(sD_TP_result))
print(','.join(sD_TV_result))
print(','.join(sD_SV_result))
