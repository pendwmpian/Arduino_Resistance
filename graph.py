import threading
import serial
import datetime
import time
import csv
import matplotlib.pyplot as plt
from collections import deque

com = serial.Serial("/dev/ttyACM0", 115200)

x = deque([])
y = deque([])
fig, ax = plt.subplots()
time_scale = 5.0

def ReadSerial():
    global x
    global y
    val_raw = com.readline().decode("utf-8").rstrip("\r\n")
    """
    try:
        val = float(val_raw.split(" ")[1])
        time = float(val_raw.split(" ")[0])
        x.append(time / 1000000.0)
        y.append(val)
    except:
        print("Could not communicate with device.")
    """

def SerialProgram():
    while True:
        ReadSerial()
        print(time.time_ns())

th0 = threading.Thread(target=SerialProgram, args=())
th0.start()

clfc = 0
"""
while True:
    
    val_raw = com.readline().decode("utf-8").rstrip("\r\n")
    try:
        val = float(val_raw)
    except:
        continue
    time = datetime.datetime.now()
    time_sec = (time - time_base).seconds + (time - time_base).microseconds / 1000000.0

    x.append(time_sec)
    y.append(val)
    

    clfc += 1
    if clfc % 30 == 0:
        ax.cla()

    while len(x) > 0 and x[-1] - x[0] > time_scale:
        x.popleft()
        y.popleft()

    if len(x) > 0:
        ax.set_xlim((x[-1] - time_scale, x[-1]))
        ax.plot(x, y, color='C0', linestyle='-')

        ax.set_xlabel('time [sec]')
        ax.set_ylabel('Voltage [mV]')
        plt.pause(0.1)

    import psutil
    mem = psutil.virtual_memory().free / 1e9
    #print(f'memory used: {mem} [GB]')
"""