import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import simps
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import mplcursors
import numpy as np
import os

def load_data():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(
        title="Select Weight Data CSV File",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    root.destroy()
    
    if not file_path:
        messagebox.showerror("File Selection Error", "No file was selected. Exiting the program.")
        exit(1)
    
    try:
        data = pd.read_csv(file_path)
        # Convert weight from grams to kilograms
        data["Weight (kg)"] = data["Weight (g)"] 
        return data
    except Exception as e:
        messagebox.showerror("File Read Error", f"An error occurred while reading the file:\n{e}")
        exit(1)

def calculate_basic_statistics(data):
    mean_weight = data["Weight (kg)"].mean()
    std_dev_weight = data["Weight (kg)"].std()
    return mean_weight, std_dev_weight 

def calculate_total_impulse(data):
    return simps(data["Weight (kg)"], data["Time (s)"])

def analyze_weight_change(data):
    data["Weight Change (kg)"] = data["Weight (kg)"].diff()
    return data

def apply_smoothing(weight_data, window_size=5):
    return np.convolve(weight_data, np.ones(window_size)/window_size, mode='same')

def plot_graph(data, canvas, smooth=False):
    fig, ax = plt.subplots(figsize=(6, 4))
    weight_data = data["Weight (kg)"]

    if smooth:
        weight_data = apply_smoothing(weight_data)

    line, = ax.plot(data["Time (s)"], weight_data, label="Weight", color="blue")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Weight (kg)")
    ax.set_title("Teerathap, Weight Over Time")
    ax.legend()
    ax.grid(True)

    cursor = mplcursors.cursor(line, hover=True)
    cursor.connect("add", lambda sel: sel.annotation.set_text(
        f"Time: {sel.target[0]:.2f}s\nWeight: {sel.target[1]:.3f}kg"))

    chart_type = FigureCanvasTkAgg(fig, master=canvas)
    chart_type.get_tk_widget().pack(fill="both", expand=True)
    chart_type.draw()

    x_min, x_max = data["Time (s)"].min(), data["Time (s)"].max()
    y_min, y_max = weight_data.min(), weight_data.max()

    def zoom_in():
        nonlocal x_min, x_max, y_min, y_max
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        x_range = (x_max - x_min) * 0.5
        y_range = (y_max - y_min) * 0.5
        x_min, x_max = x_center - x_range / 2, x_center + x_range / 2
        y_min, y_max = y_center - y_range / 2, y_center + y_range / 2
        ax.set_xlim([x_min, x_max])
        ax.set_ylim([y_min, y_max])
        chart_type.draw()

    def zoom_out():
        nonlocal x_min, x_max, y_min, y_max
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        x_range = (x_max - x_min) * 2
        y_range = (y_max - y_min) * 2
        x_min_new = max(data["Time (s)"].min(), x_center - x_range / 2)
        x_max_new = min(data["Time (s)"].max(), x_center + x_range / 2)
        y_min_new = max(weight_data.min(), y_center - y_range / 2)
        y_max_new = min(weight_data.max(), y_center + y_range / 2)
        x_min, x_max = x_min_new, x_max_new
        y_min, y_max = y_min_new, y_max_new
        ax.set_xlim([x_min, x_max])
        ax.set_ylim([y_min, y_max])
        chart_type.draw()

    def reset_zoom():
        nonlocal x_min, x_max, y_min, y_max
        x_min, x_max = data["Time (s)"].min(), data["Time (s)"].max()
        y_min, y_max = weight_data.min(), weight_data.max()
        ax.set_xlim([x_min, x_max])
        ax.set_ylim([y_min, y_max])
        chart_type.draw()

    def pan_left():
        nonlocal x_min, x_max
        shift = (x_max - x_min) * 0.1
        x_min, x_max = x_min - shift, x_max - shift
        ax.set_xlim([x_min, x_max])
        chart_type.draw()

    def pan_right():
        nonlocal x_min, x_max
        shift = (x_max - x_min) * 0.1
        x_min, x_max = x_min + shift, x_max + shift
        ax.set_xlim([x_min, x_max])
        chart_type.draw()

    def pan_up():
        nonlocal y_min, y_max
        shift = (y_max - y_min) * 0.1
        y_min, y_max = y_min + shift, y_max + shift
        ax.set_ylim([y_min, y_max])
        chart_type.draw()

    def pan_down():
        nonlocal y_min, y_max
        shift = (y_max - y_min) * 0.1
        y_min, y_max = y_min - shift, y_max - shift
        ax.set_ylim([y_min, y_max])
        chart_type.draw()

    def smooth_graph():
        for widget in canvas.winfo_children():
            widget.destroy()
        plot_graph(data, canvas, smooth=True)

    def reset_smooth():
        for widget in canvas.winfo_children():
            widget.destroy()
        plot_graph(data, canvas, smooth=False)

    button_frame = ttk.Frame(canvas)
    button_frame.pack(side="bottom", fill="x", padx=10, pady=5)
    ttk.Button(button_frame, text="Zoom In", command=zoom_in).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Zoom Out", command=zoom_out).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Reset Zoom", command=reset_zoom).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Smooth", command=smooth_graph).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Reset Smooth", command=reset_smooth).pack(side="left", padx=5)
    ttk.Button(button_frame, text="←", command=pan_left).pack(side="left", padx=5)
    ttk.Button(button_frame, text="→", command=pan_right).pack(side="left", padx=5)
    ttk.Button(button_frame, text="↑", command=pan_up).pack(side="left", padx=5)
    ttk.Button(button_frame, text="↓", command=pan_down).pack(side="left", padx=5)

