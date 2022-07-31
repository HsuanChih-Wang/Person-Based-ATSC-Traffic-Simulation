import xml.etree.cElementTree as ET
import csv


f1 = 'thesis_single_priority_fullInfo(OBU).xml'
f2 = 'thesis_single_priority_fullInfo.xml'

fileName1 = [f1, f2]


id_arterialCarFlow = ["Phase3", "Phase4", "Phase7", "Phase8"]
id_sideCarFlow = ["Phase1", "Phase2", "Phase5", "Phase6"]
id_BusFlow = ["Bus"]

# #乘載人數
# bus_Occupancy = 30
# auto_Occupancy = 1.5

fullList = []
OBUlist = []
Signallist = []


def readFullOutputFile():
    for file in fileName1:

        tree = ET.ElementTree(file=file)
        root = tree.getroot()
        totalEnergyConsumed = 0
        totalAcceleration = 0

        for timestamp in root:
            for vehicles in timestamp:
                for vehicle in vehicles:
                    if (vehicle.attrib.get('id')[0:3] == 'Bus'):
                        BusID = vehicle.attrib.get('id')
                        speed = vehicle.attrib.get('speed')
                        print("TimeStamp = %s BusID = %s speed = %s" % (timestamp.attrib.get('timestep'), BusID, speed))
                        fileOpen = open("OBU_Speed_result_" + file + ".csv", "a")
                        fileOpen.write(timestamp.attrib.get('timestep') + "," + BusID + "," + speed + "\n")

def combineFullOutputFile_and_SignalResults():
    # 開啟 CSV 檔案
    with open('OBU_Speed_result_thesis_single_priority_fullInfo.xml.csv', newline='') as OBUfile:
        OBUrows = csv.reader(OBUfile)
        for row in OBUrows:
            OBUlist.append(row)
    with open('signalResult.csv', newline='') as signalFile:
        signalRows = csv.reader(signalFile)
        for row in signalRows:
            Signallist.append(row)

    print(OBUlist)
    print(Signallist)

    for row1 in OBUlist:
        for row2 in Signallist:
            if (row1[0] == row2[0]):
                full = [row1[0] + "," + row1[1] + "," + row1[2] + "," + row2[1] + "," + row2[2]]
                fullList.append(full)
                break

    print(fullList)

    with open('output.csv', 'w', newline='') as csvfile:
        # 建立 CSV 檔寫入器
        writer = csv.writer(csvfile)
        writer.writerows(fullList)



combineFullOutputFile_and_SignalResults()