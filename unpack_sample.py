import os
import struct
import matplotlib.pyplot as plt

path = "/path/to/datafile"

def loadData(path):
    data = []
    time = []
    time_diff_ns = 0
    nrow = 0
    time_base = 0
    time_loop_cnt = 0
    with open(path, 'rb') as f:
        f.seek(0, os.SEEK_SET)
        if f.read(3).decode("ascii") != "DAT":
            raise Exception
            return
        f.seek(4, os.SEEK_SET)
        nrow = struct.unpack('<L', f.read(4))[0]
        time_diff_ns = struct.unpack('<L', f.read(4))[0]
        time_diff_ms = time_diff_ns // 1000
        f.seek(32, os.SEEK_SET)
        time_base = struct.unpack('<L', f.read(4))[0]
        time.append(time_diff_ms)
        data.append(struct.unpack('<l', f.read(4))[0])
        for i in range(nrow - 1):
            time_buf = struct.unpack('<L', f.read(4))[0] + time_diff_ms
            if time_buf + time_loop_cnt * 4294967296 - time_base < time[-1]:
                time_loop_cnt += 1
            time.append(time_buf + time_loop_cnt * 4294967296 - time_base)
            data.append(struct.unpack('<l', f.read(4))[0])
    return data, time


def convertVolt(data, amp_resistance):
    adc_multiplier = 0.125
    amp_gain = 1.0 + (100000.0 / amp_resistance)
    volt_coeff = adc_multiplier / amp_gain
    return data * volt_coeff

def main():
    d, t = loadData(path)
    d = [convertVolt(_, 390.0) for _ in d]
    t = [_ / 1000000.0 for _ in t]
    fig, ax = plt.subplots()
    ax.plot(t, d, color='C0', linestyle='-')
    ax.set_xlabel('time [sec]')
    ax.set_ylabel('Voltage [mV]')
    plt.show()

if __name__ == '__main__':
    main()