def create_gui(data):
    root = tk.Tk()
    root.title("Weight Analysis Report")
    root.geometry("1000x700")
    root.resizable(False, False)

    graph_frame = ttk.LabelFrame(root, text="Graph", padding=(10, 5))
    graph_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)
    plot_graph(data, graph_frame)

    mean_weight, std_dev_weight = calculate_basic_statistics(data)
    total_impulse = calculate_total_impulse(data)
    data = analyze_weight_change(data)

    analysis_frame = ttk.LabelFrame(root, text="Analysis Results", padding=(10, 5))
    analysis_frame.pack(side="left", fill="y", expand=False, padx=10, pady=5)

    ttk.Label(analysis_frame, text=f"Average Weight: {mean_weight:.3f} kg").pack(anchor="w", pady=2)
    ttk.Label(analysis_frame, text=f"Standard Deviation: {std_dev_weight:.3f} kg").pack(anchor="w", pady=2)
    ttk.Label(analysis_frame, text=f"Total Impulse: {total_impulse:.3f} kg·s").pack(anchor="w", pady=2)

    table_frame = ttk.LabelFrame(root, text="Weight Changes Table", padding=(10, 5))
    table_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)

    cols = ("Time (s)", "Weight (kg)", "Weight Change (kg)")
    tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    for _, row in data.iterrows():
        tree.insert("", "end", values=(
            f"{row['Time (s)']:.2f}",
            f"{row['Weight (kg)']:.3f}",
            f"{row['Weight Change (kg)']:.3f}" if not pd.isna(row['Weight Change (kg)']) else "N/A"
        ))

    tree.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    root.mainloop()

def calculate_basic_statistics(data):
    mean_weight = data["Weight (kg)"].mean()
    std_dev_weight = data["Weight (kg)"].std()
    return mean_weight, std_dev_weight

def calculate_total_impulse(data):
    return simps(data["Weight (kg)"], data["Time (s)"])

def analyze_weight_change(data):
    data["Weight Change (kg)"] = data["Weight (kg)"].diff()
    return data

def apply_smoothing(weight_data, window_size=5):
    return np.convolve(weight_data, np.ones(window_size)/window_size, mode='same')

