import xml.etree.ElementTree as ET

f1 = 'thesis_multiple_priority_tripInfo_1.xml'
f2 = 'thesis_multiple_priority_tripInfo_2.xml'
f3 = 'thesis_multiple_priority_tripInfo_3.xml'
f4 = 'thesis_multiple_priority_tripInfo_4.xml'
f5 = 'thesis_multiple_priority_tripInfo_5.xml'

fileName1 = [f1, f2, f3, f4, f5]

id_MainArterial_AutoFlow = "Auto_Arterial"
id_CrossStreets_AutoFlow = "Auto_CrossStreets"
id_BusFlow = "Bus"

#乘載人數
bus_Occupancy = 30
auto_Occupancy = 1.5

D_AV_MainArterial_result = []
WC_AV_MainArterial_result = []
D_AP_MainArterial_result = []
WC_AP_MainArterial_result = []
D_AV_CrossStreets_result = []
WC_AV_CrossStreets_result = []
D_AP_CrossStreets_result = []
WC_AP_CrossStreets_result = []
D_BV_result = []
WC_BV_result = []
D_BP_result = []
WC_BP_result = []
D_TV_result = []
WC_TV_result = []
D_TP_result = []
WC_TP_result = []

for file in fileName1:
    tree = ET.ElementTree(file=file)
    root = tree.getroot()

    delay_MainArterial_Auto = 0  # 計算幹道小客車延滯(waiting time)
    delay_CrossStreets_Auto = 0  # 計算支道小客車延滯
    delay_TotalAutoCar = 0  # 計算小客車延滯
    delay_Bus = 0  # 計算公車延滯

    waitingCount_MainArterial_Auto = 0  # 計算幹道小客車停等次數
    waitingCount_CrossStreets_Auto = 0  # 計算支道小客車停等次數
    waitingCount_TotalAutoCar = 0
    waitingCount_Bus = 0

    numOfMainArterialAuto = 0  # 計數幹道小客車數量
    numOfCrossStreetAuto = 0  # 計數支道小客車數量
    numOfTotalAuto = 0  # 計數小汽車數量
    numOfBus = 0  # 計數公車數量


    for tripinfo in root.findall('tripinfo'):  # 找tag叫做tripinfo者
        id = tripinfo.get('id')  # 取得標籤 id 的值
        waitingTime = tripinfo.get('waitingTime')  # 取得標籤 waitingTime 的值
        waitingCount = int(tripinfo.get('waitingCount')) # 取得標籤 waitingCount 的值
        print("%s, %s" % (id, waitingTime))  # 印出兩者
        print(tripinfo.get('depart'))
        if float(tripinfo.get('depart')) >= 300 and float(tripinfo.get('depart')) <= 7300:
            if id.find(id_MainArterial_AutoFlow) is not -1:
                WaitingTime_MainArterial_Auto = waitingTime
                print("WaitingTime_MainArterial_Auto=", WaitingTime_MainArterial_Auto)
                delay_MainArterial_Auto = delay_MainArterial_Auto + float(WaitingTime_MainArterial_Auto)  # 累加幹道小客車延滯
                waitingCount_MainArterial_Auto = waitingCount_MainArterial_Auto + waitingCount  # 累加幹道小客車停等次數
                numOfMainArterialAuto = numOfMainArterialAuto + 1  # 幹道小客車數量+1
                print("numOfMainArterialAuto = ", numOfMainArterialAuto)

            if id.find(id_CrossStreets_AutoFlow) is not -1:
                WaitingTime_CrossStreets_Auto = waitingTime
                print("WaitingTime_MainArterial_Auto=", WaitingTime_CrossStreets_Auto)
                delay_CrossStreets_Auto = delay_CrossStreets_Auto + float(WaitingTime_CrossStreets_Auto)  # 累加支道小客車延滯
                waitingCount_CrossStreets_Auto = waitingCount_CrossStreets_Auto + waitingCount
                numOfCrossStreetAuto = numOfCrossStreetAuto + 1  # 支道小客車數量+1
                print("numOfCrossStreetAuto = ", numOfCrossStreetAuto)

            if id.find(id_BusFlow) is not -1:
                WaitingTime_Bus = waitingTime
                print("WaitingTime_Bus=", WaitingTime_Bus)
                delay_Bus = delay_Bus + float(WaitingTime_Bus) #累加公車延滯
                waitingCount_Bus = waitingCount_Bus + waitingCount
                numOfBus = numOfBus + 1  #公車數量+1
                print("numOfBus = ", numOfBus)

    D_AV_MainArterial = round((delay_MainArterial_Auto / numOfMainArterialAuto), 2)
    WC_AV_MainArterial = round((waitingCount_MainArterial_Auto / numOfMainArterialAuto), 2)
    
    D_AP_MainArterial = round((delay_MainArterial_Auto / (numOfMainArterialAuto * auto_Occupancy)), 2)
    WC_AP_MainArterial = round((waitingCount_MainArterial_Auto / (numOfMainArterialAuto * auto_Occupancy)), 2)

    D_AV_CrossStreet = round((delay_CrossStreets_Auto / numOfCrossStreetAuto), 2)
    WC_AV_CrossStreet = round((waitingCount_CrossStreets_Auto / numOfCrossStreetAuto), 2)

    D_AP_CrossStreet = round((delay_CrossStreets_Auto / (numOfCrossStreetAuto * auto_Occupancy)), 2)
    WC_AP_CrossStreet = round((waitingCount_CrossStreets_Auto / (numOfCrossStreetAuto * auto_Occupancy)), 2)

    D_BV = round((delay_Bus / numOfBus), 2)
    WC_BV = round((waitingCount_Bus / numOfBus), 2)
    
    D_BP = round((delay_Bus / (numOfBus * bus_Occupancy)), 2)
    WC_BP = round((waitingCount_Bus / (numOfBus * bus_Occupancy)), 2)

    delay_TotalAutoCar = delay_MainArterial_Auto + delay_CrossStreets_Auto
    waitingCount_TotalAutoCar = waitingCount_MainArterial_Auto + waitingCount_CrossStreets_Auto
    numOfTotalAuto = numOfMainArterialAuto + numOfCrossStreetAuto + numOfBus

    D_TV = round(((delay_TotalAutoCar + delay_Bus) / (numOfTotalAuto + numOfBus)), 2)
    WC_TV = round(((waitingCount_TotalAutoCar + waitingCount_Bus) / (numOfTotalAuto + numOfBus)), 2)

    D_TP = round(((delay_TotalAutoCar + delay_Bus) / ((numOfMainArterialAuto + numOfCrossStreetAuto) * auto_Occupancy + (numOfBus * bus_Occupancy))), 2)
    WC_TP = round(((waitingCount_TotalAutoCar + waitingCount_Bus) / (
                (numOfMainArterialAuto + numOfCrossStreetAuto) * auto_Occupancy + (numOfBus * bus_Occupancy))), 2)

    print("--- ", file, " --- ")
    print("------------------------------")
    print("delay_MainArterial_Auto = ", delay_MainArterial_Auto)
    print("delay_CrossStreets_Auto = ", delay_CrossStreets_Auto)
    print("delay_TotalAutoCar = ", delay_TotalAutoCar)
    print("delay_Bus = ", delay_Bus)

    print("waitingCount_MainArterial_Auto = ", waitingCount_MainArterial_Auto)
    print("waitingCount_CrossStreets_Auto = ", waitingCount_CrossStreets_Auto)
    print("waitingCount_TotalAutoCar = ", waitingCount_TotalAutoCar)
    print("waitingCount_Bus =", waitingCount_Bus)

    print("numOfMainArterialAuto = ", numOfMainArterialAuto)
    print("numOfCrossStreetAuto = ", numOfCrossStreetAuto)
    print("numOfBus = ", numOfBus)

    print("D-AV (MainArterial) =", D_AV_MainArterial)
    print("WC-AV (MainArterial) =", WC_AV_MainArterial)
    print("D-AP (MainArterial) =", D_AP_MainArterial)
    print("WC-AP (MainArterial) =", WC_AP_MainArterial)
    print("D-AV (CrossStreets) =", D_AV_CrossStreet)
    print("WC-AV (CrossStreets) =", WC_AV_CrossStreet)
    print("D-AP (CrossStreets) =", D_AP_CrossStreet)
    print("WC-AP (CrossStreets) =", WC_AP_CrossStreet)

    print("D-BV =", D_BV)
    print("WC-BV =", WC_BV)
    print("D-BP =", D_BP)
    print("WC-BP =", WC_BP)
    print("D-TV =", D_TV)
    print("WC-TV =", WC_TV)
    print("D-TP =", D_TP)
    print("WC-TP =", WC_TP)

    D_AV_MainArterial_result.append(D_AV_MainArterial)
    WC_AV_MainArterial_result.append(WC_AV_MainArterial)
    D_AP_MainArterial_result.append(D_AP_MainArterial)
    WC_AP_MainArterial_result.append(WC_AP_MainArterial)
    D_AV_CrossStreets_result.append(D_AV_CrossStreet)
    WC_AV_CrossStreets_result.append(WC_AV_CrossStreet)
    D_AP_CrossStreets_result.append(D_AP_CrossStreet)
    WC_AP_CrossStreets_result.append(WC_AP_CrossStreet)
    D_BV_result.append(D_BV)
    WC_BV_result.append(WC_BV)
    D_BP_result.append(D_BP)
    WC_BP_result.append(WC_BP)
    D_TV_result.append(D_TV)
    WC_TV_result.append(WC_TV)
    D_TP_result.append(D_TP)
    WC_TP_result.append(WC_TP)


