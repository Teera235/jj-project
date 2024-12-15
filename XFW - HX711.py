import serial
import matplotlib.pyplot as plt
import numpy as np
import time
import csv

ser = serial.Serial('COM5', 57600, timeout=1)

def read_data():
    try:
        line = ser.readline().decode('utf-8').strip()
        if line:
            weight = float(line)  
            return weight
    except:
        return None

def collect_data(duration=10, sampling_rate=0.1):
    weight_data = []
    timestamps = []
    start_time = time.time()

    while time.time() - start_time < duration:
        weight = read_data()
        if weight is not None:
            weight_data.append(weight)
            timestamps.append(time.time() - start_time)
            time.sleep(sampling_rate) 

    ser.close() 
    return timestamps, weight_data

def analyze_weight(timestamps, weight_data):
    max_weight = max(weight_data)
    avg_weight = np.mean(weight_data)
    total_weight = np.trapz(weight_data, timestamps)  
    
    print(f"Max Weight: {max_weight} g")
    print(f"Average Weight: {avg_weight} g")
    print(f"Total Weight (Integrated): {total_weight} g·s")

    return max_weight, avg_weight, total_weight

def plot_weight(timestamps, weight_data):
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, weight_data, label="Weight")
    plt.xlabel("Time (s)")
    plt.ylabel("Weight (g)")
    plt.title("Weight Measurement Over Time")
    plt.legend()
    plt.grid(True)
    plt.show()

def save_to_csv(timestamps, weight_data, filename="weight_data.csv"):
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Time (s)", "Weight (g)"])
        for t, w in zip(timestamps, weight_data):
            writer.writerow([f"{t:.2f}", f"{w:.2f}"])
    print(f"Data saved to {filename}")


duration = 5
timestamps, weight_data = collect_data(duration)

max_weight, avg_weight, total_weight = analyze_weight(timestamps, weight_data)

plot_weight(timestamps, weight_data)
save_to_csv(timestamps,weight_data)
#saveRawData