def plot_graph(data, canvas, smooth=False):
    fig, ax = plt.subplots(figsize=(6, 4))
    weight_data = data["Weight (kg)"]

    if smooth:
        weight_data = apply_smoothing(weight_data)

    line, = ax.plot(data["Time (s)"], weight_data, label="Weight", color="blue")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Weight (kg)")
    ax.set_title("Teerathap, Weight Over Time")
    ax.legend()
    ax.grid(True)

    cursor = mplcursors.cursor(line, hover=True)
    cursor.connect("add", lambda sel: sel.annotation.set_text(
        f"Time: {sel.target[0]:.2f}s\nWeight: {sel.target[1]:.3f}kg"))

    chart_type = FigureCanvasTkAgg(fig, master=canvas)
    chart_type.get_tk_widget().pack(fill="both", expand=True)
    chart_type.draw()

    x_min, x_max = data["Time (s)"].min(), data["Time (s)"].max()
    y_min, y_max = weight_data.min(), weight_data.max()

    def zoom_in():
        nonlocal x_min, x_max, y_min, y_max
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        x_range = (x_max - x_min) * 0.5
        y_range = (y_max - y_min) * 0.5
        x_min, x_max = x_center - x_range / 2, x_center + x_range / 2
        y_min, y_max = y_center - y_range / 2, y_center + y_range / 2
        ax.set_xlim([x_min, x_max])
        ax.set_ylim([y_min, y_max])
        chart_type.draw()

    def zoom_out():
        nonlocal x_min, x_max, y_min, y_max
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        x_range = (x_max - x_min) * 2
        y_range = (y_max - y_min) * 2
        x_min_new = max(data["Time (s)"].min(), x_center - x_range / 2)
        x_max_new = min(data["Time (s)"].max(), x_center + x_range / 2)
        y_min_new = max(weight_data.min(), y_center - y_range / 2)
        y_max_new = min(weight_data.max(), y_center + y_range / 2)
        x_min, x_max = x_min_new, x_max_new
        y_min, y_max = y_min_new, y_max_new
        ax.set_xlim([x_min, x_max])
        ax.set_ylim([y_min, y_max])
        chart_type.draw()

    def reset_zoom():
        nonlocal x_min, x_max, y_min, y_max
        x_min, x_max = data["Time (s)"].min(), data["Time (s)"].max()
        y_min, y_max = weight_data.min(), weight_data.max()
        ax.set_xlim([x_min, x_max])
        ax.set_ylim([y_min, y_max])
        chart_type.draw()

    def pan_left():
        nonlocal x_min, x_max
        shift = (x_max - x_min) * 0.1
        x_min, x_max = x_min - shift, x_max - shift
        ax.set_xlim([x_min, x_max])
        chart_type.draw()

    def pan_right():
        nonlocal x_min, x_max
        shift = (x_max - x_min) * 0.1
        x_min, x_max = x_min + shift, x_max + shift
        ax.set_xlim([x_min, x_max])
        chart_type.draw()

    def pan_up():
        nonlocal y_min, y_max
        shift = (y_max - y_min) * 0.1
        y_min, y_max = y_min + shift, y_max + shift
        ax.set_ylim([y_min, y_max])
        chart_type.draw()

    def pan_down():
        nonlocal y_min, y_max
        shift = (y_max - y_min) * 0.1
        y_min, y_max = y_min - shift, y_max - shift
        ax.set_ylim([y_min, y_max])
        chart_type.draw()

    def smooth_graph():
        for widget in canvas.winfo_children():
            widget.destroy()
        plot_graph(data, canvas, smooth=True)

    def reset_smooth():
        for widget in canvas.winfo_children():
            widget.destroy()
        plot_graph(data, canvas, smooth=False)

    button_frame = ttk.Frame(canvas)
    button_frame.pack(side="bottom", fill="x", padx=10, pady=5)
    ttk.Button(button_frame, text="Zoom In", command=zoom_in).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Zoom Out", command=zoom_out).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Reset Zoom", command=reset_zoom).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Smooth", command=smooth_graph).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Reset Smooth", command=reset_smooth).pack(side="left", padx=5)
    ttk.Button(button_frame, text="←", command=pan_left).pack(side="left", padx=5)
    ttk.Button(button_frame, text="→", command=pan_right).pack(side="left", padx=5)
    ttk.Button(button_frame, text="↑", command=pan_up).pack(side="left", padx=5)
    ttk.Button(button_frame, text="↓", command=pan_down).pack(side="left", padx=5)

def create_gui(data):
    root = tk.Tk()
    root.title("Weight Analysis Report")
    root.geometry("1000x700")
    root.resizable(False, False)

    graph_frame = ttk.LabelFrame(root, text="Graph", padding=(10, 5))
    graph_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)
    plot_graph(data, graph_frame)

    mean_weight, std_dev_weight = calculate_basic_statistics(data)
    total_impulse = calculate_total_impulse(data)
    data = analyze_weight_change(data)

    analysis_frame = ttk.LabelFrame(root, text="Analysis Results", padding=(10, 5))
    analysis_frame.pack(side="left", fill="y", expand=False, padx=10, pady=5)

    ttk.Label(analysis_frame, text=f"Average Weight: {mean_weight:.3f} kg").pack(anchor="w", pady=2)
    ttk.Label(analysis_frame, text=f"Standard Deviation: {std_dev_weight:.3f} kg").pack(anchor="w", pady=2)
    ttk.Label(analysis_frame, text=f"Total Impulse: {total_impulse:.3f} kg·s").pack(anchor="w", pady=2)

    table_frame = ttk.LabelFrame(root, text="Weight Changes Table", padding=(10, 5))
    table_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)

    cols = ("Time (s)", "Weight (kg)", "Weight Change (kg)")
    tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    for _, row in data.iterrows():
        tree.insert("", "end", values=(
            f"{row['Time (s)']:.2f}",
            f"{row['Weight (kg)']:.3f}",
            f"{row['Weight Change (kg)']:.3f}" if not pd.isna(row['Weight Change (kg)']) else "N/A"
        ))

    tree.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    root.mainloop()

if __name__ == "__main__":
    data = load_data()
    create_gui(data)