sD_AV_MainArterial_result = [str(a) for a in D_AV_MainArterial_result]
sWC_AV_MainArterial_result = [str(a) for a in WC_AV_MainArterial_result]
sD_AP_MainArterial_result = [str(a) for a in D_AP_MainArterial_result]
sWC_AP_MainArterial_result = [str(a) for a in WC_AP_MainArterial_result]

sD_AV_CrossStreets_result = [str(a) for a in D_AV_CrossStreets_result]
sWC_AV_CrossStreets_result = [str(a) for a in WC_AV_CrossStreets_result]

sD_AP_CrossStreets_result = [str(a) for a in D_AP_CrossStreets_result]
sWC_AP_CrossStreets_result = [str(a) for a in WC_AP_CrossStreets_result]

sD_BV = [str(a) for a in D_BV_result]
sWC_BV = [str(a) for a in WC_BV_result]
sD_BP = [str(a) for a in D_BP_result]
sWC_BP = [str(a) for a in WC_BP_result]
sD_TV = [str(a) for a in D_TV_result]
sWC_TV = [str(a) for a in WC_TV_result]
sD_TP = [str(a) for a in D_TP_result]
sWC_TP = [str(a) for a in WC_TP_result]


print(','.join(sD_AV_MainArterial_result))
print(','.join(sWC_AV_MainArterial_result))

print(','.join(sD_AP_MainArterial_result))
print(','.join(sWC_AP_MainArterial_result))

print(','.join(sD_AV_CrossStreets_result))
print(','.join(sWC_AV_CrossStreets_result))

print(','.join(sD_AP_CrossStreets_result))
print(','.join(sWC_AP_CrossStreets_result))

print(','.join(sD_BV))
print(','.join(sWC_BV))

print(','.join(sD_BP))
print(','.join(sWC_BP))

print(','.join(sD_TV))
print(','.join(sWC_TV))

print(','.join(sD_TP))
print(','.join(sWC_TP))