import xml.etree.ElementTree as ET

fileName = "tripInfo_VC_new_0.9.xml"
tree = ET.ElementTree(file=fileName)
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
    duration = tripinfo.get('duration')
    dic = (id, duration)
    print(dic)
    if id.find(id_arterialCarFlow) is not -1:
        Duration_arCar = duration
        print("Duration_arCar=" , Duration_arCar)
        cal_arterialCar = cal_arterialCar + float(Duration_arCar)
        cal_aCar = cal_aCar + 1
        print("aCar")
    if id.find(id_arterialBusFlow) is not -1:
        Duration_arBus = duration
        print("Duration_arEmgVehicle=" , Duration_arBus )
        cal_arterialBus = cal_arterialBus + float(Duration_arBus)
        cal_aBus = cal_aBus +1
        print("aBus")
    if id.find(id_SideCarFlow) is not -1:
        Duration_sCar = duration
        print("Duration_sCar=" ,Duration_sCar)
        cal_sideCar = cal_sideCar + float(Duration_sCar)
        cal_sCar = cal_sCar +1
        print("sCar")


print("------------------------------")
print("--- ",fileName," ---")
print("emg_vehicle AVG traveltime=", round((cal_arterialBus/cal_aBus),2))
print("arterial car traveltime=", round((cal_arterialCar/cal_aCar),2))
print("sideCar traveltime=", round((cal_sideCar/cal_sCar),2))
print("totalCar traveltime=", round((cal_sideCar+cal_arterialCar+cal_arterialBus)/(cal_aBus+cal_aCar+cal_sCar),2))
