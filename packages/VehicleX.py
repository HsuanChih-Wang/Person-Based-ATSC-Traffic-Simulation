class vehicleX:


    def __init__(self, ID, type, order, dist, speed, occupancy, isQueue, nextTLSID, nextTLSIndex):
        self.ID = ID
        self.type = type
        self.order = order
        self.dist = dist
        self.speed = speed
        self.occupancy = occupancy
        self.isQueue = isQueue
        self.nextTLSID = nextTLSID


        self.nextTLSphase = phase
    

    def __str__(self):
        return 'Vehicle(Order = {0}, isQueue = {1}, ID = {2}, type = {3}, dist = {4}, speed = {5}, occu = {6}, TLSid = {7}, TLSphase = {8})'.format(
             self.order, self.isQueue, self.ID, self.type, self.dist, self.speed, self.occupancy, self.nextTLSID, self.nextTLSphase)

# acct = Account('Justin', '123-4567', 1000)
# acct.deposit(500)
# acct.withdraw(200)
# print(acct)