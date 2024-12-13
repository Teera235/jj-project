import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial
import threading
import time
import matplotlib.animation as animation
import numpy as np

SERIAL_PORT = 'COM5'
BAUD_RATE = 9600
TIME_WINDOW = 60

class SerialReader(threading.Thread):
    def __init__(self, port, baud_rate, data_callback):
        threading.Thread.__init__(self)
        self.port = port
        self.baud_rate = baud_rate
        self.data_callback = data_callback
        self.running = True
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
        except serial.SerialException as e:
            messagebox.showerror("Serial Port Error", f"ไม่สามารถเชื่อมต่อกับพอร์ต {self.port}:\n{e}")
            self.running = False

    def run(self):
        while self.running:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode('utf-8').strip()
                    if line:
                        parts = line.split(',')
                        if len(parts) == 2:
                            try:
                                current_time = float(parts[0])
                                weight = float(parts[1])
                                self.data_callback(current_time, weight)
                            except ValueError:
                                print(f"ข้อมูลไม่ถูกต้อง: {line}")
            except serial.SerialException as e:
                print(f"ข้อผิดพลาดในการอ่านข้อมูลจากซีเรียล: {e}")
                self.running = False
            time.sleep(0.1)

    def stop(self):
        self.running = False
        if self.ser.is_open:
            self.ser.close()

class WeightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Weight Monitoring")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)

        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.line, = self.ax.plot([], [], label="Weight (kg)", color="blue")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Weight (kg)")
        self.ax.set_title("Real-Time Weight Monitoring")
        self.ax.legend()
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        self.info_frame = ttk.Frame(self.root)
        self.info_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.current_weight_label = ttk.Label(self.info_frame, text="Current Weight: N/A kg", font=("Arial", 14))
        self.current_weight_label.pack(pady=5)

        self.average_weight_label = ttk.Label(self.info_frame, text="Average Weight: N/A kg", font=("Arial", 14))
        self.average_weight_label.pack(pady=5)

        self.button_frame = ttk.Frame(self.root)
        self.button_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        self.start_button = ttk.Button(self.button_frame, text="Start", command=self.start_reading)
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(self.button_frame, text="Stop", command=self.stop_reading, state="disabled")
        self.stop_button.pack(side="left", padx=5)

        self.times = []
        self.weights = []

        self.serial_thread = None

        self.ani = animation.FuncAnimation(self.fig, self.update_plot, interval=1000, blit=False)

    def data_callback(self, current_time, weight):
        self.times.append(current_time)
        self.weights.append(weight)

        while self.times and (self.times[-1] - self.times[0]) > TIME_WINDOW:
            self.times.pop(0)
            self.weights.pop(0)

        self.current_weight_label.config(text=f"Current Weight: {weight:.3f} kg")
        if self.weights:
            average_weight = np.mean(self.weights)
            self.average_weight_label.config(text=f"Average Weight: {average_weight:.3f} kg")

    def update_plot(self, frame):
        self.ax.clear()
        self.ax.plot(self.times, self.weights, label="Weight (kg)", color="blue")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Weight (kg)")
        self.ax.set_title("Real-Time Weight Monitoring")
        self.ax.legend()
        self.ax.grid(True)
        self.ax.set_xlim(left=max(0, self.times[-1] - TIME_WINDOW), right=self.times[-1] + 1)
        if self.weights:
            self.ax.set_ylim(min(self.weights) - 1, max(self.weights) + 1)
        self.canvas.draw()

    def start_reading(self):
        if not self.serial_thread or not self.serial_thread.is_alive():
            self.serial_thread = SerialReader(SERIAL_PORT, BAUD_RATE, self.data_callback)
            self.serial_thread.start()
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")

    def stop_reading(self):
        if self.serial_thread and self.serial_thread.is_alive():
            self.serial_thread.stop()
            self.serial_thread.join()
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")

    def on_close(self):
        self.stop_reading()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WeightApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
