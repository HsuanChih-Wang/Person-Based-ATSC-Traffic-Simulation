class Car:
    wheels = 4    # <- Class variable
    brand = '123'
    def __init__(self, name):
        self.name = name    # <- Instance variable

    def setBrand(self,brand):
        self.brand = brand

car1 = Car('car1')
car2 = Car('car2')

car1.wheels = 3
car1.setBrand('ttt')

print(car2.brand)

print(car1.wheels)
print(car1.__class__.wheels)
print(car1.brand)
print(car1.__class__.brand)