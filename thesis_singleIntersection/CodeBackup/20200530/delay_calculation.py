import xml.etree.ElementTree as ET
f1 = 'thesis_single_noPriority_tripInfo.xml'
f2 = 'thesis_single_priority_tripInfo.xml'
fileName = f2
tree = ET.ElementTree(file=fileName)
root = tree.getroot()

#for child in root:
    # print(child.tag, child.attrib)  # 印出tag和屬性

id_AutoFlow = "Phase"
id_BusFlow = "Bus"
delay_AutoCar = 0  # 計算一般車延滯(waiting time)
delay_Bus = 0  # 計算公車延滯
numOfAuto = 0  # 計數一般車數量
numOfBus = 0  # 計數公車數量
numOfTotalVehicle = 0  # 所有車數量
for tripinfo in root.findall('tripinfo'):  # 找tag叫做tripinfo者
    id = tripinfo.get('id')  # 取得標籤 id 的值
    waitingTime = tripinfo.get('waitingTime')  # 取得標籤 waitingTime 的值
    print("%s, %s" % (id, waitingTime))  # 印出兩者
    print(tripinfo.get('depart'))
    if float(tripinfo.get('depart')) >= 600:
        if id.find(id_AutoFlow) is not -1: #若該列id標籤為"Phase"
            WaitingTime_Auto = waitingTime
            #print("WaitingTime_Auto=", WaitingTime_Auto)
            delay_AutoCar = delay_AutoCar + float(WaitingTime_Auto) # 累加一般車延滯
            numOfAuto = numOfAuto + 1  # 一般車數量+1
            print("numOfAuto = ", numOfAuto)

        if id.find(id_BusFlow) is not -1:
            WaitingTime_Bus = waitingTime
            #print("WaitingTime_Bus=", WaitingTime_Bus )
            delay_Bus = delay_Bus + float(WaitingTime_Bus) #累加公車延滯
            numOfBus = numOfBus + 1  #公車數量+1
            print("numOfBus = ", numOfBus)

bus_Occupancy = 30
auto_Occupancy = 1.5

totalDelay = delay_AutoCar + delay_Bus
numOfTotalVehicle = numOfAuto + numOfBus
numOfTotalPassenger = auto_Occupancy * numOfAuto + bus_Occupancy * numOfBus

D_TP = round((totalDelay / numOfTotalPassenger), 2)
D_TV = round((totalDelay / numOfTotalVehicle), 2)
D_AP = round((delay_AutoCar / (numOfAuto * auto_Occupancy)), 2)
D_BP = round((delay_Bus / (numOfBus * bus_Occupancy)), 2)

print("------------------------------")
print("delay_AutoCar = ", delay_AutoCar)
print("delay_Bus = ", delay_Bus)
print("totalDelay = ", totalDelay)
print("numOfAuto = ", numOfAuto)
print("numOfBus = ", numOfBus)
print("numOfTotalVehicle = ", numOfTotalVehicle)

print("--- ",fileName," --- ")
print("Average delay of total passengers (D-TP) =", D_TP)
print("Average delay of total vehicle (D-TV) =", D_TV)
print("Average delay of auto passengers (D-AP) =", D_AP)
print("Average delay of bus passengers (D-BP) =", D_BP)

print(D_AP)
print(D_BP)
print(D_TP)
print(D_TV)

