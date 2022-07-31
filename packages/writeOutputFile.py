
class writeOutputFile():
    def __init__(self, fileName):
        self.fileName = fileName

    def writeFile(self):
        file = open(self.fileName, "a")
        file.write("\n [CYCLE END] \n")
        file.write("\n[ Step = "+ str(traci.simulation.getTime()) + "]\n")
        file.write("----GijkLengthCal(tau)----\n")
        ile.write("[0]: %s [1]: %s [2]: %s [3]: %s \n[4]: %s [5]: %s [6]: %s [7]: %s"
                   % (str(self.GijkLengthCal[0]), str(self.GijkLengthCal[1]), str(self.GijkLengthCal[2]), str(self.GijkLengthCal[3]),
                      str(self.GijkLengthCal[4]), str(self.GijkLengthCal[5]), str(self.GijkLengthCal[6]), str(self.GijkLengthCal[7])))
        # 關閉檔案
        file.close()