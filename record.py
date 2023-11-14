import os
import threading
import serial
from serial.tools import list_ports
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import time
import csv
import cv2
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from collections import deque
from queue import Queue


com = serial.Serial("/dev/ttyACM0", 9600)
frame = None
vid_w = None
#fig, ax = plt.subplots()
time_scale = 5.0

lock = threading.Lock()

ports = list_ports.comports()
devices = [info.device for info in ports]

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title('matplotlib graph')
        
        
        self.th_camera = None
        self.cameraID = -1
        self.deviceID = ""
        self.video_display = False
        self.graph_display = False
        self.cap = None
        self.com = None

        self.graph_x = deque([])
        self.graph_y = deque([])
        self.time_loop_cnt = 0
        self.time_start_rec = 0
        self.graph_display_clfc = 0

        frame1 = ttk.Frame(self.master, padding=10)
        frame1.grid(row=2, column=0, sticky=tk.E)

        IDirLabel = ttk.Label(frame1, text="Save to folder", padding=(5, 2))
        IDirLabel.pack(side=tk.LEFT)

        self.entry1 = tk.StringVar(self.master)
        IDirEntry = ttk.Entry(frame1, textvariable=self.entry1, width=60)
        IDirEntry.pack(side=tk.LEFT)

        IDirButton = ttk.Button(frame1, text="Browse...", command=self.dirdialog_clicked)
        IDirButton.pack(side=tk.LEFT)

        frame2 = ttk.Frame(self.master, padding=10)
        frame2.grid(row=1, column=0, sticky=tk.E)

        combo_string = tk.StringVar()
        self.combobox_dev = ttk.Combobox(frame2, textvariable=combo_string, values=devices)
        self.combobox_dev.pack(side=tk.LEFT)

        self.DevGraphButton = ttk.Button(frame2, text="Show Graph", command=self.showgraph_clicked)
        self.DevGraphButton.pack(side=tk.LEFT)

        camera_devices = self.CameraIndexes()
        combo_string_camera = tk.StringVar()
        self.combobox_camera = ttk.Combobox(frame2, textvariable=combo_string_camera, values=["Camera " + str(i) for i in camera_devices])
        self.combobox_camera.pack(side=tk.LEFT)

        self.CameraShowButton = ttk.Button(frame2, text="Show Preview", command=self.cameradisplay_clicked)
        self.CameraShowButton.pack(side=tk.LEFT)

        frame3 = ttk.Frame(self.master, padding=10)
        frame3.grid(row=3, column=1, sticky=tk.E)
        self.canvas1 = tk.Canvas(frame3, width=640, height=480)
        self.canvas1.pack()
        self.video_frame_timer()

        frame4 = ttk.Frame(self.master, padding=10)
        frame4.grid(row=3, column=0, sticky=tk.E)
        self.fig = plt.Figure()
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.fig_canvas = FigureCanvasTkAgg(self.fig, frame4)
        self.toolbar = NavigationToolbar2Tk(self.fig_canvas, frame4)
        self.fig_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.anim = animation.FuncAnimation(self.fig, self.next_graph, interval=100, blit=False)
        #self.anim.event_source.stop()

        self.master.protocol("WM_DELETE_WINDOW", self.click_close)

        self.halt_thread = False
        self.th_camera = threading.Thread(target=self.CameraCapture)
        self.th_camera.start()
        self.th_serial = threading.Thread(target=self.SerialProgram)
        self.th_serial.start()

    def dirdialog_clicked(self):
        iDir = os.path.abspath(os.path.dirname(__file__))
        iDirPath = filedialog.askdirectory(initialdir = iDir)
        self.entry1.set(iDirPath)

    def showgraph_clicked(self):
        if self.graph_display is False:
            if self.changedevice():
                self.graph_display = True
                self.anim.event_source.start()
                self.DevGraphButton.configure(text="Hide Graph")
        else:
            self.graph_display = False
            self.anim.event_source.stop()
            self.DevGraphButton.configure(text="Show Graph")

    def cameradisplay_clicked(self):
        if self.video_display is False:
            if self.changecamera():
                self.video_display = True
                self.CameraShowButton.configure(text="Hide Preview")
        else:
            self.video_display = False
            self.CameraShowButton.configure(text="Show Preview")

    def click_close(self):
        self.halt_thread = True
        if self.video_display is True:
            self.video_display = False
        self.th_camera.join()
        exit()

    def next_frame(self):
        if frame is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(rgb)
            x = self.canvas1.winfo_reqwidth()/pil.width
            y = self.canvas1.winfo_reqheight()/pil.height
            ratio = x if x<y else y
            pil = pil.resize((int(ratio*pil.width),int(ratio*pil.height)))
            self.image_video_display = ImageTk.PhotoImage(pil, master=self.master)
            self.canvas1.create_image(0,0, image=self.image_video_display, anchor =tk.NW)

    def video_frame_timer(self):
        if self.video_display:
            self.next_frame()
        self.master.after(50, self.video_frame_timer)

    def next_graph(self, i):
        if len(self.graph_x) == len(self.graph_y):
            self.graph_display_clfc += 1
            if self.graph_display_clfc % 30 == 0:
                self.ax.cla()

            while len(self.graph_x) > 1 and self.graph_x[-1] - self.graph_x[0] > time_scale:
                self.graph_x.popleft()
                self.graph_y.popleft()

            if len(self.graph_x) > 0:
                self.ax.set_xlim((self.graph_x[-1] - time_scale, self.graph_x[-1]))
                self.ax.plot(self.graph_x, self.graph_y, color='C0', linestyle='-')

                self.ax.set_xlabel('time [sec]')
                self.ax.set_ylabel('Voltage [mV]')

    def graph_display_timer(self):
        if self.graph_display:
            self.next_graph()
        self.master.after(200, self.graph_display_timer)

    def getCameraDevID(self):
        s = self.combobox_camera.get()
        if len(s) < 7:
            return -1
        else:
            return int(s[7:])
        
    def changecamera(self):
        camID = self.getCameraDevID()
        if camID != -1:
            if self.cameraID == camID:
                return True
            with lock:
                if self.cap != None:
                    self.cap.release()
                self.cap = cv2.VideoCapture(camID)
            self.cameraID = camID
            return True
        else:
            return False

    def changedevice(self):
        dev = self.combobox_dev.get()
        if dev != "":
            if self.deviceID == dev:
                return True
            with lock:
                self.com = serial.Serial(dev, 9600)
            self.deviceID = dev
            return True
        else:
            return False

    def CameraIndexes(self):
        index = 0
        arr = []
        i = 10
        while i > 0:
            cap = cv2.VideoCapture(index)
            if cap.read()[0]:
                arr.append(index)
                cap.release()
            index += 1
            i -= 1
        return arr

    def CameraCapture(self):
        global frame
        global vid_w
        while True:
            if self.halt_thread is True:
                break
            if self.cap is not None:
                ret, frame = self.cap.read()
                if vid_w is not None:
                    vid_w.write(frame)
            
    def ReadSerial(self):
        val_raw = self.com.readline().decode("utf-8").rstrip("\r\n")
        try:
            val = float(val_raw.split(" ")[1])
            time = float(val_raw.split(" ")[0])
            time = time + self.time_loop_cnt * 4294967296 - self.time_start_rec
            if len(self.graph_x) > 0 and time / 1000000.0 < self.graph_x[-1]:
                self.time_loop_cnt += 1
                time += 4294967296
            self.graph_x.append(time / 1000000.0)
            self.graph_y.append(val)
        except:
            print("Could not communicate with device.")

    def SerialProgram(self):
        while True:
            if self.halt_thread is True:
                break
            if self.graph_display:
                self.ReadSerial()
            print(time.time_ns())


root = tk.Tk()
app = Application(master=root)
app.mainloop()

"""
th0 = threading.Thread(target=SerialProgram, args=())
th0.start()

while True:

    while len(x) > 0 and x[-1] - x[0] > time_scale:
        x.popleft()
        y.popleft()

    if len(x) > 0:
        ax.set_xlim((x[-1] - time_scale, x[-1]))
        ax.plot(x, y, color='C0', linestyle='-')

        ax.set_xlabel('time [sec]')
        ax.set_ylabel('Voltage [mV]')

        plt.pause(0.1)
"""