from AC_COMBOX import AC_COMBOX 
from time import sleep

cl = AC_COMBOX()

while True:
    print("Volts: ", cl.Poll().Volt)
    print("Current: ", cl.Poll().Current)
    print("Power: ", cl.Poll().Power)
    print("Energy: ", cl.Poll().Energy)
    print("Frequency: ", cl.Poll().Freq)
    print("Pf: ", cl.Poll().Pf)
    print("Alarm: ", cl.Poll().Alarm)
    print("===============================================")

    sleep(1)