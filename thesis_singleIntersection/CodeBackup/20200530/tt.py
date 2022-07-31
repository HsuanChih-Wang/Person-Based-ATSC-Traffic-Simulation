import math
import traci
from traci._trafficlight import Phase

from thesis import PhaseObject
from thesis import RSUObject
from thesis import SignalPlanObject
from thesis import OBUObject

class Person:
    def __init__(self, fname, lname):
        self.firstname = fname
        self.lastname = lname

    def printname(self):
        print(self.firstname, self.lastname)

class Student(Person):
    def __init__(self, fname, lname, year):
        super().__init__(fname, lname)
        self.graduationyear = year

    def welcome(self):
        print("Welcome", self.firstname, self.lastname, "to the class of", self.graduationyear)


x = Student("John","Doe", 2019)
x.printname()
x.welcome()
print(type(Person))


class RSU():
    def __init__(self, ID, location):
        self.ID = ID
        self.location = location

class OPT():
    def __init__(self, RSU):
        self.RSU = RSU

rsu1 = RSU('I1', [0,0])
opt = OPT(rsu1)

print(opt.RSU.ID)

