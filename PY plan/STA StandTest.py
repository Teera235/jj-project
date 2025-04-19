import tkinter as tk
from tkinter import messagebox, ttk
import serial
import threading
import time
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import logging
from datetime import datetime

class ThrustMeasurementApp:
    """STA StandTest Loadcell 20 kg (thrust)"""
    
    CONFIG = {
        'serial_port': 'COM5',
        'baud_rate': 9600,
        'serial_timeout': 1,
        'plot_interval_ms': 100,
        'thrust_min_kgf': 0.0,
        'thrust_max_kgf': 12.0, 
        'gravity': 9.81  
    }

    def __init__(self, root):
        """Initialize the application with GUI and plot setup."""
        self.root = root
        self.root.title("Rocket Thrust Measurement System")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logging.basicConfig(filename='thrust_measurement.log', level=logging.INFO,
                           format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()

        self.ser = None
        self.data = []
        self.is_measuring = False
        self.start_time = None
        self.read_thread = None

        self.setup_gui()
        
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.line, = self.ax.plot([], [], lw=2, color='blue')
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Thrust (kgf)')
        self.ax.set_title('RThrust Measurement')
        self.ax.grid(True)
        self.ax.set_ylim(0, 12) 
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=self.CONFIG['plot_interval_ms'], blit=True)

    def setup_gui(self):
        """Configure the GUI layout and widgets."""
        self.plot_frame = ttk.Frame(self.root)
        self.plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=1, padx=10, pady=10)

        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        self.start_button = ttk.Button(self.control_frame, text="Start Measurement", command=self.start_measurement)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(self.control_frame, text="Stop Measurement", 
                                     command=self.stop_measurement, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(self.control_frame, text="Status: Idle")
        self.status_label.pack(side=tk.LEFT, padx=10)

    def start_measurement(self):
        """Initiate thrust measurement process."""
        if self.ser is None:
            try:
                self.ser = serial.Serial(self.CONFIG['serial_port'], self.CONFIG['baud_rate'], 
                                       timeout=self.CONFIG['serial_timeout'])
                self.logger.info(f"Connected to Arduino on {self.CONFIG['serial_port']}")
                time.sleep(2) 
            except serial.SerialException as e:
                self.logger.error(f"Serial connection failed: {e}")
                messagebox.showerror("Connection Error", f"Cannot connect to Arduino: {e}")
                return

        self.data = []
        self.start_time = time.time()
        self.is_measuring = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Measuring...")
        
        self.ax.clear()
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Thrust (kgf)')
        self.ax.set_title('Real-time Thrust Measurement')
        self.ax.grid(True)
        self.ax.set_ylim(0, 12)  
        self.line, = self.ax.plot([], [], lw=2, color='red')
        
        self.read_thread = threading.Thread(target=self.read_from_serial, daemon=True)
        self.read_thread.start()

    def stop_measurement(self):
        """Stop measurement and save data to Excel."""
        self.is_measuring = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Idle")

        if self.data:
            try:
                df = pd.DataFrame(self.data, columns=['Time (s)', 'Thrust (kgf)'])
                df['Thrust (N)'] = df['Thrust (kgf)'] * self.CONFIG['gravity']
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f'thrust_data_{timestamp}.xlsx'
                df.to_excel(filename, index=False)
                self.logger.info(f"Data saved to {filename}")
                messagebox.showinfo("Success", f"Data saved to {filename}")
            except Exception as e:
                self.logger.error(f"Failed to save data: {e}")
                messagebox.showerror("Save Error", f"Failed to save data: {e}")

        self.close_serial()
    

    def read_from_serial(self):
        """Read thrust data from Arduino in a separate thread."""
        while self.is_measuring:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if line:
                    try:
                        thrust_kgf = float(line)
                        if self.CONFIG['thrust_min_kgf'] <= thrust_kgf <= self.CONFIG['thrust_max_kgf']:
                            current_time = time.time() - self.start_time
                            self.data.append([current_time, thrust_kgf])
                        else:
                            self.logger.warning(f"Thrust value out of range: {thrust_kgf}")
                    except ValueError:
                        self.logger.warning(f"Invalid data received: {line}")
            except serial.SerialException as e:
                self.logger.error(f"Serial read error: {e}")
                self.is_measuring = False
                self.root.after(0, lambda: messagebox.showerror("Serial Error", f"Serial communication failed: {e}"))
                break

    def update_plot(self, frame):
        """Update the real-time plot with latest data."""
        if self.is_measuring and self.data:
            times = [d[0] for d in self.data]
            thrusts = [d[1] for d in self.data]
            self.line.set_data(times, thrusts)
            self.ax.set_xlim(0, max(times) + 0.1 if times else 1) 
        return self.line,

    def close_serial(self):
        """Safely close the serial connection."""
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
                self.logger.info("Serial connection closed")
            except serial.SerialException as e:
                self.logger.error(f"Error closing serial port: {e}")
            finally:
                self.ser = None

    def on_closing(self):
        """Handle application shutdown."""
        self.is_measuring = False
        self.close_serial()
        self.root.destroy()
        
    

if __name__ == "__main__":
    root = tk.Tk()
    app = ThrustMeasurementApp(root)
    root.mainloop()
