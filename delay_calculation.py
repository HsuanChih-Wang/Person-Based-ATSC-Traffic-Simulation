import xml.etree.ElementTree as ET

tree = ET.ElementTree(file='tripInfo_VC_new_0.9.xml')
root = tree.getroot()

for child in root:
    print(child.tag, child.attrib)

id_arterialCarFlow = "Arterial"
id_arterialBusFlow = "Emg_vehicle"
id_SideCarFlow = "SideCar"
cal_arterialCar = 0
cal_arterialBus = 0
cal_sideCar = 0
cal_aCar = 0
cal_aBus = 0
cal_sCar = 0
for tripinfo in root.findall('tripinfo'):
    id = tripinfo.get('id')
    waitingTime = tripinfo.get('waitingTime')
    dic = (id, waitingTime)
    print(dic)

    if float(tripinfo.get('depart')) >= 600:
        if id.find(id_arterialCarFlow) is not -1:
            WaitingTime_arCar = waitingTime
            print("WaitingTime_arCar=" , WaitingTime_arCar)
            cal_arterialCar = cal_arterialCar + float(WaitingTime_arCar)
            cal_aCar = cal_aCar + 1
            print("aCar")
        if id.find(id_arterialBusFlow) is not -1:
            WaitingTime_arBus = waitingTime
            print("WaitingTime_arBus=" ,WaitingTime_arBus )
            cal_arterialBus = cal_arterialBus + float(WaitingTime_arBus)
            cal_aBus = cal_aBus +1
            print("aBus")
        if id.find(id_SideCarFlow) is not -1:
            WaitingTime_sCar = waitingTime
            print("WaitingTime_sCar=" ,WaitingTime_sCar)
            cal_sideCar = cal_sideCar + float(WaitingTime_sCar)
            cal_sCar = cal_sCar +1
            print("sCar")


print("------------------------------")
print("bus delay=", round((cal_arterialBus/cal_aBus),2))
print("arterial delay=", round((cal_arterialCar/cal_aCar),2))
print("sideCar delay=", round((cal_sideCar/cal_sCar),2))
print("totalCar delay=", round((cal_sideCar+cal_arterialCar+cal_arterialBus)/(cal_aBus+cal_aCar+cal_sCar),2))